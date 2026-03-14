"""RTE API worker adapter for resilient Tempo handling."""
from __future__ import annotations

import datetime
from typing import Optional

from .api_worker import APIWorker
from .const import (
    COLOR_BLUE,
    COLOR_RED,
    COLOR_UNKNOWN,
    COLOR_WHITE,
    FRANCE_TZ,
    RESOLVER_SOURCE_RTE,
    API_VALUE_BLUE,
    API_VALUE_RED,
    API_VALUE_WHITE,
)
from .source_models import TempoValue


def normalize_rte_color(raw: str | None) -> str:
    """Normalize an RTE raw color into one of: blue, white, red, unknown."""
    if raw is None:
        return COLOR_UNKNOWN

    value = raw.strip().upper()

    mapping = {
        API_VALUE_BLUE: COLOR_BLUE,
        API_VALUE_WHITE: COLOR_WHITE,
        API_VALUE_RED: COLOR_RED,
    }

    return mapping.get(value, COLOR_UNKNOWN)


def read_rte_current_value(
    api_worker: APIWorker | None,
    details: Optional[str] = None,
) -> TempoValue | None:
    """Read the current day color from the API worker cache."""
    if api_worker is None:
        return None

    localized_now = datetime.datetime.now(FRANCE_TZ)

    for tempo_day in api_worker.get_adjusted_days():
        if tempo_day.Start <= localized_now < tempo_day.End:
            normalized = normalize_rte_color(tempo_day.Value)
            return TempoValue(
                color=normalized,
                source=RESOLVER_SOURCE_RTE,
                available=normalized != COLOR_UNKNOWN,
                fetched_at=tempo_day.Updated,
                confidence=0.95 if normalized != COLOR_UNKNOWN else 0.0,
                details=details or "rte current day from APIWorker",
            )

    return TempoValue(
        color=COLOR_UNKNOWN,
        source=RESOLVER_SOURCE_RTE,
        available=False,
        fetched_at=localized_now,
        confidence=0.0,
        details=details or "rte current day unavailable in APIWorker cache",
    )


def read_rte_next_value(
    api_worker: APIWorker | None,
    details: Optional[str] = None,
) -> TempoValue | None:
    """Read the next day color from the API worker cache."""
    if api_worker is None:
        return None

    localized_now = datetime.datetime.now(FRANCE_TZ)

    for tempo_day in api_worker.get_adjusted_days():
        if localized_now < tempo_day.Start:
            normalized = normalize_rte_color(tempo_day.Value)
            return TempoValue(
                color=normalized,
                source=RESOLVER_SOURCE_RTE,
                available=normalized != COLOR_UNKNOWN,
                fetched_at=tempo_day.Updated,
                confidence=0.9 if normalized != COLOR_UNKNOWN else 0.0,
                details=details or "rte next day from APIWorker",
            )

    return TempoValue(
        color=COLOR_UNKNOWN,
        source=RESOLVER_SOURCE_RTE,
        available=False,
        fetched_at=localized_now,
        confidence=0.0,
        details=details or "rte next day unavailable in APIWorker cache",
    )
