"""Resilience diagnostic sensors for Tempo handling."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DEVICE_MANUFACTURER, DEVICE_MODEL, DEVICE_NAME, DOMAIN
from .resilience_service import TempoResilienceService


SOURCE_OPTIONS = ["web", "local", "default", "forecast", "unknown"]
MODE_OPTIONS = ["auto", "web", "local", "default", "compare"]
CONSISTENCY_OPTIONS = ["consistent", "inconsistent", "partial", "unknown"]
SOURCE_STATUS_OPTIONS = ["nominal", "dégradé", "fallback", "indisponible"]


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
        self._listener = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _refresh() -> None:
            self.async_schedule_update_ha_state(True)

        self._listener = _refresh
        self._service.register_listener(_refresh)

    async def async_will_remove_from_hass(self) -> None:
        if self._listener is not None:
            self._service.unregister_listener(self._listener)
        await super().async_will_remove_from_hass()

    def _base_attributes(self, snapshot):
        return {
            "configured_mode": snapshot.configured_source_mode,
            "effective_mode": snapshot.effective_source_mode,
            "runtime_override_mode": snapshot.runtime_source_mode,
            "local_current_entity": snapshot.local_today_entity,
            "local_next_entity": snapshot.local_tomorrow_entity,
            "source_status": snapshot.source_status,
            "last_evaluated_at": snapshot.evaluated_at.isoformat(),
            "last_changed_at": snapshot.last_change_at.isoformat() if snapshot.last_change_at else None,
            "last_valid_source_at": snapshot.last_valid_source_at.isoformat() if snapshot.last_valid_source_at else None,
        }


class CurrentResolvedColorSensor(_BaseResilienceSensor):
    """Resolved current color."""

    _attr_name = "Couleur actuelle résolue"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:shield-check"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_current_resolved"

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
                "web_color": _display_color(snapshot.today_rte.color) if snapshot.today_rte else None,
                "web_available": snapshot.today_rte.available if snapshot.today_rte else False,
                "local_color": _display_color(snapshot.today_local.color) if snapshot.today_local else None,
                "local_available": snapshot.today_local.available if snapshot.today_local else False,
            }
        )
        self._attr_extra_state_attributes = attrs


class CurrentResolvedSourceSensor(_BaseResilienceSensor):
    """Resolved current source."""

    _attr_name = "Source actuelle résolue"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_OPTIONS
    _attr_icon = "mdi:source-branch"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_current_source"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.today.source
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class NextResolvedColorSensor(_BaseResilienceSensor):
    """Resolved next color."""

    _attr_name = "Prochaine couleur résolue"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Bleu", "Blanc", "Rouge", "Inconnu"]
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_next_resolved"

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
                "web_color": _display_color(snapshot.tomorrow_rte.color) if snapshot.tomorrow_rte else None,
                "web_available": snapshot.tomorrow_rte.available if snapshot.tomorrow_rte else False,
                "local_color": _display_color(snapshot.tomorrow_local.color) if snapshot.tomorrow_local else None,
                "local_available": snapshot.tomorrow_local.available if snapshot.tomorrow_local else False,
            }
        )
        self._attr_extra_state_attributes = attrs


class NextResolvedSourceSensor(_BaseResilienceSensor):
    """Resolved next source."""

    _attr_name = "Source prochaine résolue"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_OPTIONS
    _attr_icon = "mdi:source-merge"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_next_source"

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


class ResilienceSourceStatusSensor(_BaseResilienceSensor):
    """Stable source status."""

    _attr_name = "Source status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SOURCE_STATUS_OPTIONS
    _attr_icon = "mdi:lan-connect"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_source_status"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.source_status
        attrs = self._base_attributes(snapshot)
        attrs.update(
            {
                "current_source": snapshot.today.source,
                "next_source": snapshot.tomorrow.source,
            }
        )
        self._attr_extra_state_attributes = attrs


class ResilienceConsistencySensor(_BaseResilienceSensor):
    """Consistency state between web and local sources."""

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

        current_consistent = (
            snapshot.today_rte is not None
            and snapshot.today_local is not None
            and snapshot.today_rte.available
            and snapshot.today_local.available
            and snapshot.today_rte.color == snapshot.today_local.color
        )
        next_consistent = (
            snapshot.tomorrow_rte is not None
            and snapshot.tomorrow_local is not None
            and snapshot.tomorrow_rte.available
            and snapshot.tomorrow_local.available
            and snapshot.tomorrow_rte.color == snapshot.tomorrow_local.color
        )

        comparable_current = bool(
            snapshot.today_rte is not None
            and snapshot.today_local is not None
            and snapshot.today_rte.available
            and snapshot.today_local.available
        )
        comparable_next = bool(
            snapshot.tomorrow_rte is not None
            and snapshot.tomorrow_local is not None
            and snapshot.tomorrow_rte.available
            and snapshot.tomorrow_local.available
        )

        if comparable_current and comparable_next:
            state = "consistent" if (current_consistent and next_consistent) else "inconsistent"
        elif comparable_current or comparable_next:
            current_value = current_consistent if comparable_current else next_consistent
            state = "partial" if current_value else "inconsistent"
        else:
            state = "unknown"

        self._attr_native_value = state
        attrs = self._base_attributes(snapshot)
        attrs.update(
            {
                "current_comparable": comparable_current,
                "current_consistent": current_consistent if comparable_current else None,
                "current_web_color": _display_color(snapshot.today_rte.color) if snapshot.today_rte else None,
                "current_local_color": _display_color(snapshot.today_local.color) if snapshot.today_local else None,
                "next_comparable": comparable_next,
                "next_consistent": next_consistent if comparable_next else None,
                "next_web_color": _display_color(snapshot.tomorrow_rte.color) if snapshot.tomorrow_rte else None,
                "next_local_color": _display_color(snapshot.tomorrow_local.color) if snapshot.tomorrow_local else None,
            }
        )
        self._attr_extra_state_attributes = attrs


class ResilienceLastEvaluationSensor(_BaseResilienceSensor):
    """Timestamp of the last resolver evaluation."""

    _attr_name = "Tempo dernière évaluation résilience"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tempo_last_evaluation"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = True
        self._attr_native_value = snapshot.evaluated_at
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class ResilienceLastChangeSensor(_BaseResilienceSensor):
    """Timestamp of the last effective business change."""

    _attr_name = "Tempo dernière mise à jour résilience"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tempo_last_change"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = snapshot.last_change_at is not None
        self._attr_native_value = snapshot.last_change_at
        self._attr_extra_state_attributes = self._base_attributes(snapshot)


class ResilienceLastValidSourceSensor(_BaseResilienceSensor):
    """Timestamp of the last valid payload received from the active source."""

    _attr_name = "Tempo dernière donnée valide source"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:database-check-outline"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        super().__init__(config_id, service)
        self._attr_unique_id = f"{DOMAIN}_{config_id}_tempo_last_valid_source"

    def update(self) -> None:
        snapshot = self._service.build_snapshot()
        self._attr_available = snapshot.last_valid_source_at is not None
        self._attr_native_value = snapshot.last_valid_source_at
        self._attr_extra_state_attributes = self._base_attributes(snapshot)
