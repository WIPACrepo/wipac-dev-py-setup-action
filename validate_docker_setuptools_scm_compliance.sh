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
# Mount the entire build context (including '.git/') just for this step
# NOTE:
#  - mounting '.git/' allows the Python project to build with 'setuptools-scm'
#  - no 'COPY .' because we don't want to copy extra files (especially '.git/')
#  - using '/tmp/pip-cache' allows pip to cache
RUN --mount=type=cache,target=/tmp/pip-cache \
    pip install --upgrade "pip>=25" "setuptools>=80" "wheel>=0.45"
RUN --mount=type=bind,source=.,target=/src,rw \
    --mount=type=cache,target=/tmp/pip-cache \
    pip install /src[<insert your optional dependency name(s) here>]
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
