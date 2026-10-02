from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import _entry_settings
from .const import CONF_FILENAME_PREFIX, DOMAIN
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonFilenamePrefixText(hass.data[DOMAIN][entry.entry_id], entry)])


class EpsonFilenamePrefixText(EpsonEntity, TextEntity):
    _attr_unique_id = "epson_l3210_filename_prefix"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Filename prefix"
    _attr_native_min = 1
    _attr_native_max = 32
    _attr_mode = "text"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def native_value(self) -> str:
        return _entry_settings(self._entry)[CONF_FILENAME_PREFIX]

    async def async_set_value(self, value: str) -> None:
        prefix = "".join(char for char in value if char.isalnum() or char in "-_")[:32] or "scan"
        options = {**_entry_settings(self._entry), CONF_FILENAME_PREFIX: prefix}
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.async_write_ha_state()
