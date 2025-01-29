# api.py
import logging
import aiohttp
import asyncio
import time
from .const import LOGIN_URL, WRITE_TAGS_URL

_LOGGER = logging.getLogger(__name__)

class LeisurePoolAPI:
    """API client for interacting with the Leisure Pool system."""
    
    def __init__(self, host: str, username: str, password: str):
        """
        Initialize the API client.
        """
        self._host = host
        self._username = username
        self._password = password

        self._headers = {'User-Agent': 'Custom User-Agent'}
        self._timeout = aiohttp.ClientTimeout(total=30)
        self._session = None
        self._is_connected = False
        self._login_cooldown = 10
        self._last_login_attempt = 0
        _LOGGER.debug(f"LeisurePoolAPI initialized with host: {host}, username: {username}")

    async def _ensure_session(self):
        """Ensure the session is created and open."""
        if self._session is None or self._session.closed:
            _LOGGER.info("Creating a new session...")
            self._session = aiohttp.ClientSession(timeout=self._timeout, headers=self._headers)

    async def login(self) -> bool:
        """
        Log in to the Leisure Pool system.
        """
        current_time = time.time()
        if current_time - self._last_login_attempt < self._login_cooldown:
            _LOGGER.warning("Login attempt skipped to avoid frequent retries.")
            return False 
        
        await self._ensure_session()
        self._last_login_attempt = current_time
        url = LOGIN_URL.format(host=self._host)
        payload = {"username": self._username, "password": self._password}
        _LOGGER.debug(f"Logging in with URL: {url} and payload: {payload}")
        try:
            async with self._session.post(url, data=payload, headers=self._headers) as response:
                if response.status == 200:
                    cookies = response.cookies
                    if not cookies:
                        return False
                    self._session.cookie_jar.update_cookies(cookies)
                    self._is_connected = True
                    _LOGGER.info("Login successful.")
                    return True
                else:
                    _LOGGER.error(f"Login failed. Status: {response.status}, Response: {await response.text()}")
                    return False
        except Exception as e:
            _LOGGER.error(f"Error during login: {e}")
            self._is_connected = False
            return False

    async def send_request(self, action: str, value: int) -> bool:
        """
        Send a request to the Leisure Pool system.
        """
        await self._ensure_session()

        params = {
            "n": 1,
            "t1": action,
            "v1": value,
            "nocache": int(time.time() * 1000),
        }
        url = WRITE_TAGS_URL.format(host=self._host)
        _LOGGER.debug(f"Sending request to URL: {url} with params: {params}")

        try:
            async with self._session.get(url, params=params, headers=self._headers) as response:
                if response.status == 200:
                    _LOGGER.debug(f"Action '{action}' with value '{value}' was successful.")
                    return True
                elif response.status == 500:  # Session expired
                    _LOGGER.warning("Session expired. Reconnecting...")
                    self._is_connected = False
                    if await self.login():
                        _LOGGER.info("Reconnected. Retrying the request...")
                        return await self.send_request(action, value)
                else:
                    _LOGGER.error(f"Request failed. Status: {response.status}, Response: {await response.text()}")
                    return False
        except Exception as e:
            _LOGGER.error(f"Error during request to {url}: {e}")
            return False

    async def turn_light_on(self):
        """Turn on the pool light."""
        _LOGGER.info("Turning on the pool light...")
        await self.send_request("bLightsON.0", 1)
        await self.send_request("bLightsON.0", 0)
        return True

    async def turn_light_off(self):
        """Turn off the pool light."""
        _LOGGER.info("Turning off the pool light...")
        return await self.send_request("nLichtKleur.-1", 0)

    async def open_cover(self):
        """Open the pool cover."""
        _LOGGER.info("Opening the pool cover...")
        await self.send_request("bOpenCover.0", 1)
        await self.send_request("bOpenCover.0", 0)
        return True
    
    async def close_cover(self):
        """Close the pool cover."""
        _LOGGER.info("Closing the pool cover...")
        await self.send_request("bCloseCover.0", 1)
        await self.send_request("bCloseCover.0", 0)
        return True

    async def close(self):
        """Close the API session."""
        if self._session and not self._session.closed:
            _LOGGER.info("Closing the API session...")
            await self._session.close()
