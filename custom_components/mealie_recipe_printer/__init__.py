"""Print Mealie recipes on the LX-D02 receipt printer."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_INGREDIENTS,
    ATTR_RECIPE,
    ATTR_SIZE,
    ATTR_STEPS,
    DOMAIN,
    SERVICE_PRINT_RECIPE,
    SIZES,
)
from .coordinator import RecipeListCoordinator, RecipePrinterConfigEntry, RecipePrinterData

PLATFORMS = [Platform.BUTTON, Platform.SELECT]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PRINT_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    vol.Optional(ATTR_RECIPE): cv.string,
    vol.Optional(ATTR_INGREDIENTS, default=True): cv.boolean,
    vol.Optional(ATTR_STEPS, default=True): cv.boolean,
    vol.Optional(ATTR_SIZE, default="normal"): vol.In(SIZES),
})


def _loaded_entry(hass: HomeAssistant, entry_id: str | None) -> RecipePrinterConfigEntry:
    """The entry named in the call, or the only one there is."""
    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]
    if entry_id:
        entries = [e for e in entries if e.entry_id == entry_id]
    if not entries:
        raise ServiceValidationError("Mealie recipe printer is not set up")
    if len(entries) > 1:
        raise ServiceValidationError("Several Mealie recipe printers are set up; choose one")
    return entries[0]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the print_recipe action."""

    async def print_recipe(call: ServiceCall) -> None:
        entry = _loaded_entry(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        name = call.data.get(ATTR_RECIPE) or entry.runtime_data.selected
        if not name:
            raise ServiceValidationError("No recipe chosen")
        await entry.runtime_data.coordinator.async_print(
            name, ingredients=call.data[ATTR_INGREDIENTS], steps=call.data[ATTR_STEPS], size=call.data[ATTR_SIZE]
        )

    hass.services.async_register(DOMAIN, SERVICE_PRINT_RECIPE, print_recipe, schema=PRINT_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RecipePrinterConfigEntry) -> bool:
    coordinator = RecipeListCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = RecipePrinterData(coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RecipePrinterConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
