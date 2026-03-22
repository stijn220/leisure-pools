import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get

from .api import LeisurePoolAPI
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light", "cover", "sensor", "binary_sensor", "switch", "button", "select"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Leisure Pool integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Leisure Pool from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    api = LeisurePoolAPI(host, username, password)
    if not await api.async_setup():
        _LOGGER.error("Failed to initialize Leisure Pool API")
        await api.close()
        return False

    hass.data[DOMAIN][entry.entry_id] = {"api": api}

    device_registry = async_get(hass)
    device_registry.async_get_or_create(
        identifiers={(DOMAIN, f"pool_device_{entry.entry_id}")},
        name="Pool",
        model="Leisure Pool",
        manufacturer="Leisure Pools",
        configuration_url=f"http://{host}",
        config_entry_id=entry.entry_id,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data:
            await entry_data["api"].close()
    return unload_ok
