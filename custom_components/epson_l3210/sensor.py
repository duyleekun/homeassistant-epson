from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonLastScanSensor(hass.data[DOMAIN][entry.entry_id])])


class EpsonLastScanSensor(EpsonEntity, SensorEntity):
    _attr_unique_id = "epson_l3210_last_scan"
    _attr_name = "Last scan"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    @property
    def native_value(self):
        scan = self.coordinator.data.get("last_scan")
        if not scan:
            return None
        completed_at = scan.get("completed_at")
        if isinstance(completed_at, (int, float)):
            return datetime.fromtimestamp(completed_at, tz=timezone.utc)
        if isinstance(completed_at, str):
            try:
                return datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @property
    def extra_state_attributes(self):
        scan = self.coordinator.data.get("last_scan") or {}
        return {
            key: scan[key]
            for key in ("filename", "source", "resolution", "color_mode", "size", "relative_path")
            if key in scan
        }
