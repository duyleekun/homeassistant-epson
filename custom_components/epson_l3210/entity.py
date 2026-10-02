from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, NAME, SERIAL


class EpsonEntity(CoordinatorEntity):
    """Base entity for the local Epson L3210 device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, SERIAL)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=NAME,
        )
