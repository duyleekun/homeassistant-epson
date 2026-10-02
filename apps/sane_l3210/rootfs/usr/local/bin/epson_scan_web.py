#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
import html
import json
import os
import signal
import subprocess
import threading
import time

BASE = Path("/share/epson-scan")
OUTPUT = BASE / "output"
DEFAULT_SETTINGS = BASE / "DefaultSettings.SF2"
PANEL_DISABLED = BASE / "panel-listener.disabled"
DEVICE_ID = "L3210 Series:583848523332363114"
SCAN_LOCK = threading.Lock()
PANEL_LOCK = threading.Lock()
PANEL_PROCESS = None
PANEL_LISTENER_LOCK = threading.Lock()
PANEL_LISTENER = None
PANEL_STATUS = "Physical panel-button scanning is unavailable on this Linux host. Use Scan above."
INGRESS_PROXY = "172.30.32.2"
INGRESS_BIND = "172.30.32.1"


def ensure_dirs():
    BASE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def ensure_default_settings():
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


def load_settings():
    ensure_default_settings()
    return json.loads(DEFAULT_SETTINGS.read_text(encoding="utf-8-sig"))


def set_int(settings, key, value):
    settings[key] = {"int": int(value)}


def set_string(settings, key, value):
    settings[key] = {"string": str(value)}


def build_settings(resolution, prefix, overrides=None):
    overrides = overrides or {}
    data = load_settings()
    settings = data["Preset"][0]["0"][0]
    set_string(settings, "UserDefinePath", str(OUTPUT))
    set_string(settings, "FileNamePrefix", prefix)
    set_int(settings, "FileNameOverWrite", 0)
    set_int(settings, "Resolution", resolution)
    set_int(settings, "ImageFormat", overrides.get("image_format", 1))
    set_int(settings, "ColorType", overrides.get("ColorType", 0))
    set_int(settings, "FunctionalUnit", overrides.get("FunctionalUnit", 0))
    set_int(settings, "FunctionalUnit_Auto", overrides.get("FunctionalUnit_Auto", 0))
    set_int(settings, "PaperDeskew", overrides.get("PaperDeskew", 0))
    set_int(settings, "AutoSize", overrides.get("AutoSize", 0))
    for key, value in overrides.items():
        if key in ("image_format", "ColorType", "FunctionalUnit", "FunctionalUnit_Auto", "PaperDeskew", "AutoSize"):
            continue
        set_int(settings, key, value)
    path = BASE / "WebScanSettings.SF2"
    path.write_text("\ufeff" + json.dumps(data, indent=4), encoding="utf-8")
    return path


def list_scans():
    ensure_dirs()
    return sorted(
        [p for p in OUTPUT.iterdir() if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def start_panel_listener():
    global PANEL_LISTENER, PANEL_STATUS
    if PANEL_DISABLED.exists():
        PANEL_STATUS = "Physical panel-button scanning is unavailable on this Linux host. Use Scan above."
        return
    with PANEL_LISTENER_LOCK:
        if PANEL_LISTENER is not None and PANEL_LISTENER.poll() is None:
            return
        PANEL_LISTENER = subprocess.Popen(
            ["/usr/local/bin/es2button", "/usr/local/bin/epson_panel_scan.py"],
            env={
                "RUST_LOG": "info",
                "LD_LIBRARY_PATH": "/opt/es2button/lib",
            },
        )
    time.sleep(1)
    if PANEL_LISTENER.poll() is None:
        PANEL_STATUS = "Panel-button scanning is enabled. Hold both copy buttons to scan."
    else:
        PANEL_STATUS = "Panel-button listener could not start."


def stop_panel_listener():
    global PANEL_LISTENER
    with PANEL_LISTENER_LOCK:
        proc = PANEL_LISTENER
        PANEL_LISTENER = None
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    time.sleep(5)


def native_scan(resolution, prefix, overrides=None, manage_listener=True):
    settings = build_settings(resolution, prefix, overrides or {})
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    if manage_listener:
        stop_panel_listener()
    try:
        refresh_native_device(env)
        result = subprocess.run(
            ["epsonscan2", "--scan", DEVICE_ID, str(settings)],
            env=env,
            timeout=300,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    finally:
        if manage_listener:
            start_panel_listener()
    if result.returncode == 0:
        return "Scan finished."
    return f"Scan command exited {result.returncode}: {result.stdout[-500:]}"


def refresh_native_device(env=None):
    """Refresh Epson Scan 2's USB enumeration after a hotplug transition."""
    refresh_env = env or os.environ.copy()
    refresh_env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run(
        ["epsonscan2", "--get-status"],
        env=refresh_env,
        timeout=45,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def current_epson2_device():
    devices = subprocess.run(
        ["scanimage", "-L"],
        timeout=10,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    ).stdout
    for line in devices.splitlines():
        if "`epson2:libusb:" in line:
            return line.split("`", 1)[1].split("'", 1)[0]
    return None


def page(message=""):
    rows = []
    for p in list_scans()[:30]:
        stat = p.stat()
        rows.append(
            "<tr>"
            f"<td><a href='files/{quote(p.name)}'>{html.escape(p.name)}</a></td>"
            f"<td>{stat.st_size:,} bytes</td>"
            f"<td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))}</td>"
            "</tr>"
        )
    message_html = f"<p class='msg'>{html.escape(message)}</p>" if message else ""
    panel_html = f"<p class='msg'>{html.escape(PANEL_STATUS)}</p>"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Epson L3210 Scanner</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; margin: 24px; color: #172026; }}
    main {{ max-width: 760px; margin: 0 auto; }}
    form {{ display: flex; gap: 12px; align-items: end; flex-wrap: wrap; margin: 20px 0; }}
    label {{ display: grid; gap: 6px; font-size: 14px; }}
    input, select, button {{ font: inherit; padding: 9px 11px; border: 1px solid #b8c2cc; border-radius: 6px; }}
    button {{ background: #1457d9; color: white; border-color: #1457d9; cursor: pointer; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 18px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #e3e8ee; padding: 10px 8px; }}
    .msg {{ padding: 10px 12px; background: #eef7ee; border: 1px solid #b9dfb9; border-radius: 6px; }}
  </style>
</head>
<body>
<main>
  <h1>Epson L3210 Scanner</h1>
  {message_html}
  {panel_html}
  <form method="post" action="scan">
    <label>Resolution
      <select name="resolution">
        <option value="200">200 dpi</option>
        <option value="100">100 dpi</option>
        <option value="300">300 dpi</option>
      </select>
    </label>
    <label>Filename prefix
      <input name="prefix" value="scan" maxlength="32">
    </label>
    <label>Mode
      <select name="color">
        <option value="0">Color</option>
        <option value="1">Grayscale</option>
      </select>
    </label>
    <button type="submit">Scan</button>
  </form>
  <h2>Recent Scans</h2>
  <table>
    <thead><tr><th>File</th><th>Size</th><th>Created</th></tr></thead>
    <tbody>{''.join(rows) or '<tr><td colspan="3">No scans yet.</td></tr>'}</tbody>
  </table>
</main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(page())
            return
        if parsed.path == "/diag/sane":
            self.send_text(sane_diagnostics())
            return
        if parsed.path == "/diag/es2button":
            self.send_text(run_diag(["es2button", "--list"]))
            return
        if parsed.path == "/diag/es2button-listen":
            self.send_text(
                run_diag(
                    [
                        "/usr/bin/env",
                        "RUST_LOG=trace",
                        "LD_LIBRARY_PATH=/opt/es2button/lib",
                        "timeout",
                        "15",
                        "es2button",
                        "/usr/bin/env",
                    ],
                    timeout=20,
                )
            )
            return
        if parsed.path.startswith("/files/"):
            name = unquote(parsed.path.removeprefix("/files/"))
            path = (OUTPUT / name).resolve()
            if path.parent != OUTPUT.resolve() or not path.exists():
                self.send_error(404)
                return
            content_type = "image/jpeg"
            if path.suffix.lower() in (".pnm", ".ppm", ".pgm"):
                content_type = "image/x-portable-anymap"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(path.stat().st_size))
            self.end_headers()
            with path.open("rb") as f:
                self.wfile.write(f.read())
            return
        self.send_error(404)

    def do_POST(self):
        if self.path == "/arm":
            self.handle_arm()
            return
        if self.path == "/cancel-panel":
            self.handle_cancel_panel()
            return
        if self.path != "/scan":
            self.send_error(404)
            return
        self.handle_scan()

    def handle_scan(self):
        length = int(self.headers.get("Content-Length", "0"))
        params = parse_qs(self.rfile.read(length).decode("utf-8"))
        resolution = int(params.get("resolution", ["200"])[0])
        if resolution not in (100, 200, 300):
            resolution = 200
        prefix = params.get("prefix", ["scan"])[0]
        prefix = "".join(c for c in prefix if c.isalnum() or c in "-_")[:32] or "scan"
        override_map = {
            "unit": "FunctionalUnit",
            "unit_auto": "FunctionalUnit_Auto",
            "doc": "documentType",
            "color": "ColorType",
            "format": "image_format",
            "deskew": "PaperDeskew",
            "autosize": "AutoSize",
            "fixed": "FixedDocumentSize",
            "width": "ScanAreaWidth",
            "height": "ScanAreaHeight",
            "user_width": "UserScanAreaWidth",
            "user_height": "UserScanAreaHeight",
            "offset_x": "ScanAreaOffsetX",
            "offset_y": "ScanAreaOffsetY",
        }
        overrides = {}
        for param, key in override_map.items():
            if param not in params:
                continue
            try:
                overrides[key] = int(params[param][0])
            except ValueError:
                pass
        if not SCAN_LOCK.acquire(blocking=False):
            self.send_html(page("A scan is already running."))
            return
        try:
            message = native_scan(resolution, prefix, overrides)
        except Exception as exc:
            message = f"Scan failed: {exc}"
        finally:
            SCAN_LOCK.release()
        self.send_html(page(message))

    def handle_arm(self):
        self.send_html(
            page(
                "Physical panel-button scanning is unavailable on this Linux "
                "host. Use Scan above."
            )
        )

    def handle_cancel_panel(self):
        global PANEL_STATUS
        with PANEL_LOCK:
            active = PANEL_PROCESS is not None and PANEL_PROCESS.poll() is None
        if active:
            cancel_panel_scan()
            PANEL_STATUS = "Panel scan canceled."
            self.send_html(page("Panel scan canceled."))
            return
        self.send_html(page("No panel scan is running."))

    def send_html(self, body):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, body):
        data = body.encode("utf-8", errors="replace")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_diag(command, timeout=20):
    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return f"$ {' '.join(command)}\nexit={result.returncode}\n{result.stdout}\n"
    except Exception as exc:
        return f"$ {' '.join(command)}\nfailed: {exc}\n"


def sane_diagnostics():
    return "\n".join(
        [
            run_diag(["scanimage", "-L"]),
            run_diag(["scanimage", "-A"]),
        ]
    )


def wait_for_button(timeout):
    device = current_epson2_device() or "epson2:libusb:009:011"
    command = [
        "scanimage",
        "-d",
        device,
        "--wait-for-button=yes",
        "--mode",
        "Gray",
        "--resolution",
        "75",
        "-x",
        "10",
        "-y",
        "10",
    ]
    try:
        started = time.time()
        result = subprocess.run(
            command,
            timeout=timeout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        elapsed = time.time() - started
        return (
            f"$ {' '.join(command)}\n"
            f"exit={result.returncode}\n"
            f"elapsed={elapsed:.1f}s\n"
            f"bytes={len(result.stdout)}\n"
            f"tail={result.stdout[-500:].decode('utf-8', errors='replace')}\n"
        )
    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s waiting for a scanner button.\n"
    except Exception as exc:
        return f"Button wait failed: {exc}\n"


def run_panel_scan_job():
    global PANEL_STATUS
    with SCAN_LOCK:
        try:
            PANEL_STATUS = arm_panel_scan(120)
        except Exception as exc:
            PANEL_STATUS = f"Panel scan failed: {exc}"
    print(PANEL_STATUS, flush=True)


def cancel_panel_scan():
    global PANEL_PROCESS
    with PANEL_LOCK:
        proc = PANEL_PROCESS
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def arm_panel_scan(timeout):
    global PANEL_PROCESS
    device = current_epson2_device()
    if not device:
        return "Panel scan could not arm: epson2 scanner backend is not available."
    output = OUTPUT / f"{time.strftime('panel-%Y%m%d-%H%M%S')}.pnm"
    command = [
        "scanimage",
        "-d",
        device,
        "--wait-for-button=yes",
        "--mode",
        "Color",
        "--resolution",
        "150",
        "-x",
        "215.9",
        "-y",
        "297.18",
    ]
    started = time.time()
    try:
        with output.open("wb") as f:
            proc = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
            )
            with PANEL_LOCK:
                PANEL_PROCESS = proc
            try:
                _, stderr = proc.communicate(timeout=timeout)
                returncode = proc.returncode
            finally:
                with PANEL_LOCK:
                    if PANEL_PROCESS is proc:
                        PANEL_PROCESS = None
    except subprocess.TimeoutExpired:
        cancel_panel_scan()
        output.unlink(missing_ok=True)
        return f"Panel scan timed out after {timeout}s."
    elapsed = time.time() - started
    if returncode != 0:
        output.unlink(missing_ok=True)
        return f"Panel button wait exited {returncode}: {stderr[-500:]}"
    return f"Panel scan finished after {elapsed:.1f}s: {output.name}"


if __name__ == "__main__":
    ensure_default_settings()
    start_panel_listener()

    class IngressOnlyServer(ThreadingHTTPServer):
        def verify_request(self, request, client_address):
            return True

    IngressOnlyServer((INGRESS_BIND, 8101), Handler).serve_forever()
