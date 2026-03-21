import logging

from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from .api import LeisurePoolAPI

_LOGGER = logging.getLogger(__name__)


class LeisurePoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Leisure Pool."""

    async def async_step_user(self, user_input=None):
        """Handle the user step for Leisure Pool integration."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            api = LeisurePoolAPI(host, username, password)
            login_success = await api.login()
            await api.close()

            if login_success:
                return self.async_create_entry(title=f"Leisure Pool ({host})", data=user_input)
            else:
                errors["base"] = "login_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

