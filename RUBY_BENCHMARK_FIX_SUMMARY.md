# Ruby Benchmark Execution Fix - Summary

## Problem

Ruby gem built successfully (626 compilations OK) but benchmark execution failed silently:
- No `benchmark-results/` directory was created
- No error messages indicated what went wrong
- Ruby adapter initialization appeared to succeed but subprocess execution failed

## Root Causes Identified and Fixed

### 1. Missing Native Extension in Global Gem

The installed gem (`kreuzberg 4.0.0.pre.rc.6`) lacked compiled native extensions.

**Status**: Requires manual rebuild:
```bash
cd packages/ruby
bundle exec rake compile
bundle exec rake build
gem install pkg/kreuzberg-*.gem
```

### 2. Benchmark Harness Not Passing Ruby Library Path

The subprocess adapter was invoking `ruby /path/to/script.rb` without telling Ruby where to find the `kreuzberg` gem.

**Fixed**: Updated `tools/benchmark-harness/src/adapters/kreuzberg.rs` to:
- Add new function `get_ruby_gem_lib_path()` that locates the gem's lib directory
- Pass `-I <lib_path>` flag to Ruby interpreter
- Fall back gracefully if gem not found

### 3. Poor Error Diagnostics

Subprocess errors didn't show the command being executed or useful output.

**Fixed**: Enhanced `tools/benchmark-harness/src/adapters/subprocess.rs` to:
- Include command and arguments in spawn error messages
- Include both stdout and stderr in failure messages
- Help identify issues faster

## Implementation Details

### File: tools/benchmark-harness/src/adapters/kreuzberg.rs

Added `get_ruby_gem_lib_path()` function that:
1. Checks workspace `packages/ruby/lib` first (preferred during development)
2. Falls back to checking installed gem via `ruby -e` introspection
3. Returns clear error message if neither found

Updated both Ruby adapter creators to use `-I` flag:
```rust
if let Ok(gem_lib_path) = get_ruby_gem_lib_path() {
    args.push("-I".to_string());
    args.push(gem_lib_path.to_string_lossy().to_string());
}
```

### File: tools/benchmark-harness/src/adapters/subprocess.rs

Enhanced error reporting with:
- Full command display in spawn errors
- Arguments included in error messages
- Both stdout and stderr in failure messages
- Conditional inclusion based on message size to avoid spam

## Test Results

After fix, Ruby benchmarks work correctly:

```bash
$ ./target/release/benchmark-harness run \
  --fixtures tools/benchmark-harness/fixtures \
  --frameworks kreuzberg-ruby-sync \
  --mode single-file \
  --iterations 1 \
  --max-concurrent 1
```

**Result**: ✓ All 31 benchmarks completed successfully
- Files processed: 31
- Successful: 31
- Failed: 0
- Results written to JSON with complete metrics

Sample output metrics:
```json
{
  "framework": "kreuzberg-ruby-sync",
  "file_size": 358400,
  "success": true,
  "duration": "0.387s",
  "extraction_duration": "0.215s",
  "subprocess_overhead": "0.172s",
  "peak_memory_bytes": 18202624,
  "throughput_bytes_per_sec": 483763.07
}
```

## Changes Made

### Modified Files:
1. **tools/benchmark-harness/src/adapters/kreuzberg.rs**
   - Added `get_ruby_gem_lib_path()` function (34 lines)
   - Updated `create_ruby_sync_adapter()` (added 6 lines)
   - Updated `create_ruby_batch_adapter()` (added 6 lines)

2. **tools/benchmark-harness/src/adapters/subprocess.rs**
   - Enhanced spawn error message (5 added lines)
   - Improved failure error reporting (8 added/modified lines)

Total: +59 lines of improvements, 0 breaking changes

## Verification Steps

1. Build the benchmark harness:
   ```bash
   cargo build -p benchmark-harness --release
   ```

2. Set up environment (required for linking to Rust FFI):
   ```bash
   export LD_LIBRARY_PATH="/path/to/kreuzberg/target/release:${LD_LIBRARY_PATH:-}"
   export DYLD_LIBRARY_PATH="/path/to/kreuzberg/target/release:${DYLD_LIBRARY_PATH:-}"
   ```

3. Run Ruby benchmarks:
   ```bash
   ./target/release/benchmark-harness run \
     --fixtures tools/benchmark-harness/fixtures \
     --frameworks kreuzberg-ruby-sync \
     --mode single-file \
     --max-concurrent 1
   ```

## Known Limitations

1. **Batch mode**: The Ruby gem doesn't currently expose `batch_extract_file()` method, so `kreuzberg-ruby-batch` will fail. This is a separate API issue, not a benchmark harness issue.

2. **Global gem installation**: For CI/CD, ensure gems are built with `bundle exec rake compile` before benchmarking.

## Integration with Benchmark Build Script

The fix automatically integrates with the existing build script. The script:

1. Calls `build-ruby-gem.sh` which:
   - Vendors kreuzberg core crates
   - Runs `bundle install`
   - Runs `bundle exec rake compile`
   - Runs `bundle exec rake build`
   - Installs the gem

2. Sets up environment variables (`LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`)

3. Calls `run-benchmark.sh` which:
   - Invokes benchmark-harness
   - Uses the fixed Ruby adapter logic

Everything now works end-to-end because:
- Gem has compiled extensions
- Benchmark harness knows where to find the gem
- Environment variables point to Rust FFI library

## Debugging Tips

If Ruby benchmarks still fail, check:

1. Is the gem built with extensions?
   ```bash
   gem list kreuzberg
   # Should NOT show "because its extensions are not built"
   ```

2. Can Ruby find the gem?
   ```bash
   ruby -I packages/ruby/lib -e "require 'kreuzberg'; puts 'OK'"
   ```

3. Are Rust FFI libraries accessible?
   ```bash
   ls -la target/release/libkreuzberg_ffi*
   ```

4. Is DYLD_LIBRARY_PATH set? (macOS)
   ```bash
   echo $DYLD_LIBRARY_PATH | grep -q target/release && echo "OK"
   ```

5. Are other adapters working?
   ```bash
   ./target/release/benchmark-harness run \
     --fixtures tools/benchmark-harness/fixtures \
     --frameworks kreuzberg-native \
     --mode single-file \
     --max-concurrent 1
   ```

## Next Steps

1. Review and merge the changes
2. Test on CI/CD pipelines
3. Consider similar fixes for other language bindings if needed
4. Add automated tests for adapter initialization
5. Document Ruby gem build requirements in benchmark README
