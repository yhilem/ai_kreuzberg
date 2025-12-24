#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

# Source shared utilities
source "${REPO_ROOT}/scripts/lib/common.sh"
source "${REPO_ROOT}/scripts/lib/library-paths.sh"

# Validate repository structure
validate_repo_root "$REPO_ROOT" || exit 1

START_TIME=$(date +%s)

echo "=========================================="
echo "Go Test Execution with Diagnostics"
echo "=========================================="
echo "Script directory: $SCRIPT_DIR"
echo "Repository root: $REPO_ROOT"
echo "Operating system: $OSTYPE"
echo "Go version: $(go version)"
echo "Current time: $(date)"
echo

cd "$REPO_ROOT/packages/go"
echo "Working directory: $(pwd)"
echo

# Find all Go modules (directories with go.mod)
echo "Discovering Go modules..."
modules=()
while IFS= read -r module_dir; do
	modules+=("$module_dir")
done < <(find . -maxdepth 2 -name 'go.mod' -exec dirname {} \; | sort -u)

echo "Found modules: $(printf '%s ' "${modules[@]}")"
echo

if [[ ${#modules[@]} -eq 0 ]]; then
	echo "Error: No Go modules found in $(pwd)"
	find . -maxdepth 2 -name 'go.mod'
	exit 1
fi

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
	# Windows-specific setup
	# In GitHub Actions, CGO environment is already configured by setup-go-cgo-env action
	# Only call setup_go_paths for local development
	if [[ -z "${GITHUB_ENV:-}" ]]; then
		setup_go_paths "$REPO_ROOT"
	fi

	echo "=========================================="
	echo "Windows Test Configuration"
	echo "=========================================="
	echo "PKG_CONFIG_PATH: ${PKG_CONFIG_PATH:-<not set>}"
	echo "CGO_LDFLAGS: ${CGO_LDFLAGS:-<not set>}"
	echo "CGO_ENABLED: ${CGO_ENABLED:-<not set>}"
	echo
	echo "FFI library contents (GNU target):"
	ls -la "$REPO_ROOT/target/x86_64-pc-windows-gnu/release" || true
	echo "FFI library contents (host release):"
	ls -la "$REPO_ROOT/target/release" || true
	echo

	# Skip -race on Windows: mingw + static CRT regularly fails to link race runtime
	extra_flags=()
	if [[ -n "${GO_TEST_FLAGS:-}" ]]; then
		read -r -a extra_flags <<<"$GO_TEST_FLAGS"
	fi

	# Run tests in each module
	for module in "${modules[@]}"; do
		echo ""
		echo "=========================================="
		echo "Running tests in $module"
		echo "=========================================="
		module_start=$(date +%s)
		cd "$module"
		go test -v -x -work "${extra_flags[@]:-}" ./... 2>&1 || TEST_FAILED=1
		module_end=$(date +%s)
		module_duration=$((module_end - module_start))
		echo "Module tests completed in ${module_duration}s"
		cd "$REPO_ROOT/packages/go"
	done
else
	# Unix (Linux/macOS) setup
	setup_go_paths "$REPO_ROOT"

	echo "=========================================="
	echo "Unix Test Configuration"
	echo "=========================================="
	echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-<not set>}"
	echo "DYLD_FALLBACK_LIBRARY_PATH: ${DYLD_FALLBACK_LIBRARY_PATH:-<not set>}"
	echo "CGO_LDFLAGS: ${CGO_LDFLAGS:-<not set>}"
	echo "CGO_ENABLED: ${CGO_ENABLED:-<not set>}"
	echo "PKG_CONFIG_PATH: ${PKG_CONFIG_PATH:-<not set>}"
	echo
	echo "FFI library files:"
	if [[ -d "$REPO_ROOT/target/release" ]]; then
		ls -lh "$REPO_ROOT/target/release/libkreuzberg_ffi"* 2>/dev/null || echo "  (none found)"
	fi
	echo

	extra_flags=()
	if [[ -n "${GO_TEST_FLAGS:-}" ]]; then
		read -r -a extra_flags <<<"$GO_TEST_FLAGS"
	fi

	# Run tests in each module
	TEST_FAILED=0
	for module in "${modules[@]}"; do
		echo ""
		echo "=========================================="
		echo "Running tests in $module"
		echo "=========================================="
		module_start=$(date +%s)
		cd "$module"
		go test -v -race -x "${extra_flags[@]:-}" ./... 2>&1 || TEST_FAILED=1
		module_end=$(date +%s)
		module_duration=$((module_end - module_start))
		echo "Module tests completed in ${module_duration}s"
		cd "$REPO_ROOT/packages/go"
	done
fi

# Final timing summary
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
echo ""
echo "=========================================="
echo "Go Tests Summary"
echo "=========================================="
echo "Total execution time: ${TOTAL_DURATION}s"
echo "Test status: $([ "$TEST_FAILED" -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "=========================================="

exit "${TEST_FAILED:-0}"
