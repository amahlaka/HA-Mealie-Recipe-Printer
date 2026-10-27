# Mealie recipe printer for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)

A Home Assistant integration that prints recipes from
[Mealie](https://mealie.io) on an **LX-D02** thermal receipt printer: the
recipe name, servings and time, the ingredients as a checklist and the
numbered steps.

It uses two integrations:
- Home Assistant's [Mealie integration](https://www.home-assistant.io/integrations/mealie/),
  to list and fetch recipes
- the **lxd02** receipt printer integration (the HA-LXD02 project), to print
  them

## What it adds

For each Mealie server you set it up for:

| Entity / action | What it does |
|---|---|
| `select.mealie_recipe` | **Recipe** dropdown of up to 100 recipe names, refreshed every hour |
| `button.mealie_print_recipe` | **Print recipe**: prints the chosen recipe |
| `button.mealie_print_shopping_list` | **Print shopping list**: prints just its ingredients |
| `button.mealie_refresh_recipe_list` | **Refresh recipe list**: reloads the names now |
| `mealie_recipe_printer.print_recipe` | **Print recipe** action, with options (see [Use](#use)) |

(Entity IDs follow your Mealie server's name; `mealie` is the default.)

## Install

Needs Home Assistant 2026.10 or later, with the Mealie integration and the lxd02
printer integration set up.

### With HACS

1. HACS → ⋮ → **Custom repositories**, add
   `https://github.com/amahlaka/HA-Mealie-Recipe-Printer` with type
   **Integration**.
2. Search HACS for **Mealie Recipe Printer**, download it and restart Home
   Assistant.
3. Settings → Devices & services → **Add integration** → **Mealie Recipe
   Printer**. With several Mealie servers, pick the one to print from.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=amahlaka&repository=HA-Mealie-Recipe-Printer&category=integration)

### By hand

Copy `custom_components/mealie_recipe_printer` to
`/config/custom_components/mealie_recipe_printer`, restart Home Assistant, then
do step 3 above.

### Moving from the YAML package

Earlier versions were a package (`packages/mealie.yaml`). Delete that file, and
change `script.print_mealie_recipe` to `mealie_recipe_printer.print_recipe` and
`input_select.mealie_recipe` to `select.mealie_recipe` in your automations and
dashboards.

## Use

Press **Print recipe** on the device page, or run the
**Mealie Recipe Printer: Print recipe** action (Developer tools → Actions) and
pick:

| Field | Default | |
|---|---|---|
| Recipe | the one chosen in the Recipe dropdown | which recipe, by name |
| Ingredients | on | print the ingredient checklist |
| Steps | on | print the numbered steps; off gives a shopping list |
| Text size | normal | `small`, `normal` or `large` |
| Recipe printer | the only one | which Mealie server, when several are set up |

From an automation, a voice command or a dashboard button:

```yaml
action: mealie_recipe_printer.print_recipe
data:
  recipe: Uunifeta-kanapasta
  steps: false     # ingredients only, as a shopping list
```

A dashboard card to pick a recipe and print it:

```yaml
type: entities
title: Recipes
entities:
  - entity: select.mealie_recipe
  - entity: button.mealie_print_recipe
  - entity: button.mealie_print_shopping_list
  - entity: button.mealie_refresh_recipe_list
```

A full recipe can be long (25 cm or more): use `size: small` for shorter
receipts, or `steps: false` for just the ingredients.

## Notes

- Recipes are found by name. If you get "Recipe not found in Mealie", the
  recipe was renamed or deleted since the last refresh: refresh the list and
  pick it again.
- When the recipe has no yield text, its servings count is printed instead
  ("4 servings"). Ingredients use Mealie's own display text when it has one.

## Development

The tests set up the integration in a test Home Assistant with fake
`mealie.get_recipes`, `mealie.get_recipe` and `lxd02.print` actions, shaped
like real Mealie responses (including the quirks of a real server: dates in
the data, an empty `recipe_yield` next to `recipe_servings`, notes that are the
text "None"). They check the config flow, the dropdown and the exact Markdown
that gets printed. They need Linux (or WSL) with Python 3.14:

```bash
pip install pytest-homeassistant-custom-component
```
```bash
pytest
```

GitHub Actions runs the tests, HACS validation and hassfest on every push.
For HACS to offer updates, tag releases (`v1.0.0`) and keep `version` in
`manifest.json` in step.
