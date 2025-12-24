#!/usr/bin/env bash
# Build FFI library for Go bindings
# Used by: ci-go.yaml - Build FFI library step
# Supports: Unix (Linux/macOS)
#
# Environment Variables:
# - ORT_STRATEGY: Should be set to 'system' for using system ONNX Runtime
# - ORT_LIB_LOCATION: Path to ONNX Runtime lib directory
# - ORT_SKIP_DOWNLOAD: Set to 1 to skip downloading ONNX Runtime
# - ORT_PREFER_DYNAMIC_LINK: Set to 1 for dynamic linking
# - KREUZBERG_BUILD_VERBOSE: Set to 1 for verbose output (default: enabled in CI)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

# Enable verbose output in CI environments
VERBOSE="${KREUZBERG_BUILD_VERBOSE:-${CI:-0}}"

echo "=========================================="
echo "Building Kreuzberg FFI for Unix target"
echo "=========================================="
START_TIME=$(date +%s)

# System Information
echo ""
echo "=== System Information ==="
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Go version: $(go version 2>/dev/null || echo 'not installed')"
echo ""

# Configure ONNX Runtime environment for macOS and Linux
if [[ -n "${ORT_LIB_LOCATION:-}" ]]; then
	echo "=== ONNX Runtime Configuration (Unix) ==="
	echo "ORT_STRATEGY: ${ORT_STRATEGY:-<not set>}"
	echo "ORT_LIB_LOCATION: ${ORT_LIB_LOCATION}"
	echo "ORT_SKIP_DOWNLOAD: ${ORT_SKIP_DOWNLOAD:-<not set>}"
	echo "ORT_PREFER_DYNAMIC_LINK: ${ORT_PREFER_DYNAMIC_LINK:-<not set>}"
	echo "Verifying ORT directory..."
	if [[ -d "$ORT_LIB_LOCATION" ]]; then
		echo "✓ ORT directory exists"
		find "$ORT_LIB_LOCATION" -maxdepth 1 -type f | head -5 | while read -r file; do
			printf "  %s (%s)\n" "$(basename "$file")" "$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")"
		done
	else
		echo "✗ Warning: ORT directory not found at $ORT_LIB_LOCATION"
	fi
	echo ""

	# Ensure RUSTFLAGS includes -L flag for library directory
	if [[ -n "${RUSTFLAGS:-}" ]]; then
		if [[ ! "$RUSTFLAGS" =~ "-L" ]]; then
			export RUSTFLAGS="${RUSTFLAGS} -L ${ORT_LIB_LOCATION}"
		fi
	else
		export RUSTFLAGS="-L ${ORT_LIB_LOCATION}"
	fi
	echo "RUSTFLAGS: ${RUSTFLAGS}"
	echo ""
fi

echo "=== FFI Build Configuration ==="
echo "FFI crate directory: $REPO_ROOT/crates/kreuzberg-ffi"
echo "Output directory: $REPO_ROOT/target/release"
echo ""

# Build with verbose flags
echo "=== Building FFI Library ==="
if [[ "$VERBOSE" == "1" ]]; then
	echo "Running: cargo build -p kreuzberg-ffi --release -vv --timings"
	cargo build -p kreuzberg-ffi --release -vv --timings 2>&1
else
	echo "Running: cargo build -p kreuzberg-ffi --release"
	cargo build -p kreuzberg-ffi --release 2>&1
fi

BUILD_EXIT=$?

# Verify build artifacts
echo ""
echo "=== Build Artifacts Verification ==="
if [[ -d "$REPO_ROOT/target/release" ]]; then
	echo "Checking for FFI libraries in target/release:"
	if find "$REPO_ROOT/target/release" -maxdepth 1 -name "libkreuzberg_ffi*" -type f | grep -q .; then
		echo "✓ FFI libraries found:"
		find "$REPO_ROOT/target/release" -maxdepth 1 -name "libkreuzberg_ffi*" -type f | while read -r file; do
			printf "  %s (%s)\n" "$(basename "$file")" "$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")"
		done
	else
		echo "✗ Warning: No FFI libraries found in target/release"
		echo "Contents of target/release:"
		find "$REPO_ROOT/target/release" -maxdepth 1 -type f | tail -5
	fi
else
	echo "✗ Error: target/release directory not found"
fi

# Check for pkg-config file
echo ""
echo "Checking for pkg-config file:"
if [[ -f "$REPO_ROOT/crates/kreuzberg-ffi/kreuzberg-ffi.pc" ]]; then
	echo "✓ pkg-config file exists"
else
	echo "⚠ pkg-config file not found (may be generated during full build)"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "FFI Build completed in ${DURATION}s"
echo "=========================================="

exit $BUILD_EXIT
