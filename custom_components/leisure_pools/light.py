import logging
import requests
import time
from homeassistant.components.light import LightEntity
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

class LeisurePoolsLight(LightEntity):
    """Representation of a Leisure Pools light."""

    def __init__(self, api_url, username, password):
        """Initialize the light."""
        self._is_on = False
        self._api_url = api_url
        self._username = username
        self._password = password
        self._login_url = f"{self._api_url}/cgi/login"
        self._write_tags_url = f"{self._api_url}/cgi/writeTags.json"
        self.session = requests.Session()
        self.login()

    def login(self):
        """Login to the Leisure Pools system."""
        login_payload = {
            "username": self._username,
            "password": self._password
        }
        try:
            response = self.session.post(self._login_url, data=login_payload)
            response.raise_for_status()
            _LOGGER.info("Login successful")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Login failed: {e}")

    def send_request(self, action, value):
        """Send request to the Leisure Pools system."""
        params = {
            'n': 1,
            't1': action,
            'v1': value,
            'nocache': int(time.time() * 1000)  # Using timestamp as nocache value
        }
        try:
            response = self.session.get(self._write_tags_url, params=params)
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
        self.send_request('bLightsON.0', 0)
        self._is_on = False
        self.schedule_update_ha_state()

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Leisure Pools light platform."""
    api_url = config[CONF_HOST]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    add_entities([LeisurePoolsLight(api_url, username, password)])
