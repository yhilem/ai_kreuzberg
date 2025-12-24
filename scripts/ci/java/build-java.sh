#!/usr/bin/env bash
#
# Build Java bindings with Maven
# Used by: ci-java.yaml - Build Java bindings step
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

source "$REPO_ROOT/scripts/lib/common.sh"

validate_repo_root "$REPO_ROOT" || exit 1

# Pre-build validation: Check for OpenSSL on Windows
echo "=== Pre-build validation ==="
PLATFORM="${RUNNER_OS:-$(uname -s)}"

if [ "$PLATFORM" = "Windows" ] || [[ "$PLATFORM" == MINGW* ]] || [[ "$PLATFORM" == MSYS* ]] || [[ "$PLATFORM" == CYGWIN* ]]; then
	if [ -z "${OPENSSL_DIR:-}" ]; then
		error_exit "OpenSSL is required for Java builds on Windows. Set OPENSSL_DIR environment variable before running this script." 1
	fi
	echo "Verified OPENSSL_DIR is set: $OPENSSL_DIR"
	if [ ! -d "$OPENSSL_DIR" ]; then
		error_exit "OPENSSL_DIR path does not exist: $OPENSSL_DIR" 1
	fi
	if [ ! -f "$OPENSSL_DIR/lib/libssl.lib" ] && [ ! -f "$OPENSSL_DIR/lib/ssl.lib" ] && [ ! -f "$OPENSSL_DIR/lib64/libssl.lib" ]; then
		error_exit "OpenSSL library files not found in: $OPENSSL_DIR/lib or $OPENSSL_DIR/lib64" 1
	fi
	echo "✓ OpenSSL validation passed"
fi

echo "=== Building Java bindings ==="
cd "$REPO_ROOT/packages/java"

# Enable verbose Maven output with debugging
# -X: debug mode (detailed logging)
# -e: errors mode (display full stack traces on errors)
# -DtrimStackTrace=false: preserve full stack traces
export MAVEN_OPTS="${MAVEN_OPTS:-} -XX:+UnlockDiagnosticVMOptions -XX:+LogVMOutput -XX:LogFile=maven-jvm.log"

echo "Maven invocation: mvn -X -e clean package -DskipTests -DtrimStackTrace=false"
mvn -X -e clean package -DskipTests -DtrimStackTrace=false || {
	echo "=== Maven build failed ==="
	if [ -f maven-jvm.log ]; then
		echo "=== Maven JVM Log ==="
		tail -100 maven-jvm.log || true
	fi
	exit 1
}

echo "Java build complete"
