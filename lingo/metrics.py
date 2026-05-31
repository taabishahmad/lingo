"""Quantitative metrics -- these produce the figures that back the report."""

from __future__ import annotations

from collections import Counter

from .agent import Agent


def total_distinct_words(agents: list[Agent], num_meanings: int) -> int:
    """How many different words exist across the whole population, summed over
    meanings. It spikes as agents invent, then collapses toward one-per-meaning
    as consensus forms."""
    total = 0
    for m in range(num_meanings):
        words = set()
        for agent in agents:
            words.update(agent.inventory[m])
        total += len(words)
    return total


def surviving_dialects(agents: list[Agent], num_meanings: int) -> int:
    """Number of distinct 'languages' that persist.

    Each agent's language is the tuple of its preferred word per meaning;
    distinct tuples are distinct dialects. One dialect == a single shared
    language for the whole population.
    """
    languages = Counter(
        tuple(agent.preferred_word(m) for m in range(num_meanings)) for agent in agents
    )
    return len(languages)


def dialect_breakdown(agents: list[Agent], num_meanings: int) -> dict[tuple, int]:
    """Maps each surviving language to how many agents speak it."""
    return dict(
        Counter(
            tuple(agent.preferred_word(m) for m in range(num_meanings)) for agent in agents
        )
    )
