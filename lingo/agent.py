"""The Agent: a single language learner with a private vocabulary."""

from __future__ import annotations

import random


class Agent:
    """An autonomous agent in the Naming Game.

    Each agent keeps a private inventory of words it associates with every
    meaning. Inventories start empty -- agents share no vocabulary at the
    beginning. They invent words, remember what works, and forget what does not.
    """

    def __init__(self, agent_id: int, num_meanings: int) -> None:
        self.id = agent_id
        # inventory[m] is the list of words this agent knows for meaning m.
        self.inventory: list[list[str]] = [[] for _ in range(num_meanings)]

    def speak(self, meaning: int, invent_word) -> str:
        """Produce a word for a meaning.

        If the agent knows no word yet, it invents one and stores it. Otherwise
        it picks a word it already knows (uniformly at random among them).
        """
        words = self.inventory[meaning]
        if not words:
            new_word = invent_word()
            words.append(new_word)
            return new_word
        return random.choice(words)

    def knows(self, meaning: int, word: str) -> bool:
        return word in self.inventory[meaning]

    def learn(self, meaning: int, word: str) -> None:
        """On a failed game, the hearer simply adds the new word."""
        if word not in self.inventory[meaning]:
            self.inventory[meaning].append(word)

    def agree_on(self, meaning: int, word: str) -> None:
        """On a successful game, both agents drop every competing word and
        keep only the one that worked -- the heart of the reinforcement rule."""
        self.inventory[meaning] = [word]

    def preferred_word(self, meaning: int) -> str | None:
        """The word the agent currently leans toward for a meaning.

        Used for visualisation (a dot's colour) and for counting dialects.
        We take the first word, which after convergence is the only one.
        """
        words = self.inventory[meaning]
        return words[0] if words else None
