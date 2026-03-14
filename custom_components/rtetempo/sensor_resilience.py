"""Resilience diagnostic sensors for Tempo handling."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DEVICE_MANUFACTURER, DEVICE_MODEL, DEVICE_NAME, DOMAIN
from .resilience_service import TempoResilienceService


def _display_color(value: str) -> str:
    mapping = {
        "blue": "Bleu",
        "white": "Blanc",
        "red": "Rouge",
        "unknown": "Inconnu",
    }
    return mapping.get(value, "Inconnu")


class ResilienceTodayResolvedSensor(SensorEntity):
    """Resolved color for today."""

    _attr_has_entity_name = True
    _attr_name = "Couleur résolue aujourd'hui"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:shield-check"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_today_resolved"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = _display_color(snapshot.today.color)
        self._attr_extra_state_attributes = {
            "source": snapshot.today.source,
            "degraded": snapshot.today.degraded,
            "fallback_reason": snapshot.today.fallback_reason,
            "consistent": snapshot.today.consistent,
            "compared_with": snapshot.today.compared_with,
        }


class ResilienceTodaySourceSensor(SensorEntity):
    """Resolved source for today."""

    _attr_has_entity_name = True
    _attr_name = "Source résolue aujourd'hui"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["rte", "local", "default", "forecast"]
    _attr_icon = "mdi:source-branch"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_today_source"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.today.source


class ResilienceTomorrowResolvedSensor(SensorEntity):
    """Resolved color for tomorrow."""

    _attr_has_entity_name = True
    _attr_name = "Couleur résolue demain"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tomorrow_resolved"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = _display_color(snapshot.tomorrow.color)
        self._attr_extra_state_attributes = {
            "source": snapshot.tomorrow.source,
            "degraded": snapshot.tomorrow.degraded,
            "fallback_reason": snapshot.tomorrow.fallback_reason,
            "consistent": snapshot.tomorrow.consistent,
            "compared_with": snapshot.tomorrow.compared_with,
        }


class ResilienceTomorrowSourceSensor(SensorEntity):
    """Resolved source for tomorrow."""

    _attr_has_entity_name = True
    _attr_name = "Source résolue demain"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["rte", "local", "default", "forecast"]
    _attr_icon = "mdi:source-merge"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tomorrow_source"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.tomorrow.source
