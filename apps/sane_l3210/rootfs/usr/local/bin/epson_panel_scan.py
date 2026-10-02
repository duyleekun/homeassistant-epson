#!/usr/bin/env python3
import os
import sys

from epson_scan_engine import fail_scan, post_activity, scan_panel


if __name__ == "__main__":
    button = os.environ.get("ES2_BUTTON_NUM")
    post_activity("button_pressed", source="panel_button", button=button)
    try:
        metadata = scan_panel()
    except Exception as exc:
        fail_scan("panel_button", str(exc))
        print(f"Panel scan failed: {exc}", flush=True)
        sys.exit(1)
    print(f"Scan finished: {metadata['filename']}", flush=True)
    sys.exit(0)
