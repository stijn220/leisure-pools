# light.py
from homeassistant.components.light import LightEntity, ColorMode
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up pool light for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([data["light"]])


class PoolLight(LightEntity):
    """Representation of a pool light."""

    def __init__(self, name: str, api):
        """Initialize the light."""
        self._api = api
        self._name = name
        self._state = False
        self._unique_id = "pool_light"

    @property
    def name(self):
        """Return the name of the light."""
        return self._name
    
    @property
    def unique_id(self):
        """Return the unique ID for this light."""
        return self._unique_id
    
    @property
    def is_on(self):
        """Return the state of the light."""
        return self._state

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self._api.turn_light_on()
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._api.turn_light_off()
        self._state = False
        self.async_write_ha_state()

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return ColorMode.ONOFF

    @property
    def supported_color_modes(self):
        """Return the supported color modes for the light."""
        return {ColorMode.ONOFF}

    @property
    def device_info(self):
        """Link this entity to the pool device."""
        return {
            "identifiers": {(DOMAIN, "pool_device")},
            "name": "Pool",
            "manufacturer": "Leisure Pools",
            "model": "Leisure Pool",
        }
