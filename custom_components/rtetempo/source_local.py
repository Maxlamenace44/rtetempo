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
    """Normalize a local HA state into one of: blue, white, red, unknown.

    Accepted inputs:
    - English/French colors, any case.
    - Labels containing HC/HP/Tempo (eg. "Rouge HP Tempo", "Bleu HC").
    - Numeric Tempo codes: 5/8 blue, 6/9 white, 7/10 red.

    Invalid business values return unknown:
    - 0 Base
    - 1/2 Bleu tariff outside Tempo business color
    - 3/4 EJP
    """
    if raw is None:
        return COLOR_UNKNOWN

    value = str(raw).strip().lower()
    if value in {"", "none", "unknown", "unavailable", "inconnu"}:
        return COLOR_UNKNOWN

    compact = value.replace("_", " ").replace("-", " ")

    if compact.isdigit():
        code = int(compact)
        if code in (5, 8):
            return COLOR_BLUE
        if code in (6, 9):
            return COLOR_WHITE
        if code in (7, 10):
            return COLOR_RED
        return COLOR_UNKNOWN

    if any(token in compact for token in ["base", "ejp", "jour normal", "jour de pointe"]):
        return COLOR_UNKNOWN

    if "bleu" in compact or "blue" in compact:
        # only explicit color labels are accepted in text mode
        return COLOR_BLUE
    if "blanc" in compact or "white" in compact:
        return COLOR_WHITE
    if "rouge" in compact or "red" in compact:
        return COLOR_RED

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
