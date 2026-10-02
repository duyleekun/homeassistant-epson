from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    COLOR_MODES,
    CONF_COLOR_MODE,
    CONF_FILENAME_PREFIX,
    CONF_RESOLUTION,
    DEFAULT_COLOR_MODE,
    DEFAULT_FILENAME_PREFIX,
    DEFAULT_RESOLUTION,
    DOMAIN,
    EVENT_ACTIVITY,
    EVENT_SCAN_REQUEST,
    OUTPUT_DIR,
    RESOLUTIONS,
    STATUS_PATH,
)

PLATFORMS = ["binary_sensor", "button", "event", "image", "number", "select", "sensor", "text"]

SERVICE_SCAN_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_RESOLUTION): vol.All(vol.Coerce(int), vol.In(RESOLUTIONS)),
        vol.Optional(CONF_COLOR_MODE): vol.In(COLOR_MODES),
        vol.Optional(CONF_FILENAME_PREFIX): cv.string,
    }
)


def _read_status() -> dict[str, Any]:
    try:
        status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        status = {}
    if not isinstance(status, dict):
        return {}
    return status


def _scan_files() -> list[Path]:
    try:
        files = [
            path
            for path in OUTPUT_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in {
                ".jpg",
                ".jpeg",
                ".png",
                ".pnm",
                ".ppm",
                ".pgm",
                ".tif",
                ".tiff",
            }
        ]
    except OSError:
        return []
    return sorted(files, key=lambda path: path.stat().st_mtime, reverse=True)


def _normalise_last_scan(status: dict[str, Any]) -> dict[str, Any] | None:
    scan = status.get("last_scan")
    if isinstance(scan, dict) and scan.get("filename"):
        return scan
    files = _scan_files()
    if not files:
        return None
    path = files[0]
    return {
        "filename": path.name,
        "relative_path": path.name,
        "completed_at": path.stat().st_mtime,
        "size": path.stat().st_size,
        "source": "existing_file",
    }


class EpsonCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Read the scanner status file and retain push activity from the app."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=5),
        )
        self._activity: dict[str, Any] | None = None
        self._activity_sequence = 0
        self._listeners: list[Callable[[], None]] = []

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.hass.async_add_executor_job(_read_status)
        except OSError as err:
            raise UpdateFailed(str(err)) from err
        last_scan = _normalise_last_scan(status)
        return {
            "status_available": bool(status),
            "connected": status.get("connected"),
            "state": status.get("state", "unknown"),
            "last_scan": last_scan,
            "updated_at": status.get("updated_at"),
            "activity": self._activity,
            "activity_sequence": self._activity_sequence,
        }

    @callback
    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    @callback
    def handle_activity(self, event: Event) -> None:
        data = dict(event.data)
        self._activity = data
        self._activity_sequence += 1
        current = self.data or {}
        last_scan = current.get("last_scan")
        if data.get("type") == "scan_completed" and data.get("filename"):
            last_scan = {
                key: value
                for key, value in data.items()
                if key in {
                    "filename",
                    "relative_path",
                    "completed_at",
                    "size",
                    "source",
                    "resolution",
                    "color_mode",
                }
            }
        self.async_set_updated_data(
            {
                **current,
                "status_available": True,
                "connected": data.get("connected", current.get("connected")),
                "state": data.get("state", current.get("state", "idle")),
                "last_scan": last_scan,
                "activity": data,
                "activity_sequence": self._activity_sequence,
            }
        )
        for listener in tuple(self._listeners):
            listener()


def _entry_settings(entry: ConfigEntry) -> dict[str, Any]:
    return {
        CONF_RESOLUTION: entry.options.get(CONF_RESOLUTION, DEFAULT_RESOLUTION),
        CONF_COLOR_MODE: entry.options.get(CONF_COLOR_MODE, DEFAULT_COLOR_MODE),
        CONF_FILENAME_PREFIX: entry.options.get(CONF_FILENAME_PREFIX, DEFAULT_FILENAME_PREFIX),
    }


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = EpsonCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    remove_activity_listener = hass.bus.async_listen(EVENT_ACTIVITY, coordinator.handle_activity)
    entry.async_on_unload(remove_activity_listener)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "scan"):

        async def handle_scan(call: ServiceCall) -> None:
            current = next(iter(hass.data[DOMAIN].values()), None)
            if current is None or not (current.data or {}).get("status_available"):
                raise HomeAssistantError("Epson scanner app is not connected")
            settings = _entry_settings(entry)
            resolution = call.data.get(CONF_RESOLUTION, settings[CONF_RESOLUTION])
            color_mode = call.data.get(CONF_COLOR_MODE, settings[CONF_COLOR_MODE])
            prefix = call.data.get(CONF_FILENAME_PREFIX, settings[CONF_FILENAME_PREFIX])
            prefix = "".join(char for char in str(prefix) if char.isalnum() or char in "-_")[:32] or DEFAULT_FILENAME_PREFIX
            await hass.bus.async_fire(
                EVENT_SCAN_REQUEST,
                {
                    "request_id": str(uuid4()),
                    CONF_RESOLUTION: int(resolution),
                    CONF_COLOR_MODE: color_mode,
                    CONF_FILENAME_PREFIX: prefix,
                },
            )

        hass.services.async_register(
            DOMAIN,
            "scan",
            handle_scan,
            schema=SERVICE_SCAN_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, "scan"):
            hass.services.async_remove(DOMAIN, "scan")
    return unloaded
