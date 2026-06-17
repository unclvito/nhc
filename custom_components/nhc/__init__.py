import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)
DOMAIN = "unclvito_nhca"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the custom components for NHC Atlantic."""
    # This forwards the setup process straight to sensor.py
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, config)
    )
    return True
