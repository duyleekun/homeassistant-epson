#!/usr/bin/env python3
from __future__ import annotations

import argparse

from epson_scan_engine import update_status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connected", choices=("true", "false"))
    parser.add_argument("--state")
    args = parser.parse_args()
    changes = {}
    if args.connected is not None:
        changes["connected"] = args.connected == "true"
    if args.state is not None:
        changes["state"] = args.state
    update_status(**changes)


if __name__ == "__main__":
    main()
