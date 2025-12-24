#!/usr/bin/env bash
#
# Run Ruby tests
# Used by: ci-ruby.yaml - Run Ruby tests step
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# scripts/ci/ruby lives three levels below repo root
REPO_ROOT="${REPO_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"

source "$REPO_ROOT/scripts/lib/common.sh"
source "$REPO_ROOT/scripts/lib/library-paths.sh"

validate_repo_root "$REPO_ROOT" || exit 1
setup_rust_ffi_paths "$REPO_ROOT"

echo "=== Running Ruby tests (Verbose Debug) ==="
cd "$REPO_ROOT/packages/ruby"

echo ""
echo "=== Pre-test environment ==="
echo "Ruby version: $(ruby --version)"
echo "Ruby platform: $(ruby -e 'puts RUBY_PLATFORM')"
echo "Working directory: $(pwd)"
echo ""

echo "=== Library search paths ==="
echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-<not set>}"
echo "DYLD_LIBRARY_PATH: ${DYLD_LIBRARY_PATH:-<not set>}"
echo "RUST_LOG: ${RUST_LOG:-<not set>}"
echo "RUST_BACKTRACE: ${RUST_BACKTRACE:-<not set>}"
echo ""

echo "=== Checking kreuzberg gem installation ==="
gem list kreuzberg || echo "Gem not found"
echo ""

echo "=== Checking for native extension ==="
if [ -f "lib/kreuzberg_rb.so" ] || [ -f "lib/kreuzberg_rb.dll" ] || [ -f "lib/kreuzberg_rb.dylib" ]; then
	echo "Native extension found"
	ls -lh lib/kreuzberg_rb.* || true
else
	echo "WARNING: Native extension not found in lib/"
fi
echo ""

echo "=== Ruby spec files ==="
if [ -d "spec" ]; then
	find spec -name "*_spec.rb" | head -10
else
	echo "ERROR: spec directory not found"
fi
echo ""

echo "=== Running RSpec tests with verbose output ==="
bundle exec rspec --verbose 2>&1 || {
	echo ""
	echo "ERROR: RSpec tests failed"
	echo "=== Attempting to load extension manually ==="
	ruby -e "require 'kreuzberg'; puts 'Extension loaded'" 2>&1 || {
		echo "ERROR: Could not load kreuzberg extension"
		echo "=== Checking gem paths ==="
		gem env | head -20
	}
	exit 1
}

echo ""
echo "=== Tests complete ==="
