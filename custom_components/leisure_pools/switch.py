from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, LOCK_SWITCH_UNIQUE_ID
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool switches."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PoolCoverLockSwitch(api=data["api"], entry_id=config_entry.entry_id)])


class PoolCoverLockSwitch(LeisurePoolEntity, SwitchEntity):
    """Switch to control the cover lock state."""

    _attr_name = "Cover Lock"
    _attr_icon = "mdi:lock"

    def __init__(self, api, entry_id: str) -> None:
        super().__init__(api, entry_id)
        self._attr_unique_id = f"{entry_id}_{LOCK_SWITCH_UNIQUE_ID}"

    @property
    def is_on(self):
        """Return True when the cover is unlocked."""
        return self._api.is_cover_unlocked()

    async def async_turn_on(self, **kwargs):
        """Unlock the cover."""
        await self._api.async_set_cover_unlocked(True)

    async def async_turn_off(self, **kwargs):
        """Lock the cover."""
        await self._api.async_set_cover_unlocked(False)
