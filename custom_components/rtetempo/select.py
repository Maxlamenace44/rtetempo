"""Runtime test controls for Tempo resilience."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    RUNTIME_SOURCE_MODE_OPTIONS,
    SOURCE_MODE_AUTO,
)
from .resilience_service import TempoResilienceService


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up runtime select entities."""
    resilience_service = hass.data[DOMAIN].get(f"{config_entry.entry_id}_resilience")
    if resilience_service is None:
        return
    async_add_entities(
        [TempoSourceModeSelect(config_entry.entry_id, resilience_service)],
        True,
    )


class TempoSourceModeSelect(SelectEntity):
    """Temporary runtime source selector for the resolver."""

    _attr_has_entity_name = True
    _attr_name = "Sélecteur source Tempo"
    _attr_icon = "mdi:source-branch"
    _attr_options = RUNTIME_SOURCE_MODE_OPTIONS
    _attr_should_poll = True

    def __init__(self, config_id: str, service: TempoResilienceService) -> None:
        self._config_id = config_id
        self._service = service
        self._attr_unique_id = f"{DOMAIN}_{config_id}_source_mode_select"
        self._attr_current_option = SOURCE_MODE_AUTO

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
        mode = self._service.get_effective_source_mode()
        self._attr_current_option = mode if mode in self._attr_options else SOURCE_MODE_AUTO
        self._attr_extra_state_attributes = {
            "configured_mode": self._service.get_configured_source_mode(),
            "runtime_override_mode": self._service.runtime_source_mode,
            "note": "Sélecteur de test non destructif ; reset pour revenir à la configuration sauvegardée",
        }

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise ValueError(f"Invalid option: {option}")
        self._service.set_runtime_source_mode(option)
        self._attr_current_option = option
        self.async_write_ha_state()
