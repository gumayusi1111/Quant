"""Entry point to build end-to-end signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from src.signal_generator.rules import crossover_rule
from src.signal_generator.scorer import score_signals


@dataclass
class Signal:
    symbol: str
    action: int
    confidence: float


def generate_signals(symbols: Iterable[str], fast: List[float], slow: List[float]) -> List[Signal]:
    """Combine rule + scorer pipeline."""
    rule_outputs = crossover_rule(fast, slow)
    scores = score_signals(rule_outputs)
    results: List[Signal] = []
    for idx, symbol in enumerate(symbols):
        action = rule_outputs[idx] if idx < len(rule_outputs) else 0
        confidence = scores[idx] if idx < len(scores) else 0.0
        results.append(Signal(symbol=symbol, action=action, confidence=confidence))
    return results
