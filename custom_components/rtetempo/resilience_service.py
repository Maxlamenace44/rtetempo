"""Resilient orchestration service for Tempo values."""
from __future__ import annotations

from dataclasses import dataclass
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
    SOURCE_MODE_LOCAL,
    SOURCE_MODE_WEB,
)
from .resolver import resolve_primary_value
from .source_local import read_local_tempo_value
from .source_models import ResolvedTempoValue, TempoValue
from .source_rte import read_rte_current_value, read_rte_next_value


@dataclass
class ResilienceSnapshot:
    """Resolved snapshot for today and tomorrow."""

    today: ResolvedTempoValue
    tomorrow: ResolvedTempoValue
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

    def build_snapshot(self) -> ResilienceSnapshot:
        """Build a resolved snapshot for today and tomorrow."""
        source_mode = self.entry_options.get(OPTION_SOURCE_MODE, SOURCE_MODE_AUTO)
        fallback_strategy = self.entry_options.get(
            OPTION_FALLBACK_STRATEGY, FALLBACK_UNKNOWN
        )

        local_today_entity = self.entry_options.get(OPTION_LOCAL_TODAY_ENTITY)
        local_tomorrow_entity = self.entry_options.get(OPTION_LOCAL_TOMORROW_ENTITY)

        default_today_color = self.entry_options.get(OPTION_DEFAULT_TODAY_COLOR, "unknown")
        default_tomorrow_color = self.entry_options.get(OPTION_DEFAULT_TOMORROW_COLOR, "unknown")

        today_rte = read_rte_current_value(self.api_worker, "today_rte")
        tomorrow_rte = read_rte_next_value(self.api_worker, "tomorrow_rte")

        today_local = read_local_tempo_value(self.hass, local_today_entity, "today_local")
        tomorrow_local = read_local_tempo_value(self.hass, local_tomorrow_entity, "tomorrow_local")

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
            self.last_good_today = today_loca_
