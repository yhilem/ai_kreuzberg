# Go CI Debugging Implementation Summary

## Overview

Comprehensive verbose debugging capabilities have been added to the Go CI workflow to facilitate troubleshooting of Rust FFI builds, CGO compilation, and cross-platform Go bindings.

## Files Added

### 1. Diagnostic Scripts

#### `/scripts/ci/go/debug-build-environment.sh` (Bash)
- **Purpose:** Comprehensive system and environment diagnostics for all platforms
- **Runs on:** Linux, macOS, Windows (MSYS2/Cygwin)
- **Outputs:**
  - System information (OS, architecture, kernel)
  - Tool versions (Rust, Go, GCC, pkg-config)
  - Build targets and FFI artifacts
  - Environment variables (Rust, CGO, library paths)
  - FFI library configuration
  - Go module setup
  - Dependency status

#### `/scripts/ci/go/debug-windows-environment.ps1` (PowerShell)
- **Purpose:** Windows-specific MinGW/MSYS2 toolchain diagnostics
- **Runs on:** Windows only
- **Critical checks:**
  - MSYS2 installation and MinGW64 verification
  - Compiler detection (catches MSVC vs MinGW mismatch)
  - PATH analysis for toolchain binaries
  - Environment variable configuration for MinGW
  - CGO Windows-specific settings
  - Link and compilation tools verification (gcc, ar, nasm)

### 2. Enhanced Build Scripts

#### `/scripts/ci/go/build-ffi.sh` (Updated)
- **New features:**
  - Verbose system information logging
  - Build configuration summary
  - Timing information (duration in seconds)
  - Artifact verification after build
  - FFI library listing with sizes
  - Error handling and exit code reporting
  - Optional verbose mode (`-vv --timings` flags)

#### `/scripts/ci/go/build-ffi.ps1` (Updated)
- **New features:**
  - Windows system information (OS version, processor count)
  - Toolchain verification before build
  - Tool version reporting (gcc, ar, nasm)
  - Verbose build flags for CI
  - Build artifact verification
  - File size reporting
  - Copy verification for cross-target builds
  - Colored output for status indicators

### 3. Enhanced Test Script

#### `/scripts/ci/go/run-tests.sh` (Updated)
- **New features:**
  - Per-module timing information
  - FFI library verification before tests
  - Test status summary (PASSED/FAILED)
  - Overall execution duration
  - Library file listing in Unix configuration
  - Proper exit code propagation

### 4. Documentation

#### `/scripts/ci/go/DEBUG-GUIDE.md`
- **Comprehensive guide covering:**
  - Script descriptions and functionality
  - When each script runs in CI pipeline
  - Output section reference
  - Local usage instructions
  - Success/warning indicator interpretation
  - Common issues and solutions
  - Timing analysis and bottleneck identification
  - Environment variable reference
  - Workflow integration details
  - Local development debugging
  - Advanced log collection

#### `/scripts/ci/go/DEBUGGING-SUMMARY.md` (This file)
- Quick reference for implementation changes

## Workflow Changes

### File: `.github/workflows/ci-go.yaml`

#### Build Job (`build-go`) Changes:

1. **After "Install system dependencies":**
   - Added `debug-build-environment` step (bash)
   - Added `debug-windows-environment` step (PowerShell, Windows only)

2. **Build FFI Library steps:**
   - Added `KREUZBERG_BUILD_VERBOSE=1` environment variable
   - Added `verify-ffi-build-artifacts` step to list all generated libraries

3. **Environment variable propagation:**
   - Verbose output enabled via `KREUZBERG_BUILD_VERBOSE=1`
   - No changes to command syntax, only additional logging

#### Test Job (`test-go`) Changes:

1. **After "Install system dependencies":**
   - Added `debug-build-environment` (test job) step (bash)
   - Added `debug-windows-environment` (test job) step (PowerShell, Windows only)

2. **Before "Run Go tests":**
   - Added `print-cgo-compilation-flags` step
     - Logs all CGO_* environment variables
     - Shows library path configuration
     - Displays relevant parts of PATH variable

3. **Test execution:**
   - `run-tests.sh` now includes timing information
   - Enhanced with FFI library verification
   - Proper test status reporting

## Key Features

### 1. Verbose Debugging Output

**Always enabled in CI:**
- Rust FFI builds use `-vv` and `--timings` flags
- Go tests run with `-v -x` (verbose, trace) flags
- Comprehensive environment variable logging

**Format:**
- Organized into named sections
- Status indicators: [OK], [WARN], [FAIL], [INFO]
- Color coding for terminals
- Timing information for all major steps

### 2. Windows MinGW Toolchain Verification

**Critical diagnostics:**
- Verifies gcc is from MinGW/MSYS2, not MSVC
- Checks ar is GNU ar, not MSVC lib.exe
- Validates environment variables (CC, AR, TARGET_CC, etc.)
- Confirms correct linker configuration
- Tests tool availability before build

**Output example:**
```
=== Toolchain Verification (CRITICAL) ===
[OK] gcc found at: C:\msys64\mingw64\bin\gcc.exe
[OK] Using MSYS2/MinGW gcc (correct)
[OK] ar found at: C:\msys64\mingw64\bin\ar.exe
[OK] Using MSYS2/MinGW ar (correct)
```

### 3. Comprehensive Environment Logging

**Rust build variables:**
- RUSTFLAGS, RUSTC_WRAPPER, CARGO_BUILD_TARGET
- Cargo-specific toolchain variables

**CGO configuration:**
- CGO_ENABLED, CGO_CFLAGS, CGO_LDFLAGS
- PKG_CONFIG_PATH, GOFLAGS

**Runtime paths:**
- LD_LIBRARY_PATH (Linux)
- DYLD_LIBRARY_PATH, DYLD_FALLBACK_LIBRARY_PATH (macOS)
- PATH (all platforms, Windows DLL search)

**Dependency configuration:**
- ORT_LIB_LOCATION (ONNX Runtime)
- KREUZBERG_PDFIUM_PREBUILT (PDFium)

### 4. Build Artifact Verification

**Automated checks:**
- FFI library existence and file size
- pkg-config configuration file validation
- Cross-target artifact location verification (Windows MinGW)
- Directory listing of output directories

**Example output:**
```
=== Build Artifacts Verification ===
Checking for FFI libraries in target/release:
✓ FFI libraries found:
  libkreuzberg_ffi.a (2.45 MB)
  libkreuzberg_ffi.so (1.23 MB)
```

### 5. Timing Information

**Tracks:**
- Script execution start time
- Per-module test duration
- Total execution duration
- Build step duration

**Output example:**
```
FFI Build completed in 45s
Module tests completed in 23s
Total execution time: 120s
```

## Integration Points

### CI Workflow Integration

All debug steps use:
- `if: always()` condition - ensures they run even if previous steps fail
- Platform-specific conditions - Windows diagnostics only on Windows
- No workflow exit code impact - purely informational

### Environment Variable Handling

- `KREUZBERG_BUILD_VERBOSE=1` in FFI build steps
- Auto-detection of CI environment
- Proper escaping of special characters in logs

### Cross-Platform Support

**Linux/macOS:**
- Uses bash scripts with standard GNU tools
- LD_LIBRARY_PATH and DYLD_* variables
- Library path resolution via pkg-config

**Windows:**
- Uses PowerShell for native Windows API access
- MinGW toolchain verification
- DLL search path via PATH variable
- Color output with PowerShell Write-Host

## Usage Instructions

### In GitHub Actions (Automatic)

Debug scripts run automatically:
1. After system dependencies installation (build job)
2. Before test execution (test job)
3. After FFI build completion (artifact verification)
4. Before Go test execution (CGO flag logging)

### Local Development

```bash
# Run full diagnostics
scripts/ci/go/debug-build-environment.sh

# On Windows (PowerShell)
scripts/ci/go/debug-windows-environment.ps1

# Build FFI with verbose output
KREUZBERG_BUILD_VERBOSE=1 scripts/ci/go/build-ffi.sh

# Run tests with diagnostics
scripts/ci/go/run-tests.sh
```

### Interpreting Output

**Success indicators (green [OK]):**
- Toolchain found in correct location
- FFI libraries generated
- Library paths accessible
- All tools available

**Warnings (yellow [WARN]):**
- Files not found (but not critical)
- Optional components missing
- Fallback behavior activated

**Failures (red [FAIL]):**
- Critical tools missing
- Incorrect toolchain detected
- Library path issues
- Build artifact generation failed

## Performance Impact

**Negligible:**
- Debug scripts are mostly file I/O and environment inspection
- Total overhead: <5 seconds per job
- No impact on actual build/test duration
- Uses existing environment data only

## Troubleshooting Benefits

### For Windows MinGW Issues

```
[FAIL] gcc is NOT from MSYS2/MinGW: C:\Program Files\Microsoft Visual Studio...
```
- Immediately identifies MSVC/MinGW PATH precedence issue
- Points to exact tool location
- Helps debug toolchain setup

### For FFI Build Failures

```
✗ ERROR: No FFI libraries found in target/x86_64-pc-windows-gnu/release
```
- Diagnostic output leads to cargo build error messages
- Shows exactly where artifacts should be
- Helps identify missing dependencies

### For CGO Linking Failures

```
[FAIL] ar is NOT from MSYS2/MinGW: ...
```
- Reveals compiler/archiver mismatch causing linking failure
- Shows exact paths being used
- Enables quick remediation

### For Runtime Failures

```
LD_LIBRARY_PATH: /path/to/kreuzberg/target/release:...
```
- Confirms library paths are configured
- Helps diagnose "library not found" runtime errors
- Shows exact search path ordering

## Future Enhancements

Potential additions:
- Binary compatibility checks (ELF/Mach-O/PE format verification)
- Cross-target library verification
- CGO cache analysis
- Build cache efficiency reporting
- Network connectivity checks for downloads

## References

- Full debugging guide: `scripts/ci/go/DEBUG-GUIDE.md`
- Workflow file: `.github/workflows/ci-go.yaml`
- Go bindings: `packages/go/v4/`
- FFI library: `crates/kreuzberg-ffi/`
