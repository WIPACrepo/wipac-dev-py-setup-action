#!/bin/bash
set -euo pipefail

#
# Detect all .gitignore files for '.git'
#

find . -type f -name '.gitignore' -print0 |
    while IFS= read -r -d '' f; do
        if grep -qE '^[[:space:]]*[^#][[:space:]]*\.git/?[[:space:]]*$' "$f"; then
            echo "::error file=$f::Forbidden rule ignoring '.git' found — remove for setuptools-scm compliance"
            exit 1
        fi
    done

#
# Detect 'COPY . .' (and variations) in Dockerfiles
#

join_continuations() {
    # Join lines ending with '\' (strip the backslash)
    awk '/\\[[:space:]]*$/{sub(/\\[[:space:]]*$/,""); printf "%s", $0; next}1'
}

emit_copy_dotdot_error() {
    local f="$1"
    local content="$2"

    # show just the matching lines (with line numbers) for context
    local matches
    matches="$(printf "%s\n" "$content" | grep -niE \
        '^[[:space:]]*[^#].*\<COPY\>([[:space:]]+--[^[:space:]]+)*[[:space:]]+\.[[:space:]]+\.(?:[[:space:]]*(#|$))|^[[:space:]]*[^#].*\<COPY\>[[:space:]]*\[[[:space:]]*"\."[[:space:]]*,[[:space:]]*"\."[[:space:]]*\](?:[[:space:]]*(#|$))' || true)"

    {
        echo "::error file=$f,title=Forbidden COPY . .::<<GHA_EOT"
        echo "Found forbidden \`COPY . .\` in: $f"
        echo
        if [ -n "$matches" ]; then
            echo "Matched lines:"
            echo "$matches"
            echo
        fi
        echo "Use a narrow, cache-friendly install step instead, e.g.:"

        # **** NOTE! THIS IS A HEREDOC ****
        cat <<'SNIP'
#  .git
# Mount the entire build context (including '.git/') just for this step
# NOTE:
#  - no 'COPY' because we don't want to copy extra files (especially '.git/')
#  - using '/tmp/pip-cache' allows pip to cache
RUN --mount=type=cache,target=/tmp/pip-cache \
    pip install --upgrade "pip>=25" "setuptools>=80" "wheel>=0.45"
RUN --mount=type=bind,source=.,target=/src,rw \
    --mount=type=cache,target=/tmp/pip-cache \
    pip install /src[rabbitmq]
SNIP
        # **** END ****

        echo "GHA_EOT"
    }
}

find . -type f \( -iname 'dockerfile' -o -iname '*.dockerfile' \) -print0 |
    while IFS= read -r -d '' f; do
        content="$(join_continuations <"$f")"

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

        if grep -qiE '^[[:space:]]*[^#].*\<COPY\>([[:space:]]+--[^[:space:]]+)*[[:space:]]+\.[[:space:]]+\.(?:[[:space:]]*(#|$))' <<<"$content" ||
            grep -qiE '^[[:space:]]*[^#].*\<COPY\>([[:space:]]+--[^[:space:]]+)*[[:space:]]*\[[[:space:]]*"\."[[:space:]]*,[[:space:]]*"\."[[:space:]]*\](?:[[:space:]]*(#|$))' <<<"$content"; then
            # match! echo error message...
            emit_copy_dotdot_error "$f" "$content"
            exit 1
        fi
    done
