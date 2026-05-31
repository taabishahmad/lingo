"""The Naming Game engine -- the core of Lingo.

A population of agents that share no words plays repeated pairwise games. With
nothing but a "keep what works, drop the rest" rule, a shared language emerges
from purely local interactions. No agent ever sees the global state.
"""

from __future__ import annotations

import random
import string
from collections import deque

import networkx as nx

from .agent import Agent
from .metrics import surviving_dialects, total_distinct_words
from .networks import build_network


def _make_word_factory():
    """Returns a function that hands out fresh, unique nonsense words such as
    'vv0', 'qx1' -- the invented sounds agents coin when they have none."""
    counter = {"n": 0}

    def invent() -> str:
        letters = "".join(random.choice(string.ascii_lowercase) for _ in range(2))
        word = f"{letters}{counter['n']}"
        counter["n"] += 1
        return word

    return invent


class NamingGame:
    """Runs the simulation and records the metric history step by step."""

    def __init__(
        self,
        num_agents: int = 50,
        num_meanings: int = 3,
        network_type: str = "fully_connected",
        noise: float = 0.0,
        seed: int | None = None,
    ) -> None:
        if seed is not None:
            random.seed(seed)

        self.num_agents = num_agents
        self.num_meanings = num_meanings
        self.noise = noise

        self.network: nx.Graph = build_network(network_type, num_agents)
        self.agents = [Agent(i, num_meanings) for i in range(num_agents)]
        self._invent = _make_word_factory()

        self.step_count = 0
        # A rolling window of recent outcomes gives a smooth success rate.
        self._recent_outcomes: deque[int] = deque(maxlen=max(50, num_agents))

        # Metric history, sampled as the simulation runs.
        self.history = {
            "step": [],
            "distinct_words": [],
            "success_rate": [],
            "dialects": [],
        }

    # -- one interaction -------------------------------------------------

    def step(self) -> bool:
        """Play exactly one pairwise naming game. Returns True on success."""
        speaker = self.agents[random.randrange(self.num_agents)]
        neighbours = list(self.network.neighbors(speaker.id))
        if not neighbours:
            return False
        hearer = self.agents[random.choice(neighbours)]
        meaning = random.randrange(self.num_meanings)

        word = speaker.speak(meaning, self._invent)

        # Noise occasionally garbles the transmitted word in flight.
        transmitted = word
        if self.noise > 0 and random.random() < self.noise:
            transmitted = self._invent()

        self.step_count += 1

        if hearer.knows(meaning, transmitted):
            # Success: both sides collapse to the single agreed word.
            speaker.agree_on(meaning, transmitted)
            hearer.agree_on(meaning, transmitted)
            self._recent_outcomes.append(1)
            return True

        # Failure: the hearer just files the new word away for next time.
        hearer.learn(meaning, transmitted)
        self._recent_outcomes.append(0)
        return False

    # -- running and sampling --------------------------------------------

    def success_rate(self) -> float:
        if not self._recent_outcomes:
            return 0.0
        return sum(self._recent_outcomes) / len(self._recent_outcomes)

    def record(self) -> None:
        self.history["step"].append(self.step_count)
        self.history["distinct_words"].append(
            total_distinct_words(self.agents, self.num_meanings)
        )
        self.history["success_rate"].append(self.success_rate())
        self.history["dialects"].append(
            surviving_dialects(self.agents, self.num_meanings)
        )

    def run(self, max_steps: int, sample_every: int = 0, stop_on_convergence: bool = True):
        """Run the simulation, sampling metrics periodically.

        Stops early once the population has fully converged (a sustained 100%
        success rate with a single word per meaning), unless asked not to.
        """
        if sample_every <= 0:
            sample_every = max(1, self.num_agents)

        self.record()
        for _ in range(max_steps):
            self.step()
            if self.step_count % sample_every == 0:
                self.record()
                if stop_on_convergence and self._has_converged():
                    break
        self.record()
        return self.history

    def _has_converged(self) -> bool:
        """Converged means every meaning has settled on exactly one word
        across the whole population (and there is no noise pushing it around)."""
        if self.noise > 0:
            # With noise the system never perfectly locks, so judge by success.
            return self.success_rate() >= 0.99 and len(self._recent_outcomes) >= self._recent_outcomes.maxlen
        return total_distinct_words(self.agents, self.num_meanings) == self.num_meanings

    def convergence_step(self, threshold: float = 0.95) -> int | None:
        """The first sampled step where success rate crossed the threshold.
        Returns None if the run never got there."""
        for step, rate in zip(self.history["step"], self.history["success_rate"]):
            if rate >= threshold:
                return step
        return None
