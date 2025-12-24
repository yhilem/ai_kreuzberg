# Go CI Debugging Guide

This guide documents the comprehensive debugging capabilities added to the Go CI workflow for troubleshooting build and test failures.

## Overview

The Go CI pipeline now includes extensive logging and diagnostic capabilities to help identify issues with:
- Rust FFI library builds (kreuzberg-ffi)
- Go CGO compilation and linking
- Windows MinGW toolchain configuration
- Runtime library path resolution
- Cross-platform compatibility issues

## Debug Scripts

### 1. `debug-build-environment.sh` (Unix/Linux/macOS)

Comprehensive system and environment diagnostics for all platforms.

**When it runs:**
- Automatically in `build-go` job (after system dependencies installation)
- Automatically in `test-go` job (before library setup)

**What it checks:**
- System information (OS, architecture, kernel version)
- Tool versions (Rust, Go, GCC, pkg-config)
- Cargo configuration and build targets
- Environment variables (Rust, CGO, library paths)
- FFI library configuration and artifacts
- Go module configuration
- Dependency status (PDFium, ONNX Runtime)

**Output sections:**
```
System Information
  - OS, architecture, kernel details

Tool Versions
  - rustc, cargo, go, gcc versions

Build Targets and Output Directories
  - Lists all target/ directories
  - Shows FFI library artifacts

Environment Variables
  - RUSTFLAGS, CGO_ENABLED, CGO_CFLAGS, CGO_LDFLAGS
  - LD_LIBRARY_PATH, DYLD_LIBRARY_PATH, DYLD_FALLBACK_LIBRARY_PATH
  - PKG_CONFIG_PATH

FFI Library Configuration
  - Verifies FFI source and headers
  - Checks pkg-config configuration

Go Module Configuration
  - Validates go.mod and Go packages
```

**Usage locally:**
```bash
cd /path/to/kreuzberg
scripts/ci/go/debug-build-environment.sh
```

### 2. `debug-windows-environment.ps1` (Windows only)

Comprehensive Windows-specific diagnostics for MinGW toolchain and CGO setup.

**When it runs:**
- Automatically in `build-go` job (after system dependencies installation)
- Automatically in `test-go` job (before library setup)

**What it checks:**
- Windows version and system information
- MSYS2 installation and MinGW64 toolchain
- Required tools (gcc, ar, ranlib, nasm)
- Environment variables for MinGW toolchain
- CGO configuration for Windows
- PATH variable analysis and MinGW/MSYS2 entries
- Build directory structure
- FFI library configuration
- Go module setup
- Compiler verification (critical for catching MSVC/MinGW mismatch)
- External dependencies (PDFium, ONNX Runtime)

**Critical checks:**
- Verifies `gcc` is from MinGW/MSYS2, not MSVC
- Verifies `ar` is GNU ar, not MSVC lib.exe
- Confirms TARGET_CC, TARGET_AR environment variables
- Validates CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER

**Usage locally (PowerShell):**
```powershell
cd C:\path\to\kreuzberg
scripts/ci/go/debug-windows-environment.ps1
```

### 3. Enhanced `build-ffi.sh` and `build-ffi.ps1`

Now include detailed diagnostics and timing information.

**New features:**
- System information logging
- Build configuration summary
- Timing information (start, end, duration)
- Verbose output with `-vv` and `--timings` flags in CI
- Artifact verification after build
- pkg-config file validation
- Directory listing of output

**Timing output example:**
```
==========================================
FFI Build completed in 45s
==========================================
```

**Environment variable:**
- `KREUZBERG_BUILD_VERBOSE=1` - Enables verbose output (default in CI)

### 4. Enhanced `run-tests.sh`

Test execution now includes comprehensive diagnostics and timing.

**New features:**
- Per-module timing information
- FFI library verification before tests
- Test status summary
- Detailed environment variable logging
- Library path verification

**Timing output example:**
```
==========================================
Go Tests Summary
==========================================
Total execution time: 120s
Test status: PASSED
==========================================
```

## CI Workflow Debug Steps

### Build Job

The `build-go` job now includes:

1. **Debug build environment** - Captures initial system state
2. **Debug Windows environment** (Windows only) - MinGW toolchain verification
3. **Build FFI library** - With verbose output and timing
4. **Verify FFI build artifacts** - Lists all generated libraries
5. **Build Go bindings** - Creates CGO bindings
6. **Upload FFI library** - Saves artifacts for test job

### Test Job

The `test-go` job now includes:

1. **Debug build environment** - Captures test environment state
2. **Debug Windows environment** (Windows only) - Toolchain verification
3. **Setup Go CGO environment** - Configures library paths
4. **Export library paths** - Sets runtime paths
5. **Verify CGO configuration** - Pre-test validation
6. **Print CGO compilation flags** - Detailed flag logging
7. **Run Go tests** - With verbose output and timing
8. **Generate E2E tests** - Auto-generated from fixtures
9. **Run E2E tests** - End-to-end testing with library paths

## Understanding the Output

### Success Indicators

When everything works, you'll see:
```
[OK] gcc found at: C:\msys64\mingw64\bin\gcc.exe
[OK] Using MSYS2/MinGW gcc (correct)
[OK] ar found at: C:\msys64\mingw64\bin\ar.exe
[OK] Using MSYS2/MinGW ar (correct)
✓ FFI libraries found:
  libkreuzberg_ffi.a (2.45 MB)
```

### Warning Signs

**Missing FFI libraries:**
```
✗ WARNING: No FFI libraries found in target/release
```
- Indicates Rust build did not produce expected artifacts
- Check RUSTFLAGS, CARGO_BUILD_TARGET
- Verify FFI crate Cargo.toml

**MSVC tools instead of MinGW (Windows):**
```
[FAIL] gcc is NOT from MSYS2/MinGW: C:\Program Files (x86)\Microsoft Visual Studio\...
```
- Indicates PATH precedence issue
- Check that MSYS2 bin is at the beginning of PATH
- Verify `setup-msys2-windows.ps1` ran successfully

**CGO linking issues:**
```
[FAIL] Library path does not exist: /path/to/lib
```
- Library search path doesn't point to built artifacts
- Check CGO_LDFLAGS and PKG_CONFIG_PATH
- Verify FFI build completed

**Missing pkg-config file:**
```
⚠ pkg-config cannot find kreuzberg-ffi
```
- PKG_CONFIG_PATH not set or invalid
- FFI crate hasn't been built (generates .pc file)
- May be OK if build is still in progress

## Common Issues and Solutions

### Issue 1: "gcc is NOT from MSYS2/MinGW" on Windows

**Symptom:**
```
[FAIL] gcc is NOT from MSVC tools detected
```

**Root cause:**
- MSVC installation adding mingw to PATH first
- MSYS2/MinGW path not prioritized in PATH

**Solution:**
1. Check `setup-msys2-windows.ps1` output
2. Verify MSYS2 bin is at PATH beginning
3. Ensure `CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER` is set to MinGW gcc
4. In workflow: check Windows toolchain setup step runs before build

### Issue 2: FFI Build Produces No Artifacts

**Symptom:**
```
✗ ERROR: No FFI libraries found in target/x86_64-pc-windows-gnu/release
```

**Root cause:**
- Rust build failed silently
- ONNX Runtime configuration issues
- Dependency (PDFium, ONNX Runtime) missing

**Solution:**
1. Look for `cargo build` error messages
2. Check RUSTFLAGS for invalid flags
3. Verify ORT_LIB_LOCATION points to valid directory
4. Ensure PDFium staging completed

### Issue 3: CGO Linking Fails

**Symptom:**
```
undefined reference to `kreuzberg_ffi_new`
```

**Root cause:**
- FFI library not in library path
- CGO_LDFLAGS incorrect
- Library compiled for different target

**Solution:**
1. Verify "FFI Build Artifacts" section shows libraries
2. Check CGO_LDFLAGS contains correct `-L` path
3. Confirm library path readable by CGO
4. On Windows: verify static linking flags (`-static-libgcc`)

### Issue 4: Go Tests Can't Find Runtime Library

**Symptom:**
```
error: failed to load kreuzberg-ffi library: library not found
```

**Root cause:**
- LD_LIBRARY_PATH/DYLD_LIBRARY_PATH not set
- Library in wrong location
- Relative path resolution issue

**Solution:**
1. Check "Library Paths" in test environment output
2. Verify LD_LIBRARY_PATH includes target/release
3. On macOS: check DYLD_LIBRARY_PATH and DYLD_FALLBACK_LIBRARY_PATH
4. Ensure FFI library was moved to correct location in test job

## Timing Analysis

The debug output includes timing information to help identify bottlenecks:

```
FFI Build completed in 45s
Module tests completed in 23s
Total execution time: 120s
```

**Typical timings:**
- FFI build (Unix): 30-60s (depends on cache)
- FFI build (Windows MinGW): 40-90s (MinGW linking is slower)
- Go tests per module: 10-30s
- E2E tests: 20-40s

**If timings are much longer:**
1. Check if cache is working (look for "Compiling" messages)
2. Verify no network timeouts during dependency download
3. Check for disk I/O bottlenecks in CI environment

## Environment Variable Reference

### Build Variables

| Variable | Scope | Value | Purpose |
|----------|-------|-------|---------|
| `RUSTFLAGS` | Rust | `-L /path/to/ort` | Add library search path for ORT |
| `CARGO_BUILD_TARGET` | Windows | `x86_64-pc-windows-gnu` | Explicit MinGW target |
| `CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER` | Windows | `x86_64-w64-mingw32-gcc` | MinGW linker |
| `CC`, `AR`, `RANLIB` | All | MinGW tools | Compiler selection |
| `KREUZBERG_BUILD_VERBOSE` | Build | `1` | Enable verbose output |

### CGO Variables

| Variable | Scope | Value | Purpose |
|----------|-------|-------|---------|
| `CGO_ENABLED` | All | `1` | Enable CGO compilation |
| `CGO_CFLAGS` | All | `-I.../include` | FFI header path |
| `CGO_LDFLAGS` | All | `-L... -lkreuzberg_ffi` | FFI library link flags |
| `PKG_CONFIG_PATH` | All | `crates/kreuzberg-ffi` | pkg-config search path |

### Runtime Variables

| Variable | Platform | Value | Purpose |
|----------|----------|-------|---------|
| `LD_LIBRARY_PATH` | Linux | `target/release:...` | Shared library search path |
| `DYLD_LIBRARY_PATH` | macOS | `target/release:...` | Dynamic library search path |
| `DYLD_FALLBACK_LIBRARY_PATH` | macOS | `target/release:...` | Fallback library path |
| `PATH` | Windows | Includes MinGW bin | DLL search path |

## Workflow Integration

The debug steps are integrated into the CI workflow with:
- `if: always()` condition - runs even if previous steps fail
- Separate steps for Windows-specific checks
- No impact on workflow exit code - purely informational

This ensures you get diagnostic data regardless of whether the build/tests succeed or fail.

## Local Development

To debug locally, run the debug scripts manually:

```bash
# Full system diagnostics
scripts/ci/go/debug-build-environment.sh

# Build FFI with verbose output
KREUZBERG_BUILD_VERBOSE=1 scripts/ci/go/build-ffi.sh

# Run tests with diagnostics
scripts/ci/go/run-tests.sh
```

Or run specific steps from the workflow:

```bash
# Setup environment and check
source scripts/lib/common.sh
source scripts/lib/library-paths.sh
setup_go_paths "$(pwd)"

# Run verification
scripts/ci/go/verify-cgo-config.sh
```

## Troubleshooting Workflow Runs

1. **Check the Build Artifacts step** - Shows exactly what was built
2. **Review CGO Compilation Flags** - Verifies compiler configuration
3. **Look for colored output** - [OK] (green), [WARN] (yellow), [FAIL] (red)
4. **Check timings** - Identifies bottlenecks
5. **Search for ✓ and ✗ symbols** - Quick status indicators

## Advanced: Collecting Debug Logs

To save full debug output from a workflow run:

1. Open the GitHub Actions run page
2. Expand each step section
3. Look for "Debug build environment" and related steps
4. Copy the full output to a file for analysis

The workflow automatically collects:
- System configuration
- Tool versions
- Environment variables (sanitized)
- File listings with timestamps
- Build/test timing information
