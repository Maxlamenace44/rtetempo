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


BLUE_HINTS = (
    "bleu",
    "blue",
    "tempo_bleu",
    "tempo-blue",
    "tempo blue",
    "jour_bleu",
    "jour bleu",
    "hcjb",
    "hpjb",
)
WHITE_HINTS = (
    "blanc",
    "white",
    "tempo_blanc",
    "tempo-white",
    "tempo white",
    "jour_blanc",
    "jour blanc",
    "hcjw",
    "hpjw",
)
RED_HINTS = (
    "rouge",
    "red",
    "tempo_rouge",
    "tempo-red",
    "tempo red",
    "jour_rouge",
    "jour rouge",
    "hcjr",
    "hpjr",
)
UNKNOWN_HINTS = (
    "unknown",
    "unavailable",
    "indisponible",
    "inconnu",
    "none",
    "null",
)


def normalize_local_color(raw: str | None) -> str:
    """Normalize a local HA state into one of: blue, white, red, unknown."""
    if raw is None:
        return COLOR_UNKNOWN

    value = raw.strip().lower()
    if not value:
        return COLOR_UNKNOWN

    if value in UNKNOWN_HINTS:
        return COLOR_UNKNOWN
    if value in BLUE_HINTS:
        return COLOR_BLUE
    if value in WHITE_HINTS:
        return COLOR_WHITE
    if value in RED_HINTS:
        return COLOR_RED

    if any(hint in value for hint in BLUE_HINTS):
        return COLOR_BLUE
    if any(hint in value for hint in WHITE_HINTS):
        return COLOR_WHITE
    if any(hint in value for hint in RED_HINTS):
        return COLOR_RED
    if any(hint in value for hint in UNKNOWN_HINTS):
        return COLOR_UNKNOWN

    return COLOR_UNKNOWN


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
