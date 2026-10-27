"""Turn a Mealie recipe into the Markdown that lxd02.print formats."""
from typing import Any


def _number(value: float) -> str:
    """2.0 -> "2", 1.5 -> "1.5"."""
    return "%g" % value


def _ingredient(item: dict[str, Any]) -> str:
    """Mealie's display text, or the text built from the ingredient's parts."""
    if item.get("display"):
        return item["display"]
    unit = item.get("unit") or {}
    food = item.get("food") or {}
    # A real server sends the note "None" for no note.
    note = item.get("note") if item.get("note") != "None" else ""
    parts = [_number(item["quantity"]) if item.get("quantity") else "",
             unit.get("name"), food.get("name"), note]
    return " ".join(part for part in parts if part)


def recipe_markdown(recipe: dict[str, Any], *, ingredients: bool = True, steps: bool = True) -> str:
    """Servings and times, the ingredients as a checklist and the numbered steps."""
    servings = f"{_number(recipe['recipe_servings'])} servings" if recipe.get("recipe_servings") else ""
    meta = [recipe.get("recipe_yield") or servings,
            f"Total {recipe['total_time']}" if recipe.get("total_time") else "",
            f"Prep {recipe['prep_time']}" if recipe.get("prep_time") else "",
            f"Cook {recipe['perform_time']}" if recipe.get("perform_time") else ""]
    text = " · ".join(part for part in meta if part)

    if ingredients and recipe.get("ingredients"):
        text += "\n\n## Ingredients"
        for item in recipe["ingredients"]:
            if item.get("title"):
                text += f"\n\n**{item['title']}**"
            text += f"\n- [ ] {_ingredient(item)}"

    if steps and recipe.get("instructions"):
        text += "\n\n## Steps"
        for number, step in enumerate(recipe["instructions"], 1):
            if step.get("title"):
                text += f"\n\n### {step['title']}"
            text += f"\n\n**{number}.** {(step.get('text') or '').strip()}"

    return text.lstrip("\n")
