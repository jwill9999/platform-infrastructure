#!/usr/bin/env bash
set -euo pipefail

empty_tree="$(git hash-object -t tree /dev/null)"
git diff --check "$empty_tree" HEAD
git diff --check
git diff --check --cached

blocked_paths_regex='(^|/)(\.env($|\.)|id_(rsa|dsa|ecdsa|ed25519)($|\.)|[^/]+\.(pem|key|p12|pfx|jks|keystore|mobileprovision))$'
blocked_paths="$({ git ls-files | grep -E "$blocked_paths_regex"; } || true)"
if [[ -n "$blocked_paths" ]]; then
  echo "Credential-like tracked paths are prohibited:" >&2
  echo "$blocked_paths" >&2
  exit 1
fi

oversized=0
while IFS= read -r -d '' path; do
  if (( $(stat -c '%s' -- "$path") > 1048576 )); then
    if (( oversized == 0 )); then
      echo "Tracked files over 1 MiB require explicit review and external storage:" >&2
    fi
    printf '  %q\n' "$path" >&2
    oversized=1
  fi
done < <(git ls-files -z)
(( oversized == 0 )) || exit 1

echo "Repository structural validation passed."
