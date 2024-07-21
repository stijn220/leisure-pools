import logging

from homeassistant.helpers import discovery
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "leisure_pools"

def setup(hass: HomeAssistant, config: dict):
    """Set up the Leisure Pools component."""
    _LOGGER.info("Setting up Leisure Pools component")
    hass.helpers.discovery.load_platform('light', DOMAIN, {}, config)
    return True
