from homeassistant.components.light import LightEntity
from .const import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the light platform."""
    api = hass.data[DOMAIN]
    async_add_entities([LeisurePoolsLight(api)])

class LeisurePoolsLight(LightEntity):
    """Representation of a Leisure Pools Light."""

    def __init__(self, api):
        """Initialize the light."""
        self._api = api
        self._is_on = False

    @property
    def name(self):
        """Return the name of the light."""
        return "Leisure Pools Light"

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._api.turn_on_lights()
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._api.turn_off_lights()
        self._is_on = False
        self.async_write_ha_state()
