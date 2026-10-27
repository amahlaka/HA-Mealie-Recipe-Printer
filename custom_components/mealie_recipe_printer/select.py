"""The recipe dropdown."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import RecipePrinterConfigEntry
from .entity import RecipePrinterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RecipePrinterConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([RecipeSelect(entry)])


class RecipeSelect(RecipePrinterEntity, SelectEntity, RestoreEntity):
    """Recipe names from Mealie; the chosen one is what gets printed."""

    _attr_icon = "mdi:chef-hat"

    def __init__(self, entry: RecipePrinterConfigEntry) -> None:
        super().__init__(entry.runtime_data.coordinator, "recipe")
        self._data = entry.runtime_data

    @property
    def options(self) -> list[str]:
        return self.coordinator.data or []

    @property
    def current_option(self) -> str | None:
        return self._data.selected if self._data.selected in self.options else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (state := await self.async_get_last_state()) and state.state in self.options:
            self._data.selected = state.state

    async def async_select_option(self, option: str) -> None:
        self._data.selected = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        # Forget a recipe that was renamed or deleted.
        if self._data.selected not in self.options:
            self._data.selected = None
        super()._handle_coordinator_update()
