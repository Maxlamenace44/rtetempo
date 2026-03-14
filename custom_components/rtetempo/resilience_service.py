"""Resilient orchestration service for Tempo values."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from homeassistant.core import HomeAssistant

from .api_worker import APIWorker
from .const import (
    FALLBACK_UNKNOWN,
    OPTION_DEFAULT_TODAY_COLOR,
    OPTION_DEFAULT_TOMORROW_COLOR,
    OPTION_FALLBACK_STRATEGY,
    OPTION_LOCAL_TODAY_ENTITY,
    OPTION_LOCAL_TOMORROW_ENTITY,
    OPTION_SOURCE_MODE,
    SOURCE_MODE_AUTO,
    SOURCE_MODE_COMPARE,
    SOURCE_MODE_DEFAULT,
    SOURCE_MODE_LOCAL,
    SOURCE_MODE_WEB,
)
from .resolver import resolve_primary_value
from .source_default import build_default_tempo_value
from .source_local import read_local_tempo_value
from .source_models import ResolvedTempoValue, TempoValue
from .source_rte import read_rte_current_value, read_rte_next_value

SNAPSHOT_CACHE_TTL = timedelta(seconds=1)


@dataclass
class ResilienceSnapshot:
    """Resolved snapshot for today and tomorrow."""

    today: ResolvedTempoValue
    tomorrow: ResolvedTempoValue
    generated_at: datetime
    configured_source_mode: str
    effective_source_mode: str
    runtime_source_mode: str | None = None
    local_today_entity: str | None = None
    local_tomorrow_entity: str | None = None
    today_rte: TempoValue | None = None
    today_local: TempoValue | None = None
    tomorrow_rte: TempoValue | None = None
    tomorrow_local: TempoValue | None = None


class TempoResilienceService:
    """Simple orchestration layer for web/local/fallback resolution."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_worker: APIWorker | None,
        entry_options: dict,
    ) -> None:
        self.hass = hass
        self.api_worker = api_worker
        self.entry_options = entry_options
        self.last_good_today: Optional[TempoValue] = None
        self.last_good_tomorrow: Optional[TempoValue] = None
        self.runtime_source_mode: str | None = None
        self.last_snapshot: ResilienceSnapshot | None = None
        self.last_snapshot_at: datetime | None = None

    def get_configured_source_mode(self) -> str:
        """Return source mode from config entry options."""
        return str(self.entry_options.get(OPTION_SOURCE_MODE, SOURCE_MODE_AUTO))

    def get_effective_source_mode(self) -> str:
        """Return runtime override mode if present, otherwise configured mode."""
        return self.runtime_source_mode or self.get_configured_source_mode()

    def set_runtime_source_mode(self, mode: str | None) -> None:
        """Set or clear a temporary runtime source mode override."""
        self.runtime_source_mode = mode
        self.invalidate_cache()

    def invalidate_cache(self) -> None:
        """Invalidate snapshot cache."""
        self.last_snapshot = None
        self.last_snapshot_at = None

    def reset_runtime_state(self) -> None:
        """Reset runtime override and last good values."""
        self.runtime_source_mode = None
        self.last_good_today = None
        self.last_good_tomorrow = None
        self.invalidate_cache()

    def build_snapshot(self, force: bool = False) -> ResilienceSnapshot:
        """Build a resolved snapshot for today and tomorrow."""
        now = datetime.now(timezone.utc)
        if (
            not force
            and self.last_snapshot is not None
            and self.last_snapshot_at is not None
            and now - self.last_snapshot_at <= SNAPSHOT_CACHE_TTL
        ):
            return self.last_snapshot

        source_mode = self.get_effective_source_mode()
        fallback_strategy = self.entry_options.get(
            OPTION_FALLBACK_STRATEGY, FALLBACK_UNKNOWN
        )

        local_today_entity = self.entry_options.get(OPTION_LOCAL_TODAY_ENTITY)
        local_tomorrow_entity = self.entry_options.get(OPTION_LOCAL_TOMORROW_ENTITY)

        default_today_color = self.entry_options.get(
            OPTION_DEFAULT_TODAY_COLOR, "unknown"
        )
        default_tomorrow_color = self.entry_options.get(
            OPTION_DEFAULT_TOMORROW_COLOR, "unknown"
        )

        today_rte = read_rte_current_value(self.api_worker, "today_rte")
        tomorrow_rte = read_rte_next_value(self.api_worker, "tomorrow_rte")

        today_local = read_local_tempo_value(
            self.hass, local_today_entity, "today_local"
        )
        tomorrow_local = read_local_tempo_value(
            self.hass, local_tomorrow_entity, "tomorrow_local"
        )

        if source_mode == SOURCE_MODE_WEB:
            today = resolve_primary_value(
                today_rte,
                None,
                fallback_strategy,
                default_today_color,
                self.last_good_today,
            )
            tomorrow = resolve_primary_value(
                tomorrow_rte,
                None,
                fallback_strategy,
                default_tomorrow_color,
                self.last_good_tomorrow,
            )
        elif source_mode == SOURCE_MODE_LOCAL:
            today = resolve_primary_value(
                today_local,
                None,
                fallback_strategy,
                default_today_color,
                self.last_good_today,
            )
            tomorrow = resolve_primary_value(
                tomorrow_local,
                None,
                fallback_strategy,
                default_tomorrow_color,
                self.last_good_tomorrow,
            )
        elif source_mode == SOURCE_MODE_DEFAULT:
            today_default = build_default_tempo_value(
                default_today_color, "forced_default_today"
            )
            tomorrow_default = build_default_tempo_value(
                default_tomorrow_color, "forced_default_tomorrow"
            )
            today = ResolvedTempoValue(
                color=today_default.color,
                source=today_default.source,
                degraded=True,
                fallback_reason="forced_default_mode",
                fetched_at=today_default.fetched_at,
            )
            tomorrow = ResolvedTempoValue(
                color=tomorrow_default.color,
                source=tomorrow_default.source,
                degraded=True,
                fallback_reason="forced_default_mode",
                fetched_at=tomorrow_default.fetched_at,
            )
        else:
            # auto + compare start with same priority chain for V1
            today = resolve_primary_value(
                today_rte,
                today_local,
                fallback_strategy,
                default_today_color,
                self.last_good_today,
            )
            tomorrow = resolve_primary_value(
                tomorrow_rte,
                tomorrow_local,
                fallback_strategy,
                default_tomorrow_color,
                self.last_good_tomorrow,
            )

            if source_mode == SOURCE_MODE_COMPARE:
                today.compared_with = today_local.source if today_local else None
                tomorrow.compared_with = tomorrow_local.source if tomorrow_local else None
                today.consistent = (
                    today_rte is not None
                    and today_local is not None
                    and today_rte.available
                    and today_local.available
                    and today_rte.color == today_local.color
                )
                tomorrow.consistent = (
                    tomorrow_rte is not None
                    and tomorrow_local is not None
                    and tomorrow_rte.available
                    and tomorrow_local.available
                    and tomorrow_rte.color == tomorrow_local.color
                )

        if today_rte and today_rte.available:
            self.last_good_today = today_rte
        elif today_local and today_local.available:
            self.last_good_today = today_local

        if tomorrow_rte and tomorrow_rte.available:
            self.last_good_tomorrow = tomorrow_rte
        elif tomorrow_local and tomorrow_local.available:
            self.last_good_tomorrow = tomorrow_local

        snapshot = ResilienceSnapshot(
            today=today,
            tomorrow=tomorrow,
            generated_at=now,
            configured_source_mode=self.get_configured_source_mode(),
            effective_source_mode=source_mode,
            runtime_source_mode=self.runtime_source_mode,
            local_today_entity=local_today_entity or None,
            local_tomorrow_entity=local_tomorrow_entity or None,
            today_rte=today_rte,
            today_local=today_local,
            tomorrow_rte=tomorrow_rte,
            tomorrow_local=tomorrow_local,
        )
        self.last_snapshot = snapshot
        self.last_snapshot_at = now
        return snapshot
