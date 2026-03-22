from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass

from .const import DOMAIN
from .entity import LeisurePoolEntity
from .messages import get_alarm_message, get_banner_message


ValueFn = Callable[[Any], Any]


@dataclass(frozen=True, kw_only=True)
class LeisurePoolSensorDescription(SensorEntityDescription):
    value_fn: ValueFn
    code_tag: str | None = None


SENSOR_DESCRIPTIONS = (
    LeisurePoolSensorDescription(
        key="pool_ph",
        name="pH",
        value_fn=lambda api: _scaled_value(api.get_tag_value("nMetingpH"), 100),
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:ph",
    ),
    LeisurePoolSensorDescription(
        key="pool_redox",
        name="Redox",
        value_fn=lambda api: _coerce_int(api.get_tag_value("nMetingCl")),
        native_unit_of_measurement="mV",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:test-tube",
    ),
    LeisurePoolSensorDescription(
        key="motor_speed",
        name="Motor Speed",
        value_fn=lambda api: _scaled_value(api.get_tag_value("D160"), 100),
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        icon="mdi:engine",
    ),
    LeisurePoolSensorDescription(
        key="pool_alarm_banner",
        name="Alarm Banner",
        value_fn=lambda api: get_alarm_message(_coerce_int(api.get_tag_value("nBannerAlarmen"))),
        code_tag="nBannerAlarmen",
        icon="mdi:alert",
    ),
    LeisurePoolSensorDescription(
        key="pool_process_banner",
        name="Process Banner",
        value_fn=lambda api: get_banner_message(_coerce_int(api.get_tag_value("nBannerProces"))),
        code_tag="nBannerProces",
        icon="mdi:waves",
    ),
    LeisurePoolSensorDescription(
        key="light_state",
        name="Light State",
        value_fn=lambda api: _bool_to_state(api.is_light_on(), "on", "off"),
        device_class=SensorDeviceClass.ENUM,
        options=["on", "off"],
        icon="mdi:lightbulb",
    ),
    LeisurePoolSensorDescription(
        key="light_color",
        name="Light Color",
        value_fn=lambda api: _coerce_number(api.get_tag_value("nLichtKleur")),
        icon="mdi:palette",
    ),
    LeisurePoolSensorDescription(
        key="cover_state",
        name="Cover State",
        value_fn=lambda api: api.get_cover_status(),
        device_class=SensorDeviceClass.ENUM,
        options=["open", "closed", "partial", "locked", "unlocked", "unknown"],
        icon="mdi:garage",
    ),
    LeisurePoolSensorDescription(
        key="cover_position",
        name="Cover Position",
        value_fn=lambda api: api.get_cover_position(),
        native_unit_of_measurement="%",
        icon="mdi:garage-open",
    ),
    LeisurePoolSensorDescription(
        key="cover_unlocked",
        name="Cover Lock",
        value_fn=lambda api: _bool_to_state(_coerce_bool(api.get_tag_value("bCoverUnlocked")), "unlocked", "locked"),
        device_class=SensorDeviceClass.ENUM,
        options=["unlocked", "locked"],
        icon="mdi:lock-open-variant",
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool sensors."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]
    async_add_entities(
        [LeisurePoolSensor(api=api, entry_id=config_entry.entry_id, description=description) for description in SENSOR_DESCRIPTIONS]
    )


class LeisurePoolSensor(LeisurePoolEntity, SensorEntity):
    """Sensor backed by the live Leisure Pool SSE cache."""

    def __init__(self, api, entry_id: str, description: LeisurePoolSensorDescription) -> None:
        super().__init__(api, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_pool_{description.key}"
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_icon = description.icon

    @property
    def native_value(self):
        return self.entity_description.value_fn(self._api)

    @property
    def extra_state_attributes(self):
        code_tag = self.entity_description.code_tag
        if not code_tag:
            return None

        code = _coerce_int(self._api.get_tag_value(code_tag))
        if code is None:
            return None

        return {"code": code}


def _coerce_number(value: Any) -> int | float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _scaled_value(value: Any, divisor: int) -> float | None:
    number = _coerce_number(value)
    if number is None:
        return None
    return round(float(number) / divisor, 2)


def _coerce_int(value: Any) -> int | None:
    number = _coerce_number(value)
    if number is None:
        return None
    return int(round(float(number)))


def _coerce_bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    return bool(value)


def _bool_to_state(value: bool | None, true_state: str, false_state: str) -> str | None:
    if value is None:
        return None
    return true_state if value else false_state
