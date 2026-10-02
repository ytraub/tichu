from typing import Any
from dataclasses import dataclass

from cards import Card, CARD_MAP


class Combination:
    def verify(self) -> bool:
        return False


@dataclass
class Single(Combination):
    card: Card

    def verify(self) -> bool:
        return True


@dataclass
class Pair(Combination):
    cards: tuple[Card, Card]

    def verify(self) -> bool:
        a, b = self.cards

        return a.value == b.value


@dataclass
class ThreeOfAKind(Combination):
    cards: tuple[Card, Card, Card]

    def verify(self) -> bool:
        a, b, c = self.cards

        return a.value == b.value and a.value == c.value


@dataclass
class FullHouse(Combination):
    pair: Pair
    three_of_a_kind: ThreeOfAKind

    def verify(self) -> bool:
        return self.pair.verify() and self.three_of_a_kind.verify()


@dataclass
class Straight(Combination):
    cards: list[Card]

    def verify(self) -> bool:
        if len(self.cards) < 5:
            return False

        start_value = None

        for card in self.cards:
            if start_value is not None and card.value != start_value + 1:
                return False

            start_value = card.value

        return True


@dataclass
class PairStraight(Combination):
    cards: list[Pair]

    def verify(self) -> bool:
        if len(self.cards) < 2:
            return False

        start_value = None

        for pair in self.cards:
            a, _ = pair.cards

            if (
                start_value is not None and a.value != start_value + 1
            ) or not pair.verify():
                return False

            start_value = a.value

        return True


@dataclass
class Bomb(Combination):
    cards: tuple[Card, Card, Card, Card]

    def verify(self) -> bool:
        a, b, c, d = self.cards

        return a.value == b.value and a.value == c.value and a.value == d.value


@dataclass
class StraightBomb(Combination):
    cards: list[Card]

    def verify(self) -> bool:
        if len(self.cards) < 5:
            return False

        common_color = self.cards[0].color
        start_value = None

        for card in self.cards:
            if (
                start_value is not None and card.value != start_value + 1
            ) or card.color != common_color:
                return False

            start_value = card.value

        return True
