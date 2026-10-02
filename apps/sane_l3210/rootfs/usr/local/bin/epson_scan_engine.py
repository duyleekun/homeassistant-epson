#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen

try:
    import websocket
except ImportError:  # pragma: no cover - image build provides this package
    websocket = None

BASE = Path("/share/epson-scan")
OUTPUT = BASE / "output"
DEFAULT_SETTINGS = BASE / "DefaultSettings.SF2"
STATUS_PATH = BASE / "status.json"
DEVICE_ID = "L3210 Series:583848523332363114"
EVENT_ACTIVITY = "epson_l3210_activity"
SUPERVISOR_EVENT_URL = "http://supervisor/core/api/events/epson_l3210_activity"
SUPERVISOR_WS_URL = "ws://supervisor/core/websocket"


def ensure_dirs() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def update_status(**changes) -> dict:
    ensure_dirs()
    try:
        current = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        current = {}
    if not isinstance(current, dict):
        current = {}
    current.update(changes)
    current["updated_at"] = datetime.now(timezone.utc).isoformat()
    temp_fd, temp_name = tempfile.mkstemp(
        dir=str(BASE), prefix=".status-", suffix=".tmp"
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as stream:
            json.dump(current, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        temp_path.replace(STATUS_PATH)
    finally:
        temp_path.unlink(missing_ok=True)
    return current


def _fire_activity_websocket(payload: dict) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if websocket is None or not token:
        raise RuntimeError("Home Assistant WebSocket client is unavailable")
    connection = websocket.create_connection(SUPERVISOR_WS_URL, timeout=10)
    try:
        greeting = json.loads(connection.recv())
        if greeting.get("type") != "auth_required":
            raise RuntimeError("unexpected Home Assistant WebSocket greeting")
        connection.send(json.dumps({"type": "auth", "access_token": token}))
        auth_result = json.loads(connection.recv())
        if auth_result.get("type") != "auth_ok":
            raise RuntimeError("Home Assistant WebSocket authentication failed")
        connection.send(
            json.dumps(
                {
                    "id": 1,
                    "type": "fire_event",
                    "event_type": EVENT_ACTIVITY,
                    "event_data": payload,
                }
            )
        )
        result = json.loads(connection.recv())
        if result.get("id") != 1 or not result.get("success"):
            raise RuntimeError(f"Home Assistant rejected scanner activity: {result}")
    finally:
        connection.close()


def _post_activity_rest(payload: dict) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise RuntimeError("SUPERVISOR_TOKEN is unavailable")
    request = Request(
        SUPERVISOR_EVENT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=10):
        pass


def post_activity(event_type: str, **data) -> None:
    payload = {"type": event_type, **data}
    update_status(last_activity=payload)
    try:
        _fire_activity_websocket(payload)
        return
    except Exception as websocket_error:
        print(f"Could not publish scanner activity over WebSocket: {websocket_error}", flush=True)
    try:
        _post_activity_rest(payload)
    except Exception as rest_error:
        print(f"Could not publish scanner activity over REST: {rest_error}", flush=True)


def ensure_default_settings() -> None:
    ensure_dirs()
    if DEFAULT_SETTINGS.exists():
        return
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(
        ["epsonscan2", "--create"],
        cwd=str(BASE),
        env=env,
        timeout=45,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def load_settings() -> dict:
    ensure_default_settings()
    return json.loads(DEFAULT_SETTINGS.read_text(encoding="utf-8-sig"))


def set_int(settings: dict, key: str, value: int) -> None:
    settings[key] = {"int": int(value)}


def set_string(settings: dict, key: str, value: str) -> None:
    settings[key] = {"string": str(value)}


def build_settings(resolution: int, prefix: str, color_mode: str) -> Path:
    data = load_settings()
    settings = data["Preset"][0]["0"][0]
    set_string(settings, "UserDefinePath", str(OUTPUT))
    set_string(settings, "FileNamePrefix", prefix)
    set_int(settings, "FileNameOverWrite", 0)
    set_int(settings, "Resolution", resolution)
    set_int(settings, "ImageFormat", 1)
    set_int(settings, "ColorType", 1 if color_mode == "grayscale" else 0)
    path = BASE / "HassScanSettings.SF2"
    path.write_text("\ufeff" + json.dumps(data, indent=4), encoding="utf-8")
    return path


def current_epson2_device() -> str | None:
    try:
        devices = subprocess.run(
            ["scanimage", "-L"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
            check=False,
        ).stdout
    except Exception:
        return None
    for line in devices.splitlines():
        if "`epson2:libusb:" in line:
            return line.split("`", 1)[1].split("'", 1)[0]
    return None


def _scan_metadata(path: Path, source: str, resolution: int, color_mode: str) -> dict:
    return {
        "filename": path.name,
        "relative_path": path.name,
        "size": path.stat().st_size,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "resolution": resolution,
        "color_mode": color_mode,
    }


def _newest_output(prefix: str, started_at: float) -> Path | None:
    candidates = [
        path
        for path in OUTPUT.glob(f"{prefix}*")
        if path.is_file() and path.stat().st_mtime >= started_at and path.stat().st_size > 0
    ]
    return max(candidates, key=lambda path: path.stat().st_mtime, default=None)


def scan_native(resolution: int, color_mode: str, prefix: str, source: str, request_id: str | None = None) -> dict:
    ensure_dirs()
    settings = build_settings(resolution, prefix, color_mode)
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    update_status(state="scanning", scan_request_id=request_id, error=None)
    started_at = time.time()
    device = DEVICE_ID
    result = subprocess.run(
        ["epsonscan2", "--scan", device, str(settings)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=300,
        check=False,
    )
    path = _newest_output(prefix, started_at)
    if result.returncode != 0 or path is None:
        detail = result.stdout[-1000:].strip()
        raise RuntimeError(f"Epson Scan 2 exited {result.returncode}: {detail}")
    metadata = _scan_metadata(path, source, resolution, color_mode)
    update_status(state="idle", last_scan=metadata, scan_request_id=None, error=None)
    post_activity("scan_completed", request_id=request_id, **metadata)
    return metadata


def scan_panel() -> dict:
    ensure_dirs()
    device = current_epson2_device() or "epson2:libusb:009:014"
    prefix = time.strftime("panel-%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1000000:06d}"
    output = OUTPUT / f"{prefix}.jpg"
    update_status(state="scanning", scan_request_id=None, error=None)
    command = [
        "scanimage",
        "-d",
        device,
        "--format=jpeg",
        "--mode",
        "Color",
        "--resolution",
        "200",
        "-x",
        "215.9",
        "-y",
        "297.18",
    ]
    try:
        with output.open("wb") as stream:
            result = subprocess.run(
                command,
                stdout=stream,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
            )
    except Exception:
        output.unlink(missing_ok=True)
        raise
    if result.returncode != 0 or output.stat().st_size == 0:
        detail = result.stderr[-1000:].strip()
        output.unlink(missing_ok=True)
        raise RuntimeError(f"SANE panel scan exited {result.returncode}: {detail}")
    metadata = _scan_metadata(output, "panel_button", 200, "color")
    update_status(state="idle", last_scan=metadata, scan_request_id=None, error=None)
    post_activity("scan_completed", request_id=None, **metadata)
    return metadata


def fail_scan(source: str, error: str, request_id: str | None = None) -> None:
    update_status(state="idle", scan_request_id=None, error=error)
    post_activity("scan_failed", request_id=request_id, source=source, error=error)
