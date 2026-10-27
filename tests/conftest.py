"""pytest-homeassistant-custom-component provides the hass fixture."""
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load custom_components/mealie_recipe_printer."""
    yield
