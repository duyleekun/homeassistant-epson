#!/usr/bin/env python3
import time

from epson_scan_web import native_scan


if __name__ == "__main__":
    prefix = time.strftime("panel-%Y%m%d-%H%M%S")
    print(native_scan(200, prefix, manage_listener=False), flush=True)
