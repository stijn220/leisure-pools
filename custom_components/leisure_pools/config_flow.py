import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_API_URL, CONF_USERNAME, CONF_PASSWORD

class LeisurePoolsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Leisure Pools."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Leisure Pools", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_API_URL, description={"suggested_value": "http://192.168.178.252"}): str,
            vol.Required(CONF_USERNAME, description={"suggested_value": "admin"}): str,
            vol.Required(CONF_PASSWORD, description={"suggested_value": "admin"}): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description="Please provide the following information to connect to your Leisure Pools system.",
            title="Leisure Pools Configuration"
        )
