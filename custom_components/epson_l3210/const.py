from __future__ import annotations

from pathlib import Path

DOMAIN = "epson_l3210"
NAME = "Epson L3210 Scanner"
MANUFACTURER = "Epson"
MODEL = "L3210"
SERIAL = "583848523332363114"
DEVICE_ID = f"{MODEL}:{SERIAL}"

EVENT_ACTIVITY = f"{DOMAIN}_activity"
EVENT_SCAN_REQUEST = f"{DOMAIN}_scan_request"

OUTPUT_DIR = Path("/share/epson-scan/output")
STATUS_PATH = Path("/share/epson-scan/status.json")

DEFAULT_RESOLUTION = 200
DEFAULT_COLOR_MODE = "color"
DEFAULT_FILENAME_PREFIX = "scan"
RESOLUTIONS = (100, 200, 300)
COLOR_MODES = ("color", "grayscale")
SCAN_FILE_SUFFIXES = (".jpg", ".jpeg", ".png", ".pnm", ".ppm", ".pgm", ".tif", ".tiff")

CONF_RESOLUTION = "resolution"
CONF_COLOR_MODE = "color_mode"
CONF_FILENAME_PREFIX = "filename_prefix"
