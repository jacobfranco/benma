#!/bin/sh
# Isolate every MFA/micromamba writable path inside this research package.
set -eu
package_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec env \
  MAMBA_ROOT_PREFIX="$package_dir/.cache/mamba" \
  XDG_CACHE_HOME="$package_dir/.cache" \
  MFA_ROOT_DIR="$package_dir/.cache/mfa-work" \
  OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 \
  "$package_dir/.cache/micromamba-bin/bin/micromamba" run \
  -p "$package_dir/.cache/mfa-env" mfa "$@"
