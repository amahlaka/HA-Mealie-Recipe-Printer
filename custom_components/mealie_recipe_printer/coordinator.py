"""Keeps the list of recipe names from one Mealie server."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_MEALIE_ENTRY_ID,
    DOMAIN,
    MEALIE_DOMAIN,
    PRINTER_DOMAIN,
    RECIPE_LIMIT,
    REFRESH_INTERVAL,
)
from .receipt import recipe_markdown

_LOGGER = logging.getLogger(__name__)


@dataclass
class RecipePrinterData:
    """What a config entry keeps while it is loaded."""

    coordinator: RecipeListCoordinator
    # The recipe chosen in the dropdown.
    selected: str | None = None


type RecipePrinterConfigEntry = ConfigEntry[RecipePrinterData]


class RecipeListCoordinator(DataUpdateCoordinator[list[str]]):
    """Recipe names, sorted, through the Mealie integration's actions."""

    config_entry: RecipePrinterConfigEntry

    def __init__(self, hass: HomeAssistant, entry: RecipePrinterConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=REFRESH_INTERVAL)
        self.mealie_entry_id: str = entry.data[CONF_MEALIE_ENTRY_ID]

    async def _get_recipes(self, **data: Any) -> list[dict[str, Any]]:
        result = await self.hass.services.async_call(
            MEALIE_DOMAIN, "get_recipes", {"config_entry_id": self.mealie_entry_id, **data},
            blocking=True, return_response=True,
        )
        return result["recipes"]["items"]

    async def _async_update_data(self) -> list[str]:
        try:
            recipes = await self._get_recipes(result_limit=RECIPE_LIMIT)
        except HomeAssistantError as err:
            raise UpdateFailed(f"Could not load recipes from Mealie: {err}") from err
        return sorted({recipe["name"] for recipe in recipes})

    async def async_print(self, name: str, *, ingredients: bool, steps: bool, size: str) -> None:
        """Print a recipe, found by name."""
        found = await self._get_recipes(search_terms=name, result_limit=20)
        recipe_id = next((r["recipe_id"] for r in found if r["name"] == name), None)
        if recipe_id is None:
            raise ServiceValidationError(
                f"Recipe {name!r} not found in Mealie; refresh the recipe list and pick it again"
            )
        result = await self.hass.services.async_call(
            MEALIE_DOMAIN, "get_recipe", {"config_entry_id": self.mealie_entry_id, "recipe_id": recipe_id},
            blocking=True, return_response=True,
        )
        recipe = result["recipe"]
        await self.hass.services.async_call(
            PRINTER_DOMAIN, "print",
            {"icon": "mdi:chef-hat", "title": recipe["name"],
             "text": recipe_markdown(recipe, ingredients=ingredients, steps=steps), "size": size},
            blocking=True,
        )
