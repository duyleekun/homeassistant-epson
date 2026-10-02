#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import threading
import time

from epson_scan_engine import fail_scan, scan_native, update_status

try:
    import websocket
except ImportError:  # pragma: no cover - image build provides this package
    websocket = None

PANEL_PROCESS = None
RUNNING = True
SCAN_LOCK = threading.Lock()


def stop_running(_signal, _frame) -> None:
    global RUNNING
    RUNNING = False


def start_panel_listener() -> None:
    global PANEL_PROCESS
    if PANEL_PROCESS is not None and PANEL_PROCESS.poll() is None:
        return
    print("Starting native L3210 panel listener", flush=True)
    PANEL_PROCESS = __import__("subprocess").Popen(
        ["/usr/local/bin/l3210-button", "/usr/local/bin/epson_panel_scan.py"],
        env={
            **os.environ,
            "RUST_LOG": "info",
            "LD_LIBRARY_PATH": "/opt/es2button/lib",
        },
    )


def stop_panel_listener() -> None:
    global PANEL_PROCESS
    process = PANEL_PROCESS
    PANEL_PROCESS = None
    if process is None or process.poll() is not None:
        return
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=5)
    except __import__("subprocess").TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def perform_scan(request: dict) -> None:
    request_id = request.get("request_id")
    if not SCAN_LOCK.acquire(blocking=False):
        fail_scan("ha_action", "A scan is already running", request_id)
        return
    try:
        stop_panel_listener()
        scan_native(
            int(request.get("resolution", 200)),
            str(request.get("color_mode", "color")),
            str(request.get("filename_prefix", "scan")),
            "ha_action",
            request_id,
        )
    except Exception as exc:
        fail_scan("ha_action", str(exc), request_id)
    finally:
        start_panel_listener()
        SCAN_LOCK.release()


def websocket_loop() -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if websocket is None or not token:
        print("HA WebSocket bridge is unavailable; panel listener remains active", flush=True)
        while RUNNING:
            time.sleep(10)
        return
    while RUNNING:
        connection = None
        try:
            connection = websocket.create_connection("ws://supervisor/core/websocket", timeout=10)
            message = json.loads(connection.recv())
            if message.get("type") != "auth_required":
                raise RuntimeError(f"Unexpected HA WebSocket greeting: {message}")
            connection.send(json.dumps({"type": "auth", "access_token": token}))
            message = json.loads(connection.recv())
            if message.get("type") != "auth_ok":
                raise RuntimeError(f"HA WebSocket authentication failed: {message}")
            connection.send(
                json.dumps(
                    {
                        "id": 1,
                        "type": "subscribe_events",
                        "event_type": "epson_l3210_scan_request",
                    }
                )
            )
            print("Connected to Home Assistant scan event bridge", flush=True)
            while RUNNING:
                event = json.loads(connection.recv())
                if event.get("type") != "event":
                    continue
                data = event.get("event", {}).get("data", {})
                threading.Thread(target=perform_scan, args=(data,), daemon=True).start()
        except Exception as exc:
            if RUNNING:
                print(f"HA WebSocket bridge disconnected: {exc}", flush=True)
                time.sleep(5)
        finally:
            if connection is not None:
                connection.close()


def main() -> None:
    global RUNNING
    signal.signal(signal.SIGTERM, stop_running)
    signal.signal(signal.SIGINT, stop_running)
    update_status(state="idle", error=None)
    start_panel_listener()
    try:
        websocket_loop()
    finally:
        stop_panel_listener()
        RUNNING = False


if __name__ == "__main__":
    main()
