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
#   2. Dockerfile    — fail if it contains COPY . .
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
    if grep -qP '^[[:space:]]*[^#][[:space:]]*\.git/?[[:space:]]*$' "$f"; then
        echo "::error file=$f::Forbidden rule ignoring '.git' found — remove for setuptools-scm compliance (see job logs for details)"
        exit 1
    fi
done < <(find . -type f -name '.dockerignore' -print0)

#
# Detect 'COPY . .' (and variations) in Dockerfiles
#

join_continuations() {
    # Join lines ending with '\' (strip the backslash)
    awk '/\\[[:space:]]*$/{sub(/\\[[:space:]]*$/,""); printf "%s", $0; next}1'
}

emit_copy_dotdot_error() {
    local f="$1"

    {
        echo "::error file=$f,title=Forbidden COPY . .::Found forbidden \`COPY . .\` in: $f — see job logs for the full recommendation"
        echo "Found forbidden \`COPY . .\` in: $f"
        echo
        echo "Use a narrow, cache-friendly install step instead, e.g.:"

        # **** NOTE! THIS IS A HEREDOC ****
        cat <<'SNIP'
# Mount the entire build context (including '.git/') just for this step
# NOTE:
#  - mounting '.git/' allows the Python project to build with 'setuptools-scm'
#  - no 'COPY' because we don't want to copy extra files (especially '.git/')
#  - using '/tmp/pip-cache' allows pip to cache
RUN --mount=type=cache,target=/tmp/pip-cache \
    pip install --upgrade "pip>=25" "setuptools>=80" "wheel>=0.45"
RUN --mount=type=bind,source=.,target=/src,rw \
    --mount=type=cache,target=/tmp/pip-cache \
    pip install /src[<insert your optional dependency name(s) here>]
SNIP
        # **** END ****
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

    # grep two 'COPY . .' patterns
    #
    # shell-form:
    #    COPY . .
    #    COPY --chown=1000:1000 . .
    #    COPY --from=builder . .
    #    COPY --link . .
    #    COPY --from=builder --chown=appuser:appgroup . .
    #
    # JSON-array form:
    #    COPY [".", "."]
    #    COPY --chown=1000:1000 [".", "."]
    #    COPY --from=builder [".", "."]
    #    COPY --link [".", "."]
    #    COPY --from=builder --chown=appuser:appgroup [".", "."]

    if grep -qiP '^\s*COPY\b(?:\s+--\S+)*\s+\.\s+\.\s*(?:#|$)' <<<"$content" ||
        grep -qiP '^\s*COPY\b(?:\s+--\S+)*\s*\[\s*"\."\s*,\s*"\."\s*\]\s*(?:#|$)' <<<"$content"; then
        echo "DEBUG: Match found in $f"
        emit_copy_dotdot_error "$f"
        exit 1
    else
        echo "DEBUG: No match in $f"
    fi
done < <(find . -type f \( -iname 'dockerfile' -o -iname '*.dockerfile' \) -print0)

echo "DEBUG: Guardrail checks completed successfully."
