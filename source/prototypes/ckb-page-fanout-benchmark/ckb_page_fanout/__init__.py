"""Deterministic, source-bound page-fanout benchmark prototype."""

from .contracts import FanoutError
from .generator import generate_fanout, rollback_fanout

__all__ = ["FanoutError", "generate_fanout", "rollback_fanout"]
