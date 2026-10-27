"""Set up a recipe printer for one of the Mealie servers in Home Assistant."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import ConfigEntrySelector, ConfigEntrySelectorConfig

from .const import CONF_MEALIE_ENTRY_ID, DOMAIN, MEALIE_DOMAIN


class RecipePrinterConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        mealie_entries = self.hass.config_entries.async_entries(MEALIE_DOMAIN)
        if not mealie_entries:
            return self.async_abort(reason="no_mealie")
        # With one Mealie server there is nothing to ask.
        if user_input is None and len(mealie_entries) == 1:
            user_input = {CONF_MEALIE_ENTRY_ID: mealie_entries[0].entry_id}

        if user_input is not None:
            mealie_entry = self.hass.config_entries.async_get_entry(user_input[CONF_MEALIE_ENTRY_ID])
            if mealie_entry is None or mealie_entry.domain != MEALIE_DOMAIN:
                return self.async_abort(reason="no_mealie")
            await self.async_set_unique_id(mealie_entry.entry_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"{mealie_entry.title} recipe printer",
                data={CONF_MEALIE_ENTRY_ID: mealie_entry.entry_id},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MEALIE_ENTRY_ID): ConfigEntrySelector(
                    ConfigEntrySelectorConfig(integration=MEALIE_DOMAIN)
                ),
            }),
        )
