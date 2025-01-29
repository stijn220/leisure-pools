# __init__.py
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from .api import LeisurePoolAPI
from .light import PoolLight
from .cover import PoolCover
from .device import PoolDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Leisure Pool integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Leisure Pool from a config entry."""
    _LOGGER.info("Setting up Leisure Pool entry")

    # Extract configuration data
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    # Create and store the API client
    api = LeisurePoolAPI(host, username, password)
    if not await api.login():
        _LOGGER.error("Failed to log in to the Leisure Pool API")
        return False

    # Create the Pool Light and Pool Cover entities
    pool_light = PoolLight(name="Pool Light", api=api)
    pool_cover = PoolCover(name="Pool Cover", api=api)

    # Create the Pool device
    pool_device = PoolDevice(name="Pool", api=api, light_entity=pool_light, cover_entity=pool_cover)
    
    # Store the device and entities in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "light": pool_light,
        "cover": pool_cover,
        "device": pool_device,
    }

    # Register the device in the device registry
    device_registry = async_get(hass)
    device_registry.async_get_or_create(
        identifiers={(DOMAIN, pool_device.unique_id)},
        name=pool_device.name,
        model="Leisure Pool",
        manufacturer="Leisure Pools",
        configuration_url=f"http://{host}",
        config_entry_id=entry.entry_id,
    )

    # Forward the entry to the light and cover platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["light", "cover"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Leisure Pool entry {entry.entry_id}")

    # Remove the API client
    api = hass.data[DOMAIN].pop(entry.entry_id, None)
    if api:
        await api.close()

    # Forward the unload to platforms
    await hass.config_entries.async_forward_entry_unload(entry, "light")
    await hass.config_entries.async_forward_entry_unload(entry, "cover")

    return True
