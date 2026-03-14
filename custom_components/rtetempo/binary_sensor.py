"""Binary sensors for RTE Tempo integration."""
from __future__ import annotations

import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    FRANCE_TZ,
    HOUR_OF_CHANGE,
    OFF_PEAK_START,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Modern (thru config entry) binary sensors setup."""
    sensors: list[BinarySensorEntity] = [
        OffPeakHours(config_entry.entry_id),
    ]
    async_add_entities(sensors, True)


class OffPeakHours(BinarySensorEntity):
    """Tempo off-peak slot helper."""

    _attr_has_entity_name = True
    _attr_name = "Heures Creuses"
    _attr_should_poll = True
    _attr_icon = "mdi:cash-clock"

    def __init__(self, config_id: str) -> None:
        self._attr_unique_id = f"{DOMAIN}_{config_id}_off_peak"
        self._config_id = config_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @callback
    def update(self) -> None:
        localized_now = datetime.datetime.now(tz=FRANCE_TZ)
        self._attr_is_on = localized_now.hour >= OFF_PEAK_START or localized_now.hour < HOUR_OF_CHANGE
