#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BOARD_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
UEFI_DIR="${1:-${BOARD_DIR}/../edk2-sprd}"
TARGET="${2:-RELEASE}"

if [[ ! -f "${UEFI_DIR}/build.sh" ]]; then
  echo "edk2-sprd build.sh not found: ${UEFI_DIR}" >&2
  exit 1
fi

cd "${UEFI_DIR}"
exec bash ./build.sh \
  --device t610yp \
  --release "${TARGET}" \
  --toolchain CLANG38 \
  --uart \
  --skip-rootfs-gen
