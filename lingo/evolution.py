"""An evolutionary extension of the Naming Game (the optional GA variant).

In the base model every agent follows the same fixed strategy. Here we instead
give each agent an evolvable trait -- its inventiveness, the probability that it
coins a brand-new word when speaking even though it already knows words for the
meaning -- and let natural selection decide what value of that trait wins.

Agents that communicate successfully reproduce; offspring inherit the parent's
inventiveness with a small random mutation. The question the experiment answers
is: what communication strategy does evolution favour? The answer turns out to
be a strong, self-organised preference for re-using established words over
inventing new ones, which is exactly what makes a shared language possible.
"""

from __future__ import annotations

import random


class EvolutionaryNamingGame:
    """A genetic-algorithm layer on top of the Naming Game.

    The population is fully connected and uses a single meaning, which keeps the
    evolutionary signal clean. Each generation is one episode of the naming game
    followed by selection and mutation of the inventiveness trait.
    """

    def __init__(
        self,
        num_agents: int = 80,
        interactions_per_generation: int = 5000,
        mutation_sd: float = 0.05,
        tournament_size: int = 5,
        seed: int | None = None,
    ) -> None:
        if seed is not None:
            random.seed(seed)
        self.n = num_agents
        self.interactions = interactions_per_generation
        self.mutation_sd = mutation_sd
        self.tournament = tournament_size
        # The genome: each agent's inventiveness, initialised uniformly at random.
        self.inventiveness = [random.random() for _ in range(num_agents)]
        self._word_counter = 0
        self.history = {"generation": [], "inventiveness": [], "fitness": []}

    def _invent(self) -> str:
        self._word_counter += 1
        return f"w{self._word_counter}"

    def _play_generation(self) -> list[float]:
        """Run one episode of the naming game and return each agent's fitness
        (its communicative success rate over the episode)."""
        inv = [[] for _ in range(self.n)]
        success = [0] * self.n
        interactions = [0] * self.n

        for _ in range(self.interactions):
            s = random.randrange(self.n)
            h = random.randrange(self.n)
            while h == s:
                h = random.randrange(self.n)

            # The speaker invents a new word if it has none, or -- governed by
            # its inventiveness gene -- sometimes invents one anyway.
            if not inv[s] or random.random() < self.inventiveness[s]:
                word = self._invent()
                inv[s].append(word)
            else:
                word = random.choice(inv[s])

            interactions[s] += 1
            interactions[h] += 1
            if word in inv[h]:
                success[s] += 1
                success[h] += 1
                inv[s] = [word]   # standard reinforcement: both keep the
                inv[h] = [word]   # agreed word and drop the rest
            else:
                inv[h].append(word)

        return [success[i] / interactions[i] if interactions[i] else 0.0 for i in range(self.n)]

    def _next_generation(self, fitness: list[float]) -> None:
        """Tournament selection plus Gaussian mutation produces the next genome."""
        new_genes = []
        for _ in range(self.n):
            contenders = random.sample(range(self.n), self.tournament)
            winner = max(contenders, key=lambda i: fitness[i])
            child = self.inventiveness[winner] + random.gauss(0, self.mutation_sd)
            new_genes.append(min(1.0, max(0.0, child)))  # keep within [0, 1]
        self.inventiveness = new_genes

    def evolve(self, generations: int = 50):
        """Evolve the population and record the mean inventiveness and mean
        fitness at each generation."""
        for gen in range(generations):
            fitness = self._play_generation()
            self.history["generation"].append(gen)
            self.history["inventiveness"].append(sum(self.inventiveness) / self.n)
            self.history["fitness"].append(sum(fitness) / self.n)
            self._next_generation(fitness)
        return self.history
