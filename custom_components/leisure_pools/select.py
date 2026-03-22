from homeassistant.components.select import SelectEntity

from .const import DOMAIN, PUMP_MODE_OPTIONS, PUMP_MODE_SELECT_UNIQUE_ID
from .entity import LeisurePoolEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool selects."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([PoolPumpModeSelect(api=data["api"], entry_id=config_entry.entry_id)])


class PoolPumpModeSelect(LeisurePoolEntity, SelectEntity):
    """Select entity for controlling the pool pump mode."""

    _attr_name = "Pump Mode"
    _attr_options = list(PUMP_MODE_OPTIONS)
    _attr_icon = "mdi:pump"

    def __init__(self, api, entry_id: str) -> None:
        super().__init__(api, entry_id)
        self._attr_unique_id = f"{entry_id}_{PUMP_MODE_SELECT_UNIQUE_ID}"

    @property
    def current_option(self) -> str | None:
        return self._api.get_pump_mode()

    async def async_select_option(self, option: str) -> None:
        await self._api.async_set_pump_mode(option)
