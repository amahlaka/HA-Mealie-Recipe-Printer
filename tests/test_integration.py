"""Run the integration against fake Mealie and lxd02 actions."""
from datetime import date

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError

from custom_components.mealie_recipe_printer.const import CONF_MEALIE_ENTRY_ID, DOMAIN

# Shapes as returned by the Mealie integration (dataclasses.asdict of aiomealie models),
# with quirks seen on a real server: an empty recipe_yield next to recipe_servings,
# empty titles, and notes that are the string "None".
RECIPES = [
    {"recipe_id": "r1", "name": "Pancakes", "slug": "pancakes", "date_added": date(2026, 9, 4)},
    {"recipe_id": "r2", "name": "Banana bread", "slug": "banana-bread", "date_added": date(2026, 9, 5)},
]
RECIPE = {
    "recipe_id": "r1", "name": "Pancakes", "slug": "pancakes",
    "description": "Fluffy and quick. ", "recipe_yield": "", "recipe_servings": 4,
    "total_time": "25 min", "prep_time": "10 min", "perform_time": None,
    "ingredients": [
        {"title": "Batter", "display": "2 cups flour", "quantity": 2.0, "note": "",
         "unit": {"name": "cup"}, "food": {"name": "flour"}},
        {"title": "", "display": "", "quantity": 1.5, "note": "None",
         "unit": {"name": "cup"}, "food": {"name": "milk"}},
        {"title": None, "display": None, "quantity": None, "note": "a pinch of salt",
         "unit": None, "food": None},
    ],
    "instructions": [
        {"title": None, "text": "Mix the **dry** ingredients.\n"},
        {"title": "Cooking", "text": "Fry until golden."},
    ],
}
PANCAKES = (
    "4 servings · Total 25 min · Prep 10 min\n"
    "\n"
    "## Ingredients\n"
    "\n"
    "**Batter**\n"
    "- [ ] 2 cups flour\n"
    "- [ ] 1.5 cup milk\n"
    "- [ ] a pinch of salt\n"
    "\n"
    "## Steps\n"
    "\n"
    "**1.** Mix the **dry** ingredients.\n"
    "\n"
    "### Cooking\n"
    "\n"
    "**2.** Fry until golden."
)


@pytest.fixture
async def mealie(hass: HomeAssistant):
    """A Mealie config entry, fake Mealie actions and a fake lxd02.print."""
    entry = MockConfigEntry(domain="mealie", title="Mealie")
    entry.add_to_hass(hass)
    calls: dict[str, list] = {"get_recipes": [], "get_recipe": [], "print": [], "entry_id": entry.entry_id}

    async def get_recipes(call: ServiceCall):
        calls["get_recipes"].append(dict(call.data))
        term = call.data.get("search_terms", "").lower()
        return {"recipes": {"items": [r for r in RECIPES if term in r["name"].lower()]}}

    async def get_recipe(call: ServiceCall):
        calls["get_recipe"].append(dict(call.data))
        return {"recipe": RECIPE}

    async def print_receipt(call: ServiceCall):
        calls["print"].append(dict(call.data))

    hass.services.async_register("mealie", "get_recipes", get_recipes, supports_response=SupportsResponse.ONLY)
    hass.services.async_register("mealie", "get_recipe", get_recipe, supports_response=SupportsResponse.ONLY)
    hass.services.async_register("lxd02", "print", print_receipt)
    return calls


@pytest.fixture
async def printer(hass: HomeAssistant, mealie):
    """The recipe printer set up for the Mealie entry."""
    entry = MockConfigEntry(domain=DOMAIN, title="Mealie", data={CONF_MEALIE_ENTRY_ID: mealie["entry_id"]})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    return mealie


async def test_config_flow_uses_only_mealie_server(hass: HomeAssistant, mealie) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_MEALIE_ENTRY_ID: mealie["entry_id"]}

    again = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert again["type"] is FlowResultType.ABORT and again["reason"] == "already_configured"


async def test_config_flow_needs_mealie(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "no_mealie"


async def test_dropdown_lists_recipes(hass: HomeAssistant, printer) -> None:
    assert printer["get_recipes"] == [{"config_entry_id": printer["entry_id"], "result_limit": 100}]
    assert hass.states.get("select.mealie_recipe").attributes["options"] == ["Banana bread", "Pancakes"]

    await hass.services.async_call("button", "press", {"entity_id": "button.mealie_refresh_recipe_list"},
                                   blocking=True)
    assert len(printer["get_recipes"]) == 2


async def test_print_selected_recipe(hass: HomeAssistant, printer) -> None:
    await hass.services.async_call("select", "select_option",
                                   {"entity_id": "select.mealie_recipe", "option": "Pancakes"}, blocking=True)
    await hass.services.async_call(DOMAIN, "print_recipe", blocking=True)

    assert printer["get_recipe"] == [{"config_entry_id": printer["entry_id"], "recipe_id": "r1"}]
    (printed,) = printer["print"]
    assert printed == {"icon": "mdi:chef-hat", "title": "Pancakes", "text": PANCAKES, "size": "normal"}


async def test_shopping_list_button(hass: HomeAssistant, printer) -> None:
    await hass.services.async_call("select", "select_option",
                                   {"entity_id": "select.mealie_recipe", "option": "Pancakes"}, blocking=True)
    await hass.services.async_call("button", "press", {"entity_id": "button.mealie_print_shopping_list"},
                                   blocking=True)
    (printed,) = printer["print"]
    assert "## Ingredients" in printed["text"] and "## Steps" not in printed["text"]


async def test_print_named_recipe_without_steps(hass: HomeAssistant, printer) -> None:
    await hass.services.async_call(DOMAIN, "print_recipe",
                                   {"recipe": "Pancakes", "steps": False, "size": "large"}, blocking=True)
    (printed,) = printer["print"]
    assert "## Ingredients" in printed["text"] and "## Steps" not in printed["text"]
    assert printed["size"] == "large"


async def test_unknown_recipe(hass: HomeAssistant, printer) -> None:
    with pytest.raises(ServiceValidationError, match="not found in Mealie"):
        await hass.services.async_call(DOMAIN, "print_recipe", {"recipe": "Soup"}, blocking=True)
    assert printer["get_recipe"] == [] and printer["print"] == []


async def test_nothing_chosen(hass: HomeAssistant, printer) -> None:
    with pytest.raises(ServiceValidationError, match="No recipe chosen"):
        await hass.services.async_call(DOMAIN, "print_recipe", blocking=True)
