import requests
import time
from homeassistant.helpers import discovery
from .const import DOMAIN, CONF_API_URL, CONF_USERNAME, CONF_PASSWORD, SESSION_DURATION

class LeisurePoolsAPI:
    """Class to interact with Leisure Pools API."""

    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.login_time = None
        self._login()

    def _login(self):
        """Log in to the Leisure Pools API."""
        login_url = f"{self.api_url}/cgi/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(login_url, data=payload)
        response.raise_for_status()
        self.login_time = time.time()

    def _is_session_expired(self):
        """Check if the session has expired."""
        if self.login_time is None:
            return True
        return (time.time() - self.login_time) > SESSION_DURATION

    def ensure_logged_in(self):
        """Ensure that the API session is valid."""
        if self._is_session_expired():
            self._login()

    def send_request(self, action, value):
        """Send a request to the API."""
        self.ensure_logged_in()
        write_tags_url = f"{self.api_url}/cgi/writeTags.json"
        params = {
            'n': 1,
            't1': action,
            'v1': value,
            'nocache': int(time.time() * 1000)
        }
        response = self.session.get(write_tags_url, params=params)
        response.raise_for_status()
        return response.json()

    def turn_on_lights(self):
        """Turn on the lights."""
        self.send_request('bLightsON.0', 1)
        self.send_request('bLightsON.0', 0)

    def turn_off_lights(self):
        """Turn off the lights."""
        self.send_request('nLichtKleur.-1', 0)

async def async_setup_entry(hass, entry):
    """Set up the Leisure Pools integration from a config entry."""
    api_url = entry.data[CONF_API_URL]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    api = LeisurePoolsAPI(api_url, username, password)
    hass.data[DOMAIN] = api

    # Add the light entity
    hass.async_add_job(
        discovery.async_load_platform(
            hass,
            'light',
            DOMAIN,
            {},
            entry
        )
    )

    return True
