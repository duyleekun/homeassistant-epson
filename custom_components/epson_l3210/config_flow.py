from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    CONF_COLOR_MODE,
    CONF_FILENAME_PREFIX,
    CONF_RESOLUTION,
    DEFAULT_COLOR_MODE,
    DEFAULT_FILENAME_PREFIX,
    DEFAULT_RESOLUTION,
    DOMAIN,
    RESOLUTIONS,
)


class EpsonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the local Epson L3210 scanner."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(
                title="Epson L3210 Scanner",
                data={CONF_NAME: user_input.get(CONF_NAME, "Epson L3210 Scanner")},
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional(CONF_NAME, default="Epson L3210 Scanner"): str}),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EpsonOptionsFlow()


class EpsonOptionsFlow(config_entries.OptionsFlow):
    """Edit default scan settings."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RESOLUTION, default=options.get(CONF_RESOLUTION, DEFAULT_RESOLUTION)): vol.In(RESOLUTIONS),
                    vol.Required(CONF_COLOR_MODE, default=options.get(CONF_COLOR_MODE, DEFAULT_COLOR_MODE)): vol.In(("color", "grayscale")),
                    vol.Required(CONF_FILENAME_PREFIX, default=options.get(CONF_FILENAME_PREFIX, DEFAULT_FILENAME_PREFIX)): str,
                }
            ),
        )
