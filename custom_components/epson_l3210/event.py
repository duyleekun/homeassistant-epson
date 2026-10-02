from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import EpsonEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([EpsonActivityEvent(hass.data[DOMAIN][entry.entry_id])])


class EpsonActivityEvent(EpsonEntity, EventEntity):
    _attr_unique_id = "epson_l3210_activity"
    _attr_name = "Activity"
    _attr_icon = "mdi:scanner"
    _attr_event_types = ["button_pressed", "scan_completed", "scan_failed"]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._last_sequence = 0
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_listener = self.coordinator.add_listener(self._async_activity_changed)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
        await super().async_will_remove_from_hass()

    @callback
    def _async_activity_changed(self) -> None:
        activity = self.coordinator.data.get("activity")
        sequence = self.coordinator.data.get("activity_sequence", 0)
        if not activity or sequence <= self._last_sequence:
            return
        self._last_sequence = sequence
        event_type = activity.get("type")
        if event_type in self._attr_event_types:
            self._trigger_event(event_type, {key: value for key, value in activity.items() if key != "type"})
            self.async_write_ha_state()
