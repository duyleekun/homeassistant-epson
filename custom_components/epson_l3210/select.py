from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import _entry_settings
from .const import COLOR_MODES, CONF_COLOR_MODE, DOMAIN
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonColorModeSelect(hass.data[DOMAIN][entry.entry_id], entry)])


class EpsonColorModeSelect(EpsonEntity, SelectEntity):
    _attr_unique_id = "epson_l3210_color_mode"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Color mode"
    _attr_options = list(COLOR_MODES)

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def current_option(self) -> str:
        return _entry_settings(self._entry)[CONF_COLOR_MODE]

    async def async_select_option(self, option: str) -> None:
        options = {**_entry_settings(self._entry), CONF_COLOR_MODE: option}
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.async_write_ha_state()
