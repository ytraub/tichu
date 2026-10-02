from typing import Any
from dataclasses import dataclass

from cards import Card, CARD_MAP


class Combination:
    def verify(self) -> bool:
        return False


@dataclass
class Single(Combination):
    card: Card


@dataclass
class Pair(Combination):
    cards: tuple[Card, Card]


@dataclass
class ThreeOfAKind(Combination):
    cards: tuple[Card, Card, Card]


@dataclass
class FullHouse(Combination):
    pair: Pair
    three_of_a_kind: ThreeOfAKind


@dataclass
class Straight(Combination):
    cards: list[Card]


@dataclass
class PairStraight(Combination):
    cards: list[Pair]


@dataclass
class Bomb(Combination):
    cards: tuple[Card, Card, Card, Card]


@dataclass
class StraightBomb(Combination):
    cards: list[Card]
