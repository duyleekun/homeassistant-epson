#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
monitor="$repo_root/rootfs/etc/services.d/queue-monitor/run"
saned="$repo_root/rootfs/etc/services.d/saned/run"

bash -n "$monitor" "$saned"
grep -q 'lpstat -h' "$monitor"
grep -q 'usb-no-reattach-default=true' "$monitor"
grep -q 'cupsdisable' "$monitor"
grep -q 'cupsenable' "$monitor"
grep -q 'release_held_jobs' "$monitor"
grep -q 'queue-monitor/run' "$saned"

echo "queue monitor validation passed"

