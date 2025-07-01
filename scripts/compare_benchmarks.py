#!/usr/bin/env python3
"""Compare benchmark results for performance regression detection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_benchmark_results(file_path: Path) -> dict[str, Any]:
    """Load benchmark results from JSON file."""
    try:
        with file_path.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        sys.exit(1)


def compare_benchmarks(baseline: dict[str, Any], current: dict[str, Any], threshold: float = 0.2) -> bool:
    """Compare benchmark results and detect regressions.

    Args:
        baseline: Baseline benchmark results
        current: Current benchmark results
        threshold: Performance regression threshold (e.g., 0.2 = 20% slower)

    Returns:
        True if no significant regressions detected, False otherwise
    """
    print(f"Comparing benchmarks with {threshold * 100}% regression threshold")
    print("=" * 60)

    baseline_benchmarks = {b["name"]: b for b in baseline["benchmarks"]}
    current_benchmarks = {b["name"]: b for b in current["benchmarks"]}

    regressions = []
    improvements = []

    for name, current_bench in current_benchmarks.items():
        if name not in baseline_benchmarks:
            print(f"NEW: {name} - {current_bench['duration']:.3f}s")
            continue

        baseline_bench = baseline_benchmarks[name]

        # Skip failed benchmarks
        if not current_bench.get("success", True) or not baseline_bench.get("success", True):
            print(f"SKIP: {name} - benchmark failed")
            continue

        # Compare duration
        baseline_duration = baseline_bench["duration"]
        current_duration = current_bench["duration"]

        if baseline_duration > 0:
            change_ratio = (current_duration - baseline_duration) / baseline_duration
            change_percent = change_ratio * 100

            if change_ratio > threshold:
                regressions.append((name, change_percent, baseline_duration, current_duration))
                status = "🔴 REGRESSION"
            elif change_ratio < -0.05:  # 5% improvement threshold
                improvements.append((name, abs(change_percent), baseline_duration, current_duration))
                status = "🟢 IMPROVEMENT"
            else:
                status = "⚪ NO CHANGE"

            print(f"{status}: {name}")
            print(f"  Baseline: {baseline_duration:.3f}s")
            print(f"  Current:  {current_duration:.3f}s")
            print(f"  Change:   {change_percent:+.1f}%")
            print()

    # Print summary
    print("Summary")
    print("=" * 60)

    if improvements:
        print(f"🟢 {len(improvements)} improvement(s):")
        for name, improvement, baseline_dur, current_dur in improvements:
            print(f"  • {name}: {improvement:.1f}% faster ({baseline_dur:.3f}s → {current_dur:.3f}s)")
        print()

    if regressions:
        print(f"🔴 {len(regressions)} regression(s):")
        for name, regression, baseline_dur, current_dur in regressions:
            print(f"  • {name}: {regression:.1f}% slower ({baseline_dur:.3f}s → {current_dur:.3f}s)")
        print()
        return False

    print("✅ No significant performance regressions detected!")
    return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare benchmark results for performance regression detection")
    parser.add_argument("baseline", type=Path, help="Path to baseline benchmark results JSON")
    parser.add_argument("current", type=Path, help="Path to current benchmark results JSON")
    parser.add_argument(
        "--threshold", type=float, default=0.2, help="Performance regression threshold as decimal (default: 0.2 = 20%%)"
    )
    parser.add_argument(
        "--fail-on-regression", action="store_true", help="Exit with non-zero code if regressions detected"
    )

    args = parser.parse_args()

    baseline = load_benchmark_results(args.baseline)
    current = load_benchmark_results(args.current)

    no_regressions = compare_benchmarks(baseline, current, args.threshold)

    if args.fail_on_regression and not no_regressions:
        sys.exit(1)


if __name__ == "__main__":
    main()
