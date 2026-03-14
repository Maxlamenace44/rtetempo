"""Buttons for Tempo resilience runtime tests."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_MANUFACTURER, DEVICE_MODEL, DEVICE_NAME, DOMAIN
from .resilience_service import TempoResilienceService


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up runtime button entities."""
    resilience_service = hass.data[DOMAIN].get(f"{config_entry.entry_id}_resilience")
    if resilience_service is None:
        return
    async_add_entities(
        [TempoResolverResetButton(config_entry.entry_id, resilience_service)],
        True,
    )


class TempoResolverResetButton(ButtonEntity):
    """Reset runtime override and cache for resilience tests."""

    _attr_has_entity_name = True
    _attr_name = "Reset résilience Tempo"
    _attr_icon = "mdi:restart-alert"

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_resolver_reset"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._config_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    async def async_press(self) -> None:
        self._service.reset_runtime_state()
