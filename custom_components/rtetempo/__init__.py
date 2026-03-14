"""The RTE Tempo Calendar integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .api_worker import APIWorker
from .const import (
    CONFIG_CLIEND_SECRET,
    CONFIG_CLIENT_ID,
    DOMAIN,
    OPTION_ADJUSTED_DAYS,
)
from .resilience_service import TempoResilienceService

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.SELECT,
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up rtetempo from a config entry."""
    api_worker = APIWorker(
        client_id=str(entry.data.get(CONFIG_CLIENT_ID)),
        client_secret=str(entry.data.get(CONFIG_CLIEND_SECRET)),
        adjusted_days=bool(entry.options.get(OPTION_ADJUSTED_DAYS)),
    )
    api_worker.start()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, api_worker.signalstop)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    entry.async_on_unload(lambda: api_worker.signalstop("config_entry_unload"))

    try:
        hass.data[DOMAIN][entry.entry_id] = api_worker
    except KeyError:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][entry.entry_id] = api_worker

    resilience_service = TempoResilienceService(
        hass=hass,
        api_worker=api_worker,
        entry_options=entry.options,
    )
    hass.data[DOMAIN][f"{entry.entry_id}_resilience"] = resilience_service

    def cleanup_resilience_data() -> None:
        hass.data[DOMAIN].pop(f"{entry.entry_id}_resilience", None)

    entry.async_on_unload(cleanup_resilience_data)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(f"{entry.entry_id}_resilience", None)
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
