"""Lingo: an agent-based simulation of emergent shared language.

Public API:
    NamingGame      -- the simulation engine
    Agent           -- a single language learner
    build_network   -- construct an interaction topology
    NETWORK_TYPES   -- the three structures compared in the study
"""

from .agent import Agent
from .evolution import EvolutionaryNamingGame
from .game import NamingGame
from .metrics import dialect_breakdown, surviving_dialects, total_distinct_words
from .networks import NETWORK_TYPES, build_network, grid_positions

__all__ = [
    "Agent",
    "NamingGame",
    "EvolutionaryNamingGame",
    "build_network",
    "grid_positions",
    "NETWORK_TYPES",
    "total_distinct_words",
    "surviving_dialects",
    "dialect_breakdown",
]
