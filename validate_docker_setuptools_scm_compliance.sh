#!/bin/bash
set -euo pipefail

# -----------------------------------------------------------------------------
# GitHub Actions / CI Guardrail Script
#
# Purpose:
#   Enforce checks for Python's 'setuptools-scm' builds and Docker best practices.
#
# Checks:
#   1. .dockerignore — fail if it ignores .git
#   2. Dockerfile    — fail if it copies the entire build context (`COPY . ...`)
#
# Usage:
#   Run in CI to fail builds on violations. Emits GitHub Actions error annotations.
#
# Exit Codes:
#   0 - No violations
#   1 - Violation found
# -----------------------------------------------------------------------------

#
# Detect all .dockerignore files for '.git'
#

echo "DEBUG: Searching for .dockerignore files..."
while IFS= read -r -d '' f; do # (looping like this, supports whitespaces in names and doesn't need a subshell)
    echo "DEBUG: Checking $f for '.git' ignore rule..."

    # Use -E (ERE) here for max portability; match a line that's exactly ".git" or ".git/"
    if grep -qE '^[[:space:]]*\.git/?[[:space:]]*$' "$f"; then
        echo "DEBUG: Matched offending line(s) in $f:"
        echo "::error file=$f::Forbidden rule ignoring '.git' found in: $f — remove for setuptools-scm compliance"
        exit 1
    fi
done < <(find . -type f -name '.dockerignore' -print0)

#
# Detect 'COPY' that copies the entire context (source is '.')
#

join_continuations() {
    # Join lines ending with '\' (strip the backslash)
    awk '/\\[[:space:]]*$/{sub(/\\[[:space:]]*$/,""); printf "%s", $0; next}1'
}

emit_copy_dot_error() {
    local f="$1"

    {
        echo "::error file=$f,title=Forbidden COPY from .::Found forbidden \`COPY . <dest>\` in: $f — see full recommendation below"
        echo "Found forbidden \`COPY . <dest>\` in: $f"
        echo "Use a narrow, cache-friendly install step instead, e.g.:"
        echo

        # **** NOTE! THIS IS A HEREDOC ****
        cat <<'SNIP'

# THERE ARE TWO RECOMMENDED PIP-INSTALL PATTERNS TO REPLACE YOUR 'COPY .' + 'pip install .'
# NOTE: both patterns are compatible with Dockerfile's `USER ...`
# -- Uncomment your pick and replace any placeholder strings

# Pip-Install Pattern #1
# NOTE:
#  - Use this pattern if during pip-install, no additional files are written to package (compare to pattern #2)
#  - No 'COPY .' because we don't want to copy extra files (especially '.git/')
#  - Mounting source files prevents unnecessary file duplication (compare to pattern #2)
#  - Mounting '.git/' allows the Python project to build with 'setuptools-scm'
#RUN --mount=type=bind,source=.git,target=.git,ro \
#    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,ro \
#    --mount=type=bind,source=YOUR_PYTHON_PACKAGE,target=YOUR_PYTHON_PACKAGE,ro \
#    pip install --no-cache .

# Pip-Install Pattern #2
# NOTE:
#  - Use this pattern if during pip-install, additional files are written to package (like '_version.py').
#  - No 'COPY .' because we don't want to copy extra files (especially '.git/')
#  - Unlike pattern #1, using 'COPY' will duplicate source files -- generally this is not an issue.
#       > Side Note: Using 'pip install -e .' will prevent duplication BUT can hide packaging issues
#            such as improperly using '[tool.setuptools.packages.find]' in 'pyproject.toml',
#            so 'pip install -e .' is not recommended.
#  - Mounting '.git/' allows the Python project to build with 'setuptools-scm'
#COPY pyproject.toml [YOUR_WORKDIR/]pyproject.toml
#COPY YOUR_PYTHON_PACKAGE [YOUR_WORKDIR/]YOUR_PYTHON_PACKAGE
#RUN --mount=type=bind,source=.git,target=.git,ro pip install --no-cache .

SNIP
        # **** END ****

        echo
    }
}

echo "DEBUG: Searching for Dockerfiles..."
while IFS= read -r -d '' f; do # (looping like this, supports whitespaces in names and doesn't need a subshell)
    echo "DEBUG: Found Dockerfile candidate: $f"
    content="$(join_continuations <"$f")"
    echo "DEBUG: Content after joining continuations:"
    echo "--------"
    echo "$content"
    echo "--------"

    # grep 'COPY' patterns where the **source** is `.`
    #
    # shell-form examples (should be flagged):
    #    COPY . .
    #    COPY . /app
    #    COPY --chown=1000:1000 . .
    #    COPY --from=builder . /src
    #    COPY --link . .
    #    COPY --from=builder --chown=appuser:appgroup . /dst
    #
    # JSON-array form examples (should be flagged):
    #    COPY [".", "."]
    #    COPY [".", "/app"]
    #    COPY --chown=1000:1000 [".", "."]-
    #    COPY --from=builder [".", "/src"]
    #    COPY --link [".", "."]
    #    COPY --from=builder --chown=appuser:appgroup [".", "."]

    if grep -qiP '^\s*COPY\b(?:\s+--\S+)*\s+\.(?:\s|$)' <<<"$content" ||
        grep -qiP '^\s*COPY\b(?:\s+--\S+)*\s*\[\s*"\."\s*,\s*".*"\s*\]' <<<"$content"; then
        echo "DEBUG: Match found in $f"
        emit_copy_dot_error "$f"
        exit 1
    else
        echo "DEBUG: No match in $f"
    fi
done < <(find . -type f \( -iname 'dockerfile' -o -iname '*.dockerfile' \) -print0)

echo "DEBUG: Guardrail checks completed successfully."
