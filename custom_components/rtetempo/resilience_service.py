"""Resilient orchestration service for Tempo values."""
from __future__ import annotations

from collections.abc import Callable
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
    RESOLVER_SOURCE_DEFAULT,
    SOURCE_MODE_AUTO,
    SOURCE_MODE_COMPARE,
    SOURCE_MODE_DEFAULT,
    SOURCE_MODE_LOCAL,
    SOURCE_MODE_WEB,
    SOURCE_STATUS_DEGRADED,
    SOURCE_STATUS_FALLBACK,
    SOURCE_STATUS_NOMINAL,
    SOURCE_STATUS_UNAVAILABLE,
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
    evaluated_at: datetime
    configured_source_mode: str
    effective_source_mode: str
    source_status: str
    last_change_at: datetime | None = None
    last_valid_source_at: datetime | None = None
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
        self.last_effective_signature: tuple | None = None
        self.last_effective_change_at: datetime | None = None
        self.last_valid_source_at: datetime | None = None
        self._listeners: set[Callable[[], None]] = set()

    def register_listener(self, listener: Callable[[], None]) -> None:
        """Register an entity refresh listener."""
        self._listeners.add(listener)

    def unregister_listener(self, listener: Callable[[], None]) -> None:
        """Unregister an entity refresh listener."""
        self._listeners.discard(listener)

    def _notify_listeners(self) -> None:
        """Notify entities that a refresh is required."""
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                continue

    def get_configured_source_mode(self) -> str:
        """Return source mode from config entry options."""
        return str(self.entry_options.get(OPTION_SOURCE_MODE, SOURCE_MODE_AUTO))

    def get_effective_source_mode(self) -> str:
        """Return runtime override mode if present, otherwise configured mode."""
        return self.runtime_source_mode or self.get_configured_source_mode()

    def set_runtime_source_mode(self, mode: str | None) -> None:
        """Set or clear a temporary runtime source mode override."""
        normalized = None if mode in (None, "", SOURCE_MODE_AUTO) else str(mode)
        self.runtime_source_mode = normalized
        self.invalidate_cache()
        self.build_snapshot(force=True)
        self._notify_listeners()

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
        self.build_snapshot(force=True)
        self._notify_listeners()

    def _resolve_status(
        self,
        source_mode: str,
        today: ResolvedTempoValue,
        tomorrow: ResolvedTempoValue,
        today_rte: TempoValue | None,
        today_local: TempoValue | None,
        tomorrow_rte: TempoValue | None,
        tomorrow_local: TempoValue | None,
    ) -> str:
        """Return a stable source status string."""
        expected_source = {
            SOURCE_MODE_WEB: "web",
            SOURCE_MODE_LOCAL: "local",
            SOURCE_MODE_DEFAULT: "default",
            SOURCE_MODE_AUTO: "web",
            SOURCE_MODE_COMPARE: "web",
        }.get(source_mode, "web")

        comparable_web = bool(
            (today_rte and today_rte.available) or (tomorrow_rte and tomorrow_rte.available)
        )
        comparable_local = bool(
            (today_local and today_local.available) or (tomorrow_local and tomorrow_local.available)
        )

        if expected_source != "default" and all(
            resolved.source == expected_source and not resolved.degraded
            for resolved in (today, tomorrow)
        ):
            return SOURCE_STATUS_NOMINAL

        if any(resolved.source == RESOLVER_SOURCE_DEFAULT for resolved in (today, tomorrow)):
            if not comparable_web and not comparable_local:
                return SOURCE_STATUS_UNAVAILABLE
            return SOURCE_STATUS_FALLBACK

        if any(resolved.degraded for resolved in (today, tomorrow)):
            return SOURCE_STATUS_DEGRADED

        return SOURCE_STATUS_NOMINAL

    def _update_change_tracking(
        self,
        now: datetime,
        source_mode: str,
        status: str,
        today: ResolvedTempoValue,
        tomorrow: ResolvedTempoValue,
    ) -> None:
        signature = (
            source_mode,
            status,
            today.color,
            today.source,
            today.degraded,
            today.fallback_reason,
            tomorrow.color,
            tomorrow.source,
            tomorrow.degraded,
            tomorrow.fallback_reason,
        )
        if self.last_effective_signature != signature or self.last_effective_change_at is None:
            self.last_effective_signature = signature
            self.last_effective_change_at = now

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

        valid_candidates: list[datetime] = []
        if today.source == "web" and today_rte and today_rte.available and today_rte.fetched_at:
            valid_candidates.append(today_rte.fetched_at)
        if today.source == "local" and today_local and today_local.available and today_local.fetched_at:
            valid_candidates.append(today_local.fetched_at)
        if tomorrow.source == "web" and tomorrow_rte and tomorrow_rte.available and tomorrow_rte.fetched_at:
            valid_candidates.append(tomorrow_rte.fetched_at)
        if tomorrow.source == "local" and tomorrow_local and tomorrow_local.available and tomorrow_local.fetched_at:
            valid_candidates.append(tomorrow_local.fetched_at)
        if valid_candidates:
            self.last_valid_source_at = max(valid_candidates)

        source_status = self._resolve_status(
            source_mode,
            today,
            tomorrow,
            today_rte,
            today_local,
            tomorrow_rte,
            tomorrow_local,
        )
        self._update_change_tracking(now, source_mode, source_status, today, tomorrow)

        snapshot = ResilienceSnapshot(
            today=today,
            tomorrow=tomorrow,
            evaluated_at=now,
            configured_source_mode=self.get_configured_source_mode(),
            effective_source_mode=source_mode,
            source_status=source_status,
            last_change_at=self.last_effective_change_at,
            last_valid_source_at=self.last_valid_source_at,
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
