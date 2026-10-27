"""Run the package in packages/mealie.yaml against fake Mealie and lxd02 actions."""
from datetime import date
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import yaml

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

# The package's hourly time trigger leaves a timer scheduled; that is expected.
pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])

PACKAGE = Path(__file__).parent.parent / "packages" / "mealie.yaml"

# Shapes as returned by the Mealie integration (dataclasses.asdict of aiomealie models),
# with quirks seen on a real server: an empty recipe_yield next to recipe_servings,
# empty titles, and notes that are the string "None".
# Real responses contain date objects, which a script can't keep in a variable.
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


@pytest.fixture
async def package(hass: HomeAssistant):
    """Fake Mealie actions and a fake lxd02.print, then load the package."""
    # integration_entities() matches an entry title, or entities of a loaded platform;
    # nothing is loaded here, so give the entry the integration's name as title.
    entry = MockConfigEntry(domain="mealie", title="mealie")
    entry.add_to_hass(hass)
    er.async_get(hass).async_get_or_create("sensor", "mealie", "recipes", config_entry=entry)

    calls: dict[str, list] = {"get_recipes": [], "get_recipe": [], "print": []}

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

    config = yaml.safe_load(PACKAGE.read_text(encoding="utf-8"))
    for domain in ("input_select", "script", "automation"):
        assert await async_setup_component(hass, domain, {domain: config[domain]})
    await hass.async_block_till_done()
    calls["entry_id"] = entry.entry_id
    return calls


async def test_refresh_fills_dropdown(hass: HomeAssistant, package) -> None:
    await hass.services.async_call("script", "mealie_refresh_recipes", blocking=True)
    assert package["get_recipes"] == [{"config_entry_id": package["entry_id"], "result_limit": 100}]
    assert hass.states.get("input_select.mealie_recipe").attributes["options"] == ["Banana bread", "Pancakes"]


async def test_print_selected_recipe(hass: HomeAssistant, package) -> None:
    await hass.services.async_call("script", "mealie_refresh_recipes", blocking=True)
    await hass.services.async_call("input_select", "select_option",
                                   {"entity_id": "input_select.mealie_recipe", "option": "Pancakes"}, blocking=True)
    await hass.services.async_call("script", "print_mealie_recipe", blocking=True)

    assert package["get_recipe"] == [{"config_entry_id": package["entry_id"], "recipe_id": "r1"}]
    (printed,) = package["print"]
    assert printed["title"] == "Pancakes"
    assert printed["size"] == "normal"
    assert printed["text"] == (
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


async def test_print_named_recipe_without_steps(hass: HomeAssistant, package) -> None:
    await hass.services.async_call("script", "print_mealie_recipe",
                                   {"recipe": "Pancakes", "steps": False, "size": "large"}, blocking=True)
    (printed,) = package["print"]
    assert "## Ingredients" in printed["text"] and "## Steps" not in printed["text"]
    assert printed["size"] == "large"


async def test_unknown_recipe(hass: HomeAssistant, package, caplog) -> None:
    await hass.services.async_call("script", "print_mealie_recipe", {"recipe": "Soup"}, blocking=True)
    assert package["get_recipe"] == [] and package["print"] == []
    assert "Recipe not found in Mealie" in caplog.text
