from homeassistant.components.light import ColorMode, LightEntity

from .const import DOMAIN, LIGHT_ENTITY_UNIQUE_ID
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up pool light for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PoolLight(api=data["api"], entry_id=config_entry.entry_id)])


class PoolLight(LeisurePoolEntity, LightEntity):
    """Representation of a pool light."""

    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, api, entry_id: str):
        super().__init__(api, entry_id)
        self._attr_unique_id = f"{entry_id}_{LIGHT_ENTITY_UNIQUE_ID}"

    @property
    def is_on(self):
        return self._api.is_light_on()

    async def async_turn_on(self, **kwargs):
        await self._api.turn_light_on()

    async def async_turn_off(self, **kwargs):
        await self._api.turn_light_off()
