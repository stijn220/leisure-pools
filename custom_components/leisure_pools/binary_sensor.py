from __future__ import annotations

import time

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN
from .entity import LeisurePoolEntity
from .messages import ALARM_MESSAGES_NL, BANNER_MESSAGES_NL

ACTIVE_HOLD_SECONDS = 60.0


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Leisure Pool banner binary sensors."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    api = data["api"]

    entities = []
    for code, message in sorted(ALARM_MESSAGES_NL.items()):
        if _is_spare_message(message):
            continue
        entities.append(
            LeisurePoolBannerBinarySensor(
                api=api,
                entry_id=config_entry.entry_id,
                key=f"alarm_{code}",
                name=_entity_name_from_message(message, fallback=f"Alarm {code}"),
                code=code,
                message=message,
                tag_name="nBannerAlarmen",
                icon="mdi:alert",
            )
        )
    for code, message in sorted(BANNER_MESSAGES_NL.items()):
        if _is_spare_message(message):
            continue
        entities.append(
            LeisurePoolBannerBinarySensor(
                api=api,
                entry_id=config_entry.entry_id,
                key=f"process_banner_{code}",
                name=_entity_name_from_message(message, fallback=f"Process Banner {code}"),
                code=code,
                message=message,
                tag_name="nBannerProces",
                icon="mdi:waves",
            )
        )

    async_add_entities(entities)


class LeisurePoolBannerBinarySensor(LeisurePoolEntity, BinarySensorEntity):
    """Binary sensor that turns on when a specific banner code is active."""

    def __init__(
        self,
        api,
        entry_id: str,
        key: str,
        name: str,
        code: int,
        message: str,
        tag_name: str,
        icon: str,
    ) -> None:
        super().__init__(api, entry_id)
        self._code = code
        self._message = message
        self._tag_name = tag_name
        self._last_seen_monotonic: float | None = None
        self._cancel_expiry = None
        self._attr_unique_id = f"{entry_id}_pool_{key}"
        self._attr_name = name
        self._attr_icon = icon

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh_seen_state()
        self._schedule_expiry()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_scheduled_expiry()
        await super().async_will_remove_from_hass()

    @property
    def is_on(self) -> bool:
        if self._current_code == self._code:
            return True
        if self._last_seen_monotonic is None:
            return False
        return (time.monotonic() - self._last_seen_monotonic) < ACTIVE_HOLD_SECONDS

    @property
    def extra_state_attributes(self):
        return {
            "code": self._code,
            "message": self._message,
            "source_tag": self._tag_name,
            "active_code": self._current_code,
            "latched_for_seconds": ACTIVE_HOLD_SECONDS,
        }

    @property
    def _current_code(self) -> int | None:
        value = self._api.get_tag_value(self._tag_name)
        if value in (None, ""):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _handle_api_update(self) -> None:
        previous_state = self.is_on
        self._refresh_seen_state()
        self._schedule_expiry()
        if self.is_on != previous_state or self._current_code == self._code:
            self.async_write_ha_state()

    def _refresh_seen_state(self) -> None:
        if self._current_code == self._code:
            self._last_seen_monotonic = time.monotonic()

    def _schedule_expiry(self) -> None:
        self._cancel_scheduled_expiry()
        if self._last_seen_monotonic is None or self.hass is None:
            return

        remaining = ACTIVE_HOLD_SECONDS - (time.monotonic() - self._last_seen_monotonic)
        if remaining <= 0:
            return

        self._cancel_expiry = async_call_later(self.hass, remaining, self._expire_latched_state)

    def _expire_latched_state(self, _now) -> None:
        self._cancel_expiry = None
        if self._current_code == self._code:
            self._last_seen_monotonic = time.monotonic()
            self._schedule_expiry()
            self.async_write_ha_state()
            return

        self.async_write_ha_state()

    def _cancel_scheduled_expiry(self) -> None:
        if self._cancel_expiry is not None:
            self._cancel_expiry()
            self._cancel_expiry = None


def _entity_name_from_message(message: str, fallback: str) -> str:
    cleaned = " ".join(message.replace("\n", " ").split())
    if "|" in cleaned:
        _, _, cleaned = cleaned.partition("|")
        cleaned = cleaned.strip()
    return cleaned or fallback


def _is_spare_message(message: str) -> bool:
    return "SPARE" in message.upper()
