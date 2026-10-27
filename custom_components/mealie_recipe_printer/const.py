"""Constants for the Mealie recipe printer."""
from datetime import timedelta

DOMAIN = "mealie_recipe_printer"

CONF_MEALIE_ENTRY_ID = "mealie_entry_id"

MEALIE_DOMAIN = "mealie"
PRINTER_DOMAIN = "lxd02"

# How many recipe names go into the dropdown, and how often they are reloaded.
RECIPE_LIMIT = 100
REFRESH_INTERVAL = timedelta(hours=1)

SERVICE_PRINT_RECIPE = "print_recipe"
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_RECIPE = "recipe"
ATTR_INGREDIENTS = "ingredients"
ATTR_STEPS = "steps"
ATTR_SIZE = "size"
SIZES = ["small", "normal", "large"]
