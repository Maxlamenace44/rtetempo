"""Default fallback source for resilient Tempo handling."""
from __future__ import annotations

from datetime import datetime

from .const import (
    COLOR_UNKNOWN,
    RESOLVER_SOURCE_DEFAULT,
)
from .source_models import TempoValue


def build_default_tempo_value(color: str | None, details: str | None = None) -> TempoValue:
    """Build a TempoValue coming from the default fallback source."""
    normalized = (color or COLOR_UNKNOWN).strip().lower()

    if normalized not in {"blue", "white", "red", "unknown"}:
        normalized = COLOR_UNKNOWN

    return TempoValue(
        color=normalized,
        source=RESOLVER_SOURCE_DEFAULT,
        available=normalized != COLOR_UNKNOWN,
        fetched_at=datetime.now(),
        confidence=0.1 if normalized != COLOR_UNKNOWN else 0.0,
        details=details or "default fallback value",
    )
