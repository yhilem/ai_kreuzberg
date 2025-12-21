#!/usr/bin/env bash
set -euo pipefail

# Detect OpenSSL prefix from Homebrew (works for both Intel x86_64 and ARM64)
prefix="$(brew --prefix openssl@3 2>/dev/null || brew --prefix openssl 2>/dev/null || true)"

# Fallback for ARM64 macOS: check /opt/homebrew path
if [ -z "$prefix" ] && [ -d "/opt/homebrew/opt/openssl@3" ]; then
	prefix="/opt/homebrew/opt/openssl@3"
fi

# Fallback for Intel macOS: check /usr/local path
if [ -z "$prefix" ] && [ -d "/usr/local/opt/openssl@3" ]; then
	prefix="/usr/local/opt/openssl@3"
fi

if [ -z "$prefix" ]; then
	echo "Failed to locate Homebrew OpenSSL prefix" >&2
	echo "Checked: brew --prefix openssl@3, /opt/homebrew/opt/openssl@3, /usr/local/opt/openssl@3" >&2
	exit 1
fi

echo "OpenSSL detected at: $prefix"
echo "OpenSSL lib path: $prefix/lib"
echo "OpenSSL include path: $prefix/include"

{
	echo "OPENSSL_DIR=$prefix"
	echo "OPENSSL_LIB_DIR=$prefix/lib"
	echo "OPENSSL_INCLUDE_DIR=$prefix/include"
	echo "PKG_CONFIG_PATH=$prefix/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
} >>"$GITHUB_ENV"
