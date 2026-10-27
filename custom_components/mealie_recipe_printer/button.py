"""Buttons to print the chosen recipe and to reload the recipe list."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import RecipePrinterConfigEntry
from .entity import RecipePrinterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RecipePrinterConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([
        PrintButton(entry, "print_recipe", "mdi:printer", steps=True),
        PrintButton(entry, "print_shopping_list", "mdi:cart", steps=False),
        RefreshButton(entry),
    ])


class PrintButton(RecipePrinterEntity, ButtonEntity):
    """Prints the recipe chosen in the dropdown, in normal size."""

    def __init__(self, entry: RecipePrinterConfigEntry, key: str, icon: str, *, steps: bool) -> None:
        super().__init__(entry.runtime_data.coordinator, key)
        self._data = entry.runtime_data
        self._attr_icon = icon
        self._steps = steps

    async def async_press(self) -> None:
        if not self._data.selected:
            raise ServiceValidationError("No recipe chosen")
        await self.coordinator.async_print(self._data.selected, ingredients=True, steps=self._steps, size="normal")


class RefreshButton(RecipePrinterEntity, ButtonEntity):
    """Reloads the recipe names from Mealie now instead of at the next hourly refresh."""

    _attr_icon = "mdi:refresh"

    def __init__(self, entry: RecipePrinterConfigEntry) -> None:
        super().__init__(entry.runtime_data.coordinator, "refresh_recipes")

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
