from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonScanButton(hass.data[DOMAIN][entry.entry_id])])


class EpsonScanButton(EpsonEntity, ButtonEntity):
    _attr_unique_id = "epson_l3210_scan"
    _attr_name = "Scan"
    _attr_icon = "mdi:scanner"

    async def async_press(self) -> None:
        await self.hass.services.async_call(DOMAIN, "scan", {}, blocking=True)
