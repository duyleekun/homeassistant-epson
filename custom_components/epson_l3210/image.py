from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OUTPUT_DIR
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonLatestScanImage(hass.data[DOMAIN][entry.entry_id])])


class EpsonLatestScanImage(EpsonEntity, ImageEntity):
    _attr_unique_id = "epson_l3210_latest_scan"
    _attr_name = "Latest scan"
    _attr_content_type = "image/jpeg"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._last_updated = None

    @property
    def image_last_updated(self):
        scan = self.coordinator.data.get("last_scan")
        if not scan:
            return None
        value = scan.get("completed_at")
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data.get("last_scan"))

    async def async_image(self) -> bytes | None:
        scan = self.coordinator.data.get("last_scan")
        if not scan:
            return None
        path = OUTPUT_DIR / str(scan.get("filename", ""))
        if path.parent != OUTPUT_DIR or not path.is_file():
            return None
        return await self.hass.async_add_executor_job(path.read_bytes)
