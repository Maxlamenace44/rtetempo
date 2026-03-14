"""Local Home Assistant entity source for resilient Tempo handling."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from homeassistant.core import HomeAssistant

from .const import (
    COLOR_BLUE,
    COLOR_RED,
    COLOR_UNKNOWN,
    COLOR_WHITE,
    RESOLVER_SOURCE_LOCAL,
)
from .source_models import TempoValue


def normalize_local_color(raw: str | None) -> str:
    """Normalize a local HA state into one of: blue, white, red, unknown."""
    if raw is None:
        return COLOR_UNKNOWN

    value = raw.strip().lower()

    mapping = {
        "bleu": COLOR_BLUE,
        "blue": COLOR_BLUE,
        "blanc": COLOR_WHITE,
        "white": COLOR_WHITE,
        "rouge": COLOR_RED,
        "red": COLOR_RED,
        "unknown": COLOR_UNKNOWN,
        "unavailable": COLOR_UNKNOWN,
    }

    return mapping.get(value, COLOR_UNKNOWN)


def read_local_tempo_value(
    hass: HomeAssistant,
    entity_id: str | None,
    details: Optional[str] = None,
) -> TempoValue | None:
    """Read one local HA entity and convert it into a TempoValue."""
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return TempoValue(
            color=COLOR_UNKNOWN,
            source=RESOLVER_SOURCE_LOCAL,
            available=False,
            fetched_at=datetime.now(),
            confidence=0.0,
            details=details or f"local entity not found: {entity_id}",
        )

    normalized = normalize_local_color(state.state)

    return TempoValue(
        color=normalized,
        source=RESOLVER_SOURCE_LOCAL,
        available=normalized != COLOR_UNKNOWN,
        fetched_at=datetime.now(),
        confidence=0.7 if normalized != COLOR_UNKNOWN else 0.0,
        details=details or f"local entity: {entity_id}",
    )
