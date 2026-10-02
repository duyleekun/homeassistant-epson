from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonConnectedSensor(hass.data["epson_l3210"][entry.entry_id])])


class EpsonConnectedSensor(EpsonEntity, BinarySensorEntity):
    _attr_unique_id = "epson_l3210_connected"
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("connected")

    @property
    def available(self) -> bool:
        return bool(self.coordinator.data.get("status_available"))
