#!/usr/bin/env python3
import json

with open("coverage.json", "r") as f:
    data = json.load(f)

# Extract coverage information for each file
coverage_info = []
for file_path, file_data in data["files"].items():
    summary = file_data["summary"]
    missing_lines_count = summary.get("missing_lines", 0)
    missing_branches = summary.get("missing_branches", 0)
    missing_lines_list = file_data.get("missing_lines", [])

    coverage_info.append(
        {
            "file": file_path,
            "covered_lines": summary["covered_lines"],
            "total_lines": summary["num_statements"],
            "coverage_percent": summary["percent_covered"],
            "missing_lines_count": missing_lines_count,
            "missing_lines_list": missing_lines_list,
            "missing_branches": missing_branches,
        }
    )

# Sort by coverage percentage (lowest first)
coverage_info.sort(key=lambda x: x["coverage_percent"])

# Display files with lowest coverage
print("Files with lowest test coverage:")
print("=" * 60)
for i, info in enumerate(coverage_info[:10]):
    print(f"{i + 1}. File: {info['file']}")
    print(
        f"   Coverage: {info['coverage_percent']:.1f}% ({info['covered_lines']}/{info['total_lines']} lines)"
    )
    print(f"   Missing lines count: {info['missing_lines_count']}")
    print(f"   Missing branches: {info['missing_branches']}")

    # Show some specific missing line numbers for reference
    if info["missing_lines_list"] and len(info["missing_lines_list"]) <= 10:
        print(f"   Missing lines: {info['missing_lines_list']}")
    elif info["missing_lines_list"]:
        print(f"   Missing lines: {info['missing_lines_list'][:10]}...")

    print("-" * 60)

# Also show summary of files with < 80% coverage
low_coverage_files = [info for info in coverage_info if info["coverage_percent"] < 80]
print(f"\nFiles with coverage < 80%: {len(low_coverage_files)}")
for info in low_coverage_files:
    print(f"- {info['file']}: {info['coverage_percent']:.1f}%")
