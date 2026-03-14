"""Internal source and resolution models for resilient Tempo handling."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TempoValue:
    """Represents a color value coming from one source."""

    color: str
    source: str
    available: bool = True
    fetched_at: Optional[datetime] = None
    confidence: Optional[float] = None
    details: Optional[str] = None


@dataclass
class ResolvedTempoValue:
    """Represents the final resolved color after arbitration."""

    color: str
    source: str
    degraded: bool = False
    fallback_reason: Optional[str] = None
    compared_with: Optional[str] = None
    consistent: Optional[bool] = None
    fetched_at: Optional[datetime] = None
