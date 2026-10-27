# Mealie recipe printer for Home Assistant

A Home Assistant package that prints recipes from
[Mealie](https://mealie.io) on an **LX-D02** thermal receipt printer: the
recipe name, servings and time, the ingredients as a checklist and the
numbered steps.

It uses two integrations:
- Home Assistant's [Mealie integration](https://www.home-assistant.io/integrations/mealie/),
  to list and fetch recipes
- the **lxd02** receipt printer integration (the HA-LXD02 project), to print
  them

## What it adds

[`packages/mealie.yaml`](packages/mealie.yaml) contains:

| Item | What it does |
|---|---|
| `input_select.mealie_recipe` | **Mealie recipe** dropdown of recipe names |
| `script.mealie_refresh_recipes` | **Refresh Mealie recipe list**: loads up to 100 recipe names into the dropdown |
| `script.print_mealie_recipe` | **Print Mealie recipe**: prints the chosen recipe |
| automation `mealie_refresh_recipe_list` | refreshes the dropdown at startup and every hour |

## Install

1. Set up the Mealie integration and the lxd02 printer integration.
2. Enable packages in `configuration.yaml`. It must sit under `homeassistant:`;
   if that section already exists, add the `packages:` line inside it:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

3. Copy `packages/mealie.yaml` to `/config/packages/mealie.yaml`.
4. Developer tools → YAML → **Check configuration**, then restart Home
   Assistant (packages are only read at startup).
5. Run **Refresh Mealie recipe list** once (Settings → Automations & scenes →
   Scripts), or wait for the hourly refresh.

## Use

Run **Print Mealie recipe** (Scripts → ⋮ → **Run actions**) and pick:

| Field | Default | |
|---|---|---|
| Recipe | the one chosen in the Mealie recipe dropdown | which recipe |
| Ingredients | on | print the ingredient checklist |
| Steps | on | print the numbered steps; off gives a shopping list |
| Text size | normal | `small`, `normal` or `large` |

From an automation, a voice command or a dashboard button:

```yaml
action: script.print_mealie_recipe
data:
  recipe: Uunifeta-kanapasta
  steps: false     # ingredients only, as a shopping list
```

A dashboard card to pick a recipe and print it:

```yaml
type: entities
title: Recipes
entities:
  - entity: input_select.mealie_recipe
  - type: button
    name: Print recipe
    icon: mdi:printer
    action_name: Print
    tap_action:
      action: perform-action
      perform_action: script.print_mealie_recipe
  - type: button
    name: Print shopping list
    icon: mdi:cart
    action_name: Print
    tap_action:
      action: perform-action
      perform_action: script.print_mealie_recipe
      data:
        steps: false
  - type: button
    name: Refresh list
    icon: mdi:refresh
    action_name: Refresh
    tap_action:
      action: perform-action
      perform_action: script.mealie_refresh_recipes
```

A full recipe can be long (25 cm or more): use `size: small` for shorter
receipts, or `steps: false` for just the ingredients.

## Notes

- The scripts use the first Mealie server set up in Home Assistant. To pick
  another, replace the `mealie_entry` template in `print_mealie_recipe` and the
  `config_entry_id` template in `mealie_refresh_recipes` with that server's
  config entry ID.
- Recipes are found by name. If you get "Recipe not found in Mealie", the
  recipe was renamed or deleted since the last refresh: refresh the list and
  pick it again.
- When the recipe has no yield text, its servings count is printed instead
  ("4 servings"). Ingredients use Mealie's own display text when it has one.

## Development

The tests load the package into a test Home Assistant with fake
`mealie.get_recipes`, `mealie.get_recipe` and `lxd02.print` actions, shaped
like real Mealie responses (including the quirks of a real server: dates in
the data, an empty `recipe_yield` next to `recipe_servings`, notes that are the
text "None"). They check the dropdown refresh and the exact Markdown that gets
printed. They need Linux (or WSL) with Python 3.14:

```bash
pip install pytest-homeassistant-custom-component
```
```bash
pytest
```
