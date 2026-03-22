from homeassistant.components.button import ButtonEntity

from .const import DOMAIN, LIGHT_COLOR_BUTTON_UNIQUE_ID
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool buttons for a config entry."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([LightNextColorButton(api=data["api"], entry_id=config_entry.entry_id)])


class LightNextColorButton(LeisurePoolEntity, ButtonEntity):
    """Button that advances the pool light to the next color."""

    _attr_name = "Next Light Color"
    _attr_icon = "mdi:palette"

    def __init__(self, api, entry_id: str) -> None:
        super().__init__(api, entry_id)
        self._attr_unique_id = f"{entry_id}_{LIGHT_COLOR_BUTTON_UNIQUE_ID}"

    async def async_press(self) -> None:
        await self._api.cycle_light_color()
