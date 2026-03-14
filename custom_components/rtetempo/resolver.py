"""Resolution helpers for resilient Tempo handling."""
from __future__ import annotations

from .const import (
    FALLBACK_DEFAULT,
    FALLBACK_LAST_GOOD,
    FALLBACK_UNKNOWN,
    RESOLVER_SOURCE_DEFAULT,
)
from .source_default import build_default_tempo_value
from .source_models import ResolvedTempoValue, TempoValue


def resolve_primary_value(
    primary: TempoValue | None,
    secondary: TempoValue | None,
    fallback_strategy: str,
    default_color: str | None,
    last_good: TempoValue | None = None,
) -> ResolvedTempoValue:
    """Resolve one value with a simple priority chain: primary -> secondary -> fallback."""
    if primary and primary.available:
        return ResolvedTempoValue(
            color=primary.color,
            source=primary.source,
            degraded=False,
            fallback_reason=None,
            fetched_at=primary.fetched_at,
        )

    if secondary and secondary.available:
        return ResolvedTempoValue(
            color=secondary.color,
            source=secondary.source,
            degraded=True,
            fallback_reason="primary_unavailable",
            fetched_at=secondary.fetched_at,
        )

    if fallback_strategy == FALLBACK_LAST_GOOD and last_good and last_good.available:
        return ResolvedTempoValue(
            color=last_good.color,
            source=last_good.source,
            degraded=True,
            fallback_reason="fallback_last_good",
            fetched_at=last_good.fetched_at,
        )

    if fallback_strategy == FALLBACK_DEFAULT:
        default_value = build_default_tempo_value(default_color, "fallback_default")
        return ResolvedTempoValue(
            color=default_value.color,
            source=RESOLVER_SOURCE_DEFAULT,
            degraded=True,
            fallback_reason="fallback_default",
            fetched_at=default_value.fetched_at,
        )

    if fallback_strategy == FALLBACK_UNKNOWN:
        unknown_value = build_default_tempo_value("unknown", "fallback_unknown")
        return ResolvedTempoValue(
            color=unknown_value.color,
            source=RESOLVER_SOURCE_DEFAULT,
            degraded=True,
            fallback_reason="fallback_unknown",
            fetched_at=unknown_value.fetched_at,
        )

    unknown_value = build_default_tempo_value("unknown", "implicit_unknown")
    return ResolvedTempoValue(
        color=unknown_value.color,
        source=RESOLVER_SOURCE_DEFAULT,
        degraded=True,
        fallback_reason="implicit_unknown",
        fetched_at=unknown_value.fetched_at,
    )
