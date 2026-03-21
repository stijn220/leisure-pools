from homeassistant.components.cover import CoverEntity, CoverEntityFeature

from .const import COVER_ENTITY_UNIQUE_ID, DOMAIN
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up pool cover for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PoolCover(api=data["api"], entry_id=config_entry.entry_id)])


class PoolCover(LeisurePoolEntity, CoverEntity):
    """Representation of the pool cover."""

    _attr_name = "Cover"
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, api, entry_id: str):
        super().__init__(api, entry_id)
        self._attr_unique_id = f"{entry_id}_{COVER_ENTITY_UNIQUE_ID}"

    @property
    def current_cover_position(self):
        return self._api.get_cover_position()

    @property
    def is_closed(self):
        return self._api.is_cover_closed()

    async def async_open_cover(self, **kwargs):
        await self._api.open_cover()

    async def async_close_cover(self, **kwargs):
        await self._api.close_cover()
