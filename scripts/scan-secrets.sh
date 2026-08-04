#!/usr/bin/env bash
set -euo pipefail

if rg --hidden --line-number \
  --glob '!.git/**' \
  --glob '!**/node_modules/**' \
  --glob '!**/package-lock.json' \
  --glob '!scripts/scan-secrets.sh' \
  '(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' \
  .; then
  echo 'Potential committed secret detected.' >&2
  exit 1
fi

echo 'No high-confidence secret patterns found.'
