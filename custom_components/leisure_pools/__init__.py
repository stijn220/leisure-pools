import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import requests
import time

from .const import DOMAIN, CONF_API_URL, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]

def login(api_url, username, password):
    """Login to the Leisure Pools system."""
    session = requests.Session()
    login_payload = {
        "username": username,
        "password": password
    }
    try:
        response = session.post(f"{api_url}/cgi/login", data=login_payload)
        response.raise_for_status()
        _LOGGER.info("Login successful")
        return session
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Login failed: {e}")
        raise UpdateFailed(f"Login failed: {e}")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Leisure Pools from a config entry."""
    api_url = entry.data[CONF_API_URL]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    def update_data():
        """Fetch data from API."""
        session = login(api_url, username, password)
        return session

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Leisure Pools",
        update_method=update_data,
        update_interval=timedelta(minutes=100),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, platform))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
