# cover.py
from homeassistant.components.cover import CoverEntity
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up pool cover for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([data["cover"]])


class PoolCover(CoverEntity):
    """Representation of a pool cover."""

    def __init__(self, name, api):
        self._name = name
        self._api = api
        self._state = False
        self._unique_id = "pool_cover"
        self._attr_is_closed = None 

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name
    
    @property
    def unique_id(self):
        """Return the unique ID for this cover."""
        return self._unique_id
    
    @property
    def is_open(self):
        """Return the state of the cover (True if closed)."""
        return self._state
    
    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self._attr_is_closed

    async def async_open_cover(self, **kwargs):
        await self._api.open_cover()
        self._state = True
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        await self._api.close_cover()
        self._state = False
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "pool_device")},
            "name": "Pool",
            "manufacturer": "Custom Manufacturer",
            "model": "Leisure Pool",
        }
