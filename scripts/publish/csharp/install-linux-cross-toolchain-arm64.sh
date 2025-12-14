#!/usr/bin/env bash

set -euo pipefail

# Install cross-compilation toolchain (no multiarch needed)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

source "$REPO_ROOT/scripts/lib/retry.sh"

echo "::group::Installing aarch64 Linux cross toolchain"

if ! retry_with_backoff sudo apt-get update; then
	echo "::error::apt-get update failed after retries" >&2
	exit 1
fi

if ! retry_with_backoff_timeout 900 sudo apt-get install -y \
	gcc-aarch64-linux-gnu \
	g++-aarch64-linux-gnu \
	binutils-aarch64-linux-gnu \
	pkg-config; then
	echo "::error::apt-get install cross toolchain failed" >&2
	exit 1
fi

gcc_bin="$(command -v aarch64-linux-gnu-gcc || command -v aarch64-linux-gnu-gcc-14 || command -v aarch64-linux-gnu-gcc-13 || true)"
gpp_bin="$(command -v aarch64-linux-gnu-g++ || command -v aarch64-linux-gnu-g++-14 || command -v aarch64-linux-gnu-g++-13 || true)"
ar_bin="$(command -v aarch64-linux-gnu-ar || true)"
pkg_config_bin="$(command -v aarch64-linux-gnu-pkg-config || true)"
pkg_config_host_bin="$(command -v pkg-config || true)"

if [[ -z "$gcc_bin" || -z "$gpp_bin" || -z "$ar_bin" ]]; then
	echo "::error::Cross toolchain binaries not found after install" >&2
	echo "aarch64-linux-gnu-gcc: ${gcc_bin:-missing}" >&2
	echo "aarch64-linux-gnu-g++: ${gpp_bin:-missing}" >&2
	echo "aarch64-linux-gnu-ar: ${ar_bin:-missing}" >&2
	echo "aarch64-linux-gnu-pkg-config: ${pkg_config_bin:-missing}" >&2
	echo "pkg-config: ${pkg_config_host_bin:-missing}" >&2
	ls -la /usr/bin/aarch64-linux-gnu-* 2>/dev/null || true
	exit 1
fi

echo "::endgroup::"

{
	echo "CC_aarch64_unknown_linux_gnu=$gcc_bin"
	echo "CXX_aarch64_unknown_linux_gnu=$gpp_bin"
	echo "AR_aarch64_unknown_linux_gnu=$ar_bin"
	echo "CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=$gcc_bin"
} >>"${GITHUB_ENV:?GITHUB_ENV not set}"

{
	echo "PKG_CONFIG_ALLOW_CROSS=1"
	if [[ -n "$pkg_config_bin" ]]; then
		echo "PKG_CONFIG_aarch64_unknown_linux_gnu=$pkg_config_bin"
	elif [[ -n "$pkg_config_host_bin" ]]; then
		echo "PKG_CONFIG=$pkg_config_host_bin"
	fi
} >>"${GITHUB_ENV:?GITHUB_ENV not set}"
