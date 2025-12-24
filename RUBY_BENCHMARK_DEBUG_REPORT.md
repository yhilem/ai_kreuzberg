# Ruby Benchmark Execution Failure - Debug Report & Fix

## Problem Summary

The Ruby gem built successfully (626 compilations OK), but the benchmark execution produced no results. The `benchmark-results/` directory was never created, and the Ruby benchmark adapter failed silently during execution.

## Root Cause Analysis

### Issue 1: Missing Native Extension in Global Gem Installation

The installed global Ruby gem (`kreuzberg 4.0.0.pre.rc.6`) had not been compiled with its native extension. When the subprocess attempted to `require 'kreuzberg'`, it failed with:

```
[DEBUG] FAILED to load kreuzberg gem: LoadError - cannot load such file -- kreuzberg
[DEBUG] Gem root: NOT FOUND
```

The `gem list` output showed:
```
kreuzberg version=4.0.0.pre.rc.6 platform=ruby because its extensions are not built
```

**Cause**: The gem was installed as a pre-built binary without the native extension (`kreuzberg_rb.so`/`kreuzberg_rb.bundle`). This happens when:
- The gem is installed globally without rebuilding extensions
- The Ruby extension task in the Rakefile wasn't being executed during global installation

**Fix**: Rebuild the gem locally with `bundle exec rake compile && bundle exec rake build`, then reinstall it. This ensures:
1. The native extension is compiled via the Magnus FFI bridge
2. The Rust code is properly linked to the Rust FFI library
3. All dependencies are included

### Issue 2: Missing Ruby Library Path in Subprocess Adapter

Even with the extension built, the subprocess adapter in `tools/benchmark-harness/src/adapters/kreuzberg.rs` was not passing the Ruby gem's lib directory to the Ruby interpreter.

**Problem**: The Ruby adapter was using:
```rust
let (command, mut args) = find_ruby()?;
args.push(script_path.to_string_lossy().to_string());
```

This invokes Ruby like:
```bash
ruby /path/to/kreuzberg_extract.rb sync /path/to/file
```

But Ruby has no way to load the `kreuzberg` gem because:
- The gem might not be installed globally
- Even if installed, the load path isn't properly configured in subprocess context
- Different Ruby environments use different gem paths

**Fix**: Add the `-I` flag to include the gem's lib directory:
```rust
if let Ok(gem_lib_path) = get_ruby_gem_lib_path() {
    args.push("-I".to_string());
    args.push(gem_lib_path.to_string_lossy().to_string());
}
```

This invokes:
```bash
ruby -I /path/to/kreuzberg/lib /path/to/kreuzberg_extract.rb sync /path/to/file
```

### Issue 3: Poor Error Diagnostics

The subprocess adapter had minimal error reporting:

```rust
if !output.status.success() {
    return Err(Error::Benchmark(format!(
        "Subprocess failed with exit code {:?}\nstderr: {}",
        output.status.code(),
        stderr
    )));
}
```

**Problem**:
- Didn't show the command that was being executed
- Didn't include stdout in error messages (which may contain diagnostic info)
- Didn't show the arguments passed to the command

This made it impossible to diagnose what went wrong without adding manual debugging.

**Fix**: Enhanced error reporting to include:
- Full command and arguments
- Both stdout and stderr
- Spawn error details

## Solutions Implemented

### 1. Ruby Gem Library Path Discovery (`get_ruby_gem_lib_path`)

New function in `tools/benchmark-harness/src/adapters/kreuzberg.rs`:

```rust
fn get_ruby_gem_lib_path() -> Result<PathBuf> {
    // Try workspace first
    let workspace_root = workspace_root()?;
    let workspace_gem_lib = workspace_root.join("packages/ruby/lib");
    if workspace_gem_lib.exists() {
        return Ok(workspace_gem_lib);
    }

    // Try to find installed gem via `ruby -e` call
    use std::process::Command;
    if let Ok(output) = Command::new("ruby")
        .arg("-e")
        .arg("puts Gem.loaded_specs['kreuzberg_rb']&.lib_dirs&.first || ''")
        .output()
    {
        if output.status.success() {
            let gem_path = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if !gem_path.is_empty() {
                return Ok(PathBuf::from(gem_path));
            }
        }
    }

    Err(crate::Error::Config(
        "Could not find kreuzberg gem lib directory. Install the gem or use workspace build.".to_string(),
    ))
}
```

**Strategy**:
1. First checks for workspace build at `packages/ruby/lib`
2. Falls back to finding installed gem via Ruby introspection
3. Returns clear error if neither works

### 2. Updated Ruby Adapters

Both `create_ruby_sync_adapter()` and `create_ruby_batch_adapter()` now:

```rust
// Add -I flag for gem lib directory so Ruby can find the kreuzberg gem
if let Ok(gem_lib_path) = get_ruby_gem_lib_path() {
    args.push("-I".to_string());
    args.push(gem_lib_path.to_string_lossy().to_string());
}
```

### 3. Improved Subprocess Error Reporting

Enhanced `execute_subprocess()` in `tools/benchmark-harness/src/adapters/subprocess.rs`:

```rust
let child = cmd
    .spawn()
    .map_err(|e| Error::Benchmark(format!(
        "Failed to spawn subprocess '{}' with args {:?}: {}",
        self.command.display(),
        self.args,
        e
    )))?;

// ...

if !output.status.success() {
    // Include more diagnostic information in the error message
    let mut error_msg = format!(
        "Subprocess failed with exit code {:?}",
        output.status.code()
    );
    if !stderr.is_empty() {
        error_msg.push_str(&format!("\nstderr: {}", stderr));
    }
    if !stdout.is_empty() && stdout.len() < 500 {
        error_msg.push_str(&format!("\nstdout: {}", stdout));
    }
    return Err(Error::Benchmark(error_msg));
}
```

## Testing & Verification

### Test 1: Ruby Script with Debug Enabled

```bash
export KREUZBERG_BENCHMARK_DEBUG=true
export LD_LIBRARY_PATH="/path/to/target/release:${LD_LIBRARY_PATH:-}"
export DYLD_LIBRARY_PATH="/path/to/target/release:${DYLD_LIBRARY_PATH:-}"

ruby -I packages/ruby/lib tools/benchmark-harness/scripts/kreuzberg_extract.rb sync /path/to/test.pdf
```

**Result**: Successfully loaded gem and extracted PDF with proper JSON output.

### Test 2: Full Benchmark Run

```bash
export LD_LIBRARY_PATH="/path/to/target/release:${LD_LIBRARY_PATH:-}"
export DYLD_LIBRARY_PATH="/path/to/target/release:${DYLD_LIBRARY_PATH:-}"

./target/release/benchmark-harness run \
  --fixtures tools/benchmark-harness/fixtures \
  --frameworks kreuzberg-ruby-sync \
  --mode single-file \
  --iterations 1 \
  --max-concurrent 1 \
  --output test-ruby-results
```

**Result**: Successfully completed all 31 benchmarks with no failures:
```
Completed 31 benchmark(s)
Summary:
  Successful: 31
  Failed: 0
  Total: 31
Results written to: test-ruby-results/results.json
```

## Files Modified

1. **tools/benchmark-harness/src/adapters/kreuzberg.rs**
   - Added `get_ruby_gem_lib_path()` function
   - Updated `create_ruby_sync_adapter()` to include `-I` flag
   - Updated `create_ruby_batch_adapter()` to include `-I` flag

2. **tools/benchmark-harness/src/adapters/subprocess.rs**
   - Enhanced spawn error reporting with command and args
   - Improved failure error reporting with stdout/stderr details

## Key Insights

1. **Workspace builds are preferable**: The function prioritizes `packages/ruby/lib` since it's always available and up-to-date during development.

2. **Subprocess isolation**: Ruby subprocesses don't inherit the parent Bundler context, requiring explicit library path configuration.

3. **Error visibility is critical**: Silent failures in benchmarks are hard to diagnose. The improved error messages now make issues immediately obvious.

4. **Native extensions matter**: Compiled extensions provide the bridge between Ruby and Rust. Ensure they're always built before testing.

## Recommendations

1. **CI/CD**: Ensure benchmark runs always use locally built gems (from `bundle exec rake compile`)
2. **Documentation**: Add note to benchmark README about native extension requirement
3. **Testing**: Add automated tests for Ruby adapter initialization
4. **Future**: Consider centralizing library path management across all subprocess adapters

## Performance Results Sample

After fix, Ruby benchmarks produce meaningful metrics:
```json
{
  "framework": "kreuzberg-ruby-sync",
  "file_size": 358400,
  "success": true,
  "duration": "0.387s",
  "extraction_duration": "0.215s",
  "subprocess_overhead": "0.172s",
  "metrics": {
    "peak_memory_bytes": 18202624,
    "throughput_bytes_per_sec": 483763.07,
    "p50_memory_bytes": 18169856,
    "p95_memory_bytes": 18169856,
    "p99_memory_bytes": 18169856
  },
  "cold_start_duration": "0.215656s"
}
```

The subprocess overhead (~172ms) is expected and represents:
- Ruby VM startup
- Gem loading
- FFI bridge initialization
- Ruby-to-Rust call overhead

This is acceptable for benchmarking purposes as it's consistent across runs.
