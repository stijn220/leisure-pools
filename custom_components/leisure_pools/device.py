# device.py
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity import Entity
from .const import DOMAIN

class PoolDevice:
    """Representation of a Pool device."""

    def __init__(self, name: str, api, light_entity: Entity, cover_entity: Entity):
        """Initialize the device."""
        self._api = api
        self._name = name
        self._light_entity = light_entity
        self._cover_entity = cover_entity
        self._unique_id = f"pool_device"
    
    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID for this device."""
        return self._unique_id

    @property
    def device_class(self):
        """Return the device class for this device (Pool)."""
        return "pool"

    @property
    def device_type(self):
        """Return the type of the device (Light and Cover)."""
        return "Light & Cover"

    @property
    def entities(self):
        """Return the list of associated entities (light and cover)."""
        return [self._light_entity, self._cover_entity]

    def add_to_registry(self):
        """Add this device to the device registry."""
        device_entry = DeviceEntry(
            id=self._unique_id,
            name=self._name,
            identifiers={(DOMAIN, self._unique_id)},
            model="Leisure Pool",
            manufacturer="Custom Manufacturer",
            configuration_url=f"http://{self._api.host}",
        )
        return device_entry
