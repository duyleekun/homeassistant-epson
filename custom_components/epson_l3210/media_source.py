"""Expose scan history through Home Assistant's authenticated local-media view."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.media_source.local_source import LocalSource
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, OUTPUT_DIR


async def async_get_media_source(hass: HomeAssistant) -> EpsonMediaSource:
    return EpsonMediaSource(hass, DOMAIN, "Epson scans", {"scans": str(OUTPUT_DIR)}, "/api/epson_l3210/media")


class EpsonMediaSource(LocalSource):
    """Use HA's media authorization and MIME handling for existing scan files."""

    @callback
    def async_full_path(self, source_dir_id: str, location: str) -> Path:
        path = super().async_full_path(source_dir_id, location)
        if location and (Path(location).name != location or path.is_symlink()):
            raise ValueError("Invalid scan path")
        return path
