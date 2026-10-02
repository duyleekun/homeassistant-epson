from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import _entry_settings
from .const import CONF_RESOLUTION, DOMAIN, RESOLUTIONS
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonResolutionNumber(hass.data[DOMAIN][entry.entry_id], entry)])


class EpsonResolutionNumber(EpsonEntity, NumberEntity):
    _attr_unique_id = "epson_l3210_resolution"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "Resolution"
    _attr_native_min_value = min(RESOLUTIONS)
    _attr_native_max_value = max(RESOLUTIONS)
    _attr_native_step = 100
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "dpi"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def native_value(self) -> float:
        return _entry_settings(self._entry)[CONF_RESOLUTION]

    async def async_set_native_value(self, value: float) -> None:
        resolution = int(value)
        if resolution not in (100, 200, 300):
            raise ValueError("Resolution must be 100, 200, or 300 dpi")
        options = {**_entry_settings(self._entry), CONF_RESOLUTION: int(value)}
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        self.async_write_ha_state()
