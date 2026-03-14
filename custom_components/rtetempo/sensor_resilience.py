"""Resilience diagnostic sensors for Tempo handling."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DEVICE_MANUFACTURER, DEVICE_MODEL, DEVICE_NAME, DOMAIN
from .resilience_service import TempoResilienceService


SOURCE_OPTIONS = ["rte", "local", "default", "forecast", "unknown"]
MODE_OPTIONS = ["auto", "web", "local", "default", "compare"]
CONSISTENCY_OPTIONS = ["consistent", "inconsistent", "partial", "unknown"]


def _display_color(value: str) -> str:
    mapping = {
        "blue": "Bleu",
        "white": "Blanc",
        "red": "Rouge",
        "unknown": "Inconnu",
    }
    return mapping.get(value, "Inconnu")


class _BaseResilienceSensor(SensorEntity):
    """Shared helpers for resilience entities."""

    _attr_has_entity_name = True

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    def _base_attributes(self, snapshot):
        return {
            "configured_mode": snapshot.configured_source_mode,
            "effective_mode": snapshot.effective_source_mode,
            "runtime_override_mode": snapshot.runtime_source_mode,
            "local_today_entity": snapshot.local_today_entity,
            "local_tomorrow_entity": snapshot.local_tomorrow_entity,
            "generated_at": snapshot.generated_at.isoformat(),
        }


class ResilienceTodayResolvedSensor(_BaseResilienceSensor):
    """Resolved color for today."""

    _attr_name = "Couleur résolue aujourd'hui"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:shield-check"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_today_resolved"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = _display_color(snapshot.today.color)
        attrs = self._base_attributes(snapshot)
        attrs.update(
            {
                "source": snapshot.today.source,
                "degraded": snapshot.today.degraded,
                "fallback_reason": snapshot.today.fallback_reason,
                "consistent": snapshot.today.consistent,
                "compared_with": snapshot.today.compared_with,
                "rte_color": _display_color(snapshot.today_rte.color) if snapshot.today_rte else None,
                "rte_available": snapshot.today_rte.available if snapshot.today_rte else False,
                "local_color": _display_color(snapshot.today_local.color) if snapshot.today_local else None,
                "local_available": snapshot.today_local.available if snapshot.today_local else False,
            }
        )
        self._attr_extra_state_attributes = attrs


class ResilienceTodaySourceSensor(_BaseResilienceSensor):
    """Resolved source for today."""

    _attr_name = "Source résolue aujourd'hui"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_OPTIONS
    _attr_icon = "mdi:source-branch"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_today_source"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.today.source
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class ResilienceTomorrowResolvedSensor(_BaseResilienceSensor):
    """Resolved color for tomorrow."""

    _attr_name = "Couleur résolue demain"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tomorrow_resolved"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = _display_color(snapshot.tomorrow.color)
        attrs = self._base_attributes(snapshot)
        attrs.update(
            {
                "source": snapshot.tomorrow.source,
                "degraded": snapshot.tomorrow.degraded,
                "fallback_reason": snapshot.tomorrow.fallback_reason,
                "consistent": snapshot.tomorrow.consistent,
                "compared_with": snapshot.tomorrow.compared_with,
                "rte_color": _display_color(snapshot.tomorrow_rte.color) if snapshot.tomorrow_rte else None,
                "rte_available": snapshot.tomorrow_rte.available if snapshot.tomorrow_rte else False,
                "local_color": _display_color(snapshot.tomorrow_local.color) if snapshot.tomorrow_local else None,
                "local_available": snapshot.tomorrow_local.available if snapshot.tomorrow_local else False,
            }
        )
        self._attr_extra_state_attributes = attrs


class ResilienceTomorrowSourceSensor(_BaseResilienceSensor):
    """Resolved source for tomorrow."""

    _attr_name = "Source résolue demain"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_OPTIONS
    _attr_icon = "mdi:source-merge"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tomorrow_source"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.tomorrow.source
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class ResilienceModeSensor(_BaseResilienceSensor):
    """Current active mode used by the resolver."""

    _attr_name = "Mode source Tempo"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = MODE_OPTIONS
    _attr_icon = "mdi:tune-variant"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_resolver_mode"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.effective_source_mode
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class ResilienceConsistencySensor(_BaseResilienceSensor):
    """Consistency state between RTE and local sources."""

    _attr_name = "Cohérence Tempo"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = CONSISTENCY_OPTIONS
    _attr_icon = "mdi:compare"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tempo_consistency"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True

        today_consistent = (
            snapshot.today_rte is not None
            and snapshot.today_local is not None
            and snapshot.today_rte.available
            and snapshot.today_local.available
            and snapshot.today_rte.color == snapshot.today_local.color
        )
        tomorrow_consistent = (
            snapshot.tomorrow_rte is not None
            and snapshot.tomorrow_local is not None
            and snapshot.tomorrow_rte.available
            and snapshot.tomorrow_local.available
            and snapshot.tomorrow_rte.color == snapshot.tomorrow_local.color
        )

        comparable_today = bool(
            snapshot.today_rte is not None
            and snapshot.today_local is not None
            and snapshot.today_rte.available
            and snapshot.today_local.available
        )
        comparable_tomorrow = bool(
            snapshot.tomorrow_rte is not None
            and snapshot.tomorrow_local is not None
            and snapshot.tomorrow_rte.available
            and snapshot.tomorrow_local.available
        )

        if comparable_today and comparable_tomorrow:
            state = "consistent" if (today_consistent and tomorrow_consistent) else "inconsistent"
        elif comparable_today or comparable_tomorrow:
            current_value = today_consistent if comparable_today else tomorrow_consistent
            state = "partial" if current_value else "inconsistent"
        else:
            state = "unknown"

        self._attr_native_value = state
        attrs = self._base_attributes(snapshot)
        attrs.update(
            {
                "today_comparable": comparable_today,
                "today_consistent": today_consistent if comparable_today else None,
                "today_rte_color": _display_color(snapshot.today_rte.color) if snapshot.today_rte else None,
                "today_local_color": _display_color(snapshot.today_local.color) if snapshot.today_local else None,
                "tomorrow_comparable": comparable_tomorrow,
                "tomorrow_consistent": tomorrow_consistent if comparable_tomorrow else None,
                "tomorrow_rte_color": _display_color(snapshot.tomorrow_rte.color) if snapshot.tomorrow_rte else None,
                "tomorrow_local_color": _display_color(snapshot.tomorrow_local.color) if snapshot.tomorrow_local else None,
            }
        )
        self._attr_extra_state_attributes = attrs


class ResilienceLastUpdateSensor(_BaseResilienceSensor):
    """Timestamp of the last generated snapshot."""

    _attr_name = "Tempo dernière mise à jour résilience"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tempo_last_update"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.generated_at
        self._attr_extra_state_attributes = self._base_attributes(snapshot)
