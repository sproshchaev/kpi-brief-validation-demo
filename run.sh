#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
work_dir=$(mktemp -d)
trap 'rm -f -- "$work_dir/daily_totals.csv" "$work_dir/actual.txt"; rmdir -- "$work_dir"' EXIT

python3 generate_data.py > "$work_dir/daily_totals.csv"
cmp data/daily_totals.csv "$work_dir/daily_totals.csv"
python3 brief.py "$work_dir/daily_totals.csv" data/cases.json > "$work_dir/actual.txt"
if ! diff -u expected.txt "$work_dir/actual.txt"; then
  exit 1
fi
cat "$work_dir/actual.txt"
