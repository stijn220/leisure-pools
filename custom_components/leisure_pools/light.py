import logging
import time
from homeassistant.components.light import LightEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_API_URL
import requests

_LOGGER = logging.getLogger(__name__)

class LeisurePoolsLight(CoordinatorEntity, LightEntity):
    """Representation of a Leisure Pools light."""

    def __init__(self, coordinator, config_entry):
        """Initialize the light."""
        super().__init__(coordinator)
        self._is_on = False
        self._api_url = config_entry.data[CONF_API_URL]
        self._session = coordinator.data
        self._write_tags_url = f"{self._api_url}/cgi/writeTags.json"

    def send_request(self, action, value):
        """Send request to the Leisure Pools system."""
        params = {
            'n': 1,
            't1': action,
            'v1': value,
            'nocache': int(time.time() * 1000)  # Using timestamp as nocache value
        }
        try:
            response = self._session.get(self._write_tags_url, params=params)
            response.raise_for_status()
            _LOGGER.info(f"Action '{action}' with value '{value}' sent successfully")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error sending request: {e}")

    @property
    def name(self):
        """Return the display name of this light."""
        return "Leisure Pools Light"

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        self.send_request('bLightsON.0', 1)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self.send_request('nLichtKleur.-1', 0)
        self._is_on = False
        self.schedule_update_ha_state()

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pools light based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([LeisurePoolsLight(coordinator, config_entry)])
