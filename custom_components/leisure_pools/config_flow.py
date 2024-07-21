import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_API_URL, CONF_USERNAME, CONF_PASSWORD

class LeisurePoolsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Leisure Pools."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LeisurePoolsOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Leisure Pools", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_API_URL): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

class LeisurePoolsOptionsFlow(config_entries.OptionsFlow):
    """Handle a options flow for Leisure Pools."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Leisure Pools", data=user_input)

        data_schema = vol.Schema({
            vol.Optional(CONF_API_URL, default=self.config_entry.data.get(CONF_API_URL)): str,
            vol.Optional(CONF_USERNAME, default=self.config_entry.data.get(CONF_USERNAME)): str,
            vol.Optional(CONF_PASSWORD, default=self.config_entry.data.get(CONF_PASSWORD)): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
