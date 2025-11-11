"""Signal generation layer."""

from .generator import generate_signals
from .rules import crossover_rule
from .scorer import score_signals

__all__ = ["generate_signals", "crossover_rule", "score_signals"]
