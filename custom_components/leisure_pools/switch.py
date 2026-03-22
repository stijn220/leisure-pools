from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, LOCK_SWITCH_UNIQUE_ID
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool switches."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PoolCoverLockSwitch(api=data["api"], entry_id=config_entry.entry_id)])
