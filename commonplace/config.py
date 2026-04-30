"""Central configuration for Commonplace model routing and escalation policy."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = REPO_ROOT / ".env"

load_dotenv(dotenv_path=DOTENV_PATH)

FAST_MODEL = os.getenv("FAST_MODEL", "gpt-4o-mini")
SMART_MODEL = os.getenv("SMART_MODEL", "gpt-4o-2024-08-06")


@dataclass(frozen=True)
class ModelRoutingConfig:
    """Shared model-routing defaults and escalation policy."""

    fast_model: str
    smart_model: str
    low_confidence_threshold: str = "low"
    ambiguous_topic_threshold: int = 3
    escalation_triggers: tuple[str, ...] = field(
        default_factory=lambda: (
            "model-requested-escalation",
            "low-confidence",
            "flag-for-judgment",
            "ambiguous-append-target",
            "broad-topic-spread",
            "source-is-fragmentary",
        )
    )


COMMONPLACE_CONFIG = ModelRoutingConfig(
    fast_model=FAST_MODEL,
    smart_model=SMART_MODEL,
)


__all__ = ["COMMONPLACE_CONFIG", "DOTENV_PATH", "FAST_MODEL", "ModelRoutingConfig", "SMART_MODEL"]
