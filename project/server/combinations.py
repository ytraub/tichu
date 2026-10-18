from typing import Self, Any
from dataclasses import dataclass

from cards import Card, CARD_MAP
from utils import InvalidCombinationException, list_subtraction


class Combination:
    min_cards_required: int

    def verify(self) -> bool:
        return False

    def beats(self, combination: Self) -> bool:
        return False

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        return cls()


@dataclass
class Single(Combination):
    card: Card
    min_cards_required = 1

    def verify(self) -> bool:
        return True

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, Single):
            return False

        return self.card.value > combination.card.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        return cls(cards[0])


@dataclass
class Pair(Combination):
    cards: tuple[Card, Card]
    min_cards_required = 2

    def verify(self) -> bool:
        a, b = self.cards

        return a.value == b.value

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, Pair):
            return False

        x, _ = self.cards
        y, _ = combination.cards

        return x.value > y.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        combination = cls((cards[0], cards[1]))

        if not combination.verify():
            raise InvalidCombinationException()

        return combination


@dataclass
class ThreeOfAKind(Combination):
    cards: tuple[Card, Card, Card]
    min_cards_required = 3

    def verify(self) -> bool:
        a, b, c = self.cards

        return a.value == b.value and a.value == c.value

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, ThreeOfAKind):
            return False

        x, _, _ = self.cards
        y, _, _ = combination.cards

        return x.value > y.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        combination = cls((cards[0], cards[1], cards[2]))

        if not combination.verify():
            raise InvalidCombinationException()

        return combination


@dataclass
class FullHouse(Combination):
    pair: Pair
    three_of_a_kind: ThreeOfAKind
    min_cards_required = 5

    def verify(self) -> bool:
        return self.pair.verify() and self.three_of_a_kind.verify()

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, FullHouse):
            return False

        return self.three_of_a_kind.beats(combination.three_of_a_kind)

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        anchor_value = cards[0].value
        matching = [card for card in cards if card.value == anchor_value]
        remaining = list_subtraction(cards, matching)

        if len(matching) == 2:
            pair = Pair.from_cards(matching)
            three_of_a_kind = ThreeOfAKind.from_cards(remaining)

        elif len(matching) == 3:
            three_of_a_kind = ThreeOfAKind.from_cards(matching)
            pair = Pair.from_cards(remaining)

        else:
            raise InvalidCombinationException()

        if not (pair.verify() and three_of_a_kind.verify()):
            raise InvalidCombinationException()

        return cls(pair, three_of_a_kind)


@dataclass
class Straight(Combination):
    cards: list[Card]
    min_cards_required = 5

    def verify(self) -> bool:
        if len(self.cards) < 5:
            return False

        start_value = None

        for card in self.cards:
            if start_value is not None and card.value != start_value + 1:
                return False

            start_value = card.value

        return True

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, Straight):
            return False

        if len(self.cards) != len(combination.cards):
            return False

        x = self.cards[0]
        y = combination.cards[0]

        return x.value > y.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) < cls.min_cards_required:
            raise InvalidCombinationException()

        straight = cls(sorted(cards, key=lambda card: card.value))

        if not straight.verify():
            raise InvalidCombinationException()

        return straight


@dataclass
class PairStraight(Combination):
    cards: list[Pair]
    min_cards_required = 4

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

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, PairStraight):
            return False

        if len(self.cards) != len(combination.cards):
            return False

        x = self.cards[0]
        y = combination.cards[0]

        return x.beats(y)

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) < cls.min_cards_required:
            raise InvalidCombinationException()

        sorted_cards = sorted(cards, key=lambda card: card.value)
        pairs = []

        for i in range(0, len(sorted_cards), 2):
            pairs.append(Pair.from_cards([sorted_cards[i], sorted_cards[i + 1]]))

        combination = cls(pairs)

        if not combination.verify():
            raise InvalidCombinationException()

        return combination


@dataclass
class Bomb(Combination):
    cards: tuple[Card, Card, Card, Card]
    min_cards_required = 4

    def verify(self) -> bool:
        a, b, c, d = self.cards

        return a.value == b.value and a.value == c.value and a.value == d.value

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, Bomb):
            return False

        x, _, _, _ = self.cards
        y, _, _, _ = combination.cards

        return x.value > y.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != 4:
            raise InvalidCombinationException()

        combination = cls((cards[0], cards[1], cards[2], cards[3]))

        if not combination.verify():
            raise InvalidCombinationException()

        return combination


@dataclass
class StraightBomb(Combination):
    cards: list[Card]
    min_cards_required = 5

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

    def beats(self, combination: Combination) -> bool:
        if not isinstance(combination, StraightBomb):
            return False

        if len(self.cards) == len(combination.cards):
            return self.cards[0].value > combination.cards[0].value

        return len(self.cards) > len(combination.cards)

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) < cls.min_cards_required:
            raise InvalidCombinationException()

        combination = cls(sorted(cards, key=lambda card: card.value))

        if not combination.verify():
            raise InvalidCombinationException()

        return combination


COMBINATIONS: list[type[Combination]] = [
    FullHouse,
    PairStraight,
    Bomb,
    Straight,
    StraightBomb,
    ThreeOfAKind,
    Pair,
    Single,
]


def get_cards_from_card_ids(card_ids: list[str]) -> list[Card]:
    cards = []

    for card_id in card_ids:
        card = CARD_MAP.get(card_id)
        if card is not None:
            cards.append(card)

    return cards


def card_ids_to_combination(card_ids: list[str]) -> Combination | None:
    cards = get_cards_from_card_ids(card_ids)

    for combination in COMBINATIONS:
        if combination.min_cards_required >= len(cards):
            try:
                return combination.from_cards(cards)
            except InvalidCombinationException:
                continue


if __name__ == "__main__":
    x = card_ids_to_combination(["blue_2", "red_2", "black_2", "black_k", "green_k"])
    y = card_ids_to_combination(["blue_3", "red_3", "black_3", "black_4", "green_4"])
    x = card_ids_to_combination(["blue_2"])
    y = card_ids_to_combination(["blue_3"])
    x = card_ids_to_combination(["blue_a", "black_a"])
    y = card_ids_to_combination(["blue_j", "blue_j", "green_j"])
    
    if x is None or y is None:
        pass
    else:
        print(x.beats(y))
