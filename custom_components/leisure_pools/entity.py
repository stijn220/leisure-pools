from __future__ import annotations

from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class LeisurePoolEntity(Entity):
    """Shared base entity for all Leisure Pool entities."""

    _attr_has_entity_name = True

    def __init__(self, api, entry_id: str) -> None:
        self._api = api
        self._entry_id = entry_id
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        self._remove_listener = self._api.add_listener(self._handle_api_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def _handle_api_update(self) -> None:
        self.async_write_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"pool_device_{self._entry_id}")},
            "name": "Pool",
            "manufacturer": "Leisure Pools",
            "model": "Leisure Pool Controller",
        }
