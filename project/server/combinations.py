from typing import Self, Any, Optional
from dataclasses import dataclass

from cards import Card, CARD_MAP
from utils import InvalidCombinationException, list_subtraction


class Combination:
    min_cards_required: int

    def json(self) -> Any:
        return ""

    def verify(self) -> bool:
        return False

    def beats(
        self, their_combination: Self, previous_combination: Self | None = None
    ) -> bool:
        return False

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        return cls()


@dataclass
class Single(Combination):
    card: Card
    min_cards_required = 1

    def json(self) -> Any:
        return [self.card.card_id]

    def verify(self) -> bool:
        return True

    def beats(
        self,
        their_combination: Combination,
        previous_combination: Combination | None = None,
    ) -> bool:
        if not isinstance(their_combination, Single):
            return False

        if self.card.card_id == "phoenix":
            return their_combination.card.value < 15

        if their_combination.card.card_id == "phoenix":
            if not isinstance(previous_combination, Single):
                return False

            return self.card.value > previous_combination.card.value

        return self.card.value > their_combination.card.value

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        return cls(cards[0])


@dataclass
class Pair(Combination):
    cards: tuple[Card, Card]
    min_cards_required = 2

    def json(self) -> Any:
        a, b = self.cards

        return (a.card_id, b.card_id)

    def verify(self) -> bool:
        a, b = self.cards

        has_phoenix, _ = contains_phoenix(list(self.cards))
        if has_phoenix:
            return True

        return a.value == b.value

    def beats(
        self,
        their_combination: Combination,
        previous_combination: Combination | None = None,
    ) -> bool:
        if not isinstance(their_combination, Pair):
            return False

        my_without_phoenix = get_card_list_without_phoenix(list(self.cards))
        they_without_phoenix = get_card_list_without_phoenix(
            list(their_combination.cards)
        )

        return my_without_phoenix[0].value > they_without_phoenix[0].value

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

    def json(self) -> Any:
        a, b, c = self.cards

        return (a.card_id, b.card_id, c.card_id)

    def verify(self) -> bool:
        without_phoenix = get_card_list_without_phoenix(list(self.cards))

        return all(x.value == without_phoenix[0].value for x in without_phoenix)

    def beats(
        self,
        their_combination: Combination,
        previous_combination: Combination | None = None,
    ) -> bool:
        if not isinstance(their_combination, ThreeOfAKind):
            return False

        my_without_phoenix = get_card_list_without_phoenix(list(self.cards))
        they_without_phoenix = get_card_list_without_phoenix(
            list(their_combination.cards)
        )

        return my_without_phoenix[0].value > they_without_phoenix[0].value

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

    def json(self) -> Any:
        return (self.three_of_a_kind.json(), self.pair.json())

    def verify(self) -> bool:
        return self.pair.verify() and self.three_of_a_kind.verify()

    def beats(
        self,
        their_combination: Combination,
        previous_combination: Combination | None = None,
    ) -> bool:
        if not isinstance(their_combination, FullHouse):
            return False

        return self.three_of_a_kind.beats(their_combination.three_of_a_kind)

    @classmethod
    def from_cards(cls, cards: list[Card]) -> Self:
        def get_subsets(
            matching_card_list: list[Card], remaining_card_list: list[Card]
        ) -> tuple[Pair, ThreeOfAKind]:
            match len(matching_card_list):
                case 1:  # phoenix required in pair matching
                    has_phoenix, i = contains_phoenix(remaining_card_list)

                    if not has_phoenix:
                        raise InvalidCombinationException()

                    phoenix = remaining_card_list.pop(i)

                    return Pair.from_cards(
                        [*matching_card_list, phoenix]
                    ), ThreeOfAKind.from_cards(remaining_card_list)
                case 2:  # could be both, for now chose higher
                    has_phoenix, i = contains_phoenix(remaining_card_list)
                    if not has_phoenix:  # No phoenix at all
                        return Pair.from_cards(
                            matching_card_list
                        ), ThreeOfAKind.from_cards(remaining_card_list)

                    matching_without_phoenix = get_card_list_without_phoenix(
                        matching_card_list
                    )
                    remaining_without_phoenix = get_card_list_without_phoenix(
                        remaining_card_list
                    )

                    if (
                        matching_card_list[0].value < remaining_card_list[0].value
                    ):  # phoenix already at right place
                        return Pair.from_cards(
                            matching_card_list
                        ), ThreeOfAKind.from_cards(remaining_card_list)

                    phoenix = remaining_card_list.pop(i)

                    return Pair.from_cards(
                        remaining_card_list
                    ), ThreeOfAKind.from_cards([*matching_card_list, phoenix])

                case 3:  # phoenix required in pair remaining
                    has_phoenix, _ = contains_phoenix(remaining_card_list)
                    if not has_phoenix:  # No phoenix at all
                        return Pair.from_cards(
                            remaining_card_list
                        ), ThreeOfAKind.from_cards(matching_card_list)

                    return Pair.from_cards(
                        remaining_card_list
                    ), ThreeOfAKind.from_cards(matching_card_list)
                case _:
                    raise InvalidCombinationException()

        if len(cards) != cls.min_cards_required:
            raise InvalidCombinationException()

        anchor_value = cards[0].value
        matching = [card for card in cards if card.value == anchor_value]
        remaining = list_subtraction(cards, matching)

        pair, three_of_a_kind = get_subsets(matching, remaining)

        if not (pair.verify() and three_of_a_kind.verify()):
            raise InvalidCombinationException()

        return cls(pair, three_of_a_kind)


@dataclass
class Straight(Combination):
    cards: list[Card]
    min_cards_required = 5

    def json(self) -> Any:
        return (card.card_id for card in self.cards)

    def verify(self) -> bool:
        if len(self.cards) < 5:
            return False

        start_value = None

        for card in self.cards:
            if start_value is not None and card.value != start_value + 1:
                return False

            start_value = card.value

        return True

    def beats(
        self, combination: Combination, previous_combination: Combination | None = None
    ) -> bool:
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

    def json(self) -> Any:
        return [pair.json() for pair in self.cards]

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

    def beats(
        self, combination: Combination, previous_combination: Combination | None = None
    ) -> bool:
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

    def json(self) -> Any:
        a, b, c, d = self.cards

        return (a.card_id, b.card_id, c.card_id, d.card_id)

    def verify(self) -> bool:
        a, b, c, d = self.cards

        return a.value == b.value and a.value == c.value and a.value == d.value

    def beats(
        self, combination: Combination, previous_combination: Combination | None = None
    ) -> bool:
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

    def json(self) -> Any:
        return (card.card_id for card in self.cards)

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

    def beats(
        self, combination: Combination, previous_combination: Combination | None = None
    ) -> bool:
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


def get_card_list_without_phoenix(card_list: list[Card]) -> list[Card]:
    return [card for card in card_list if not card.card_id == "phoenix"]


def contains_phoenix(card_list: list[Card]) -> tuple[bool, int]:
    for i, card in enumerate(card_list):
        if card.card_id == "phoenix":
            return True, i

    return False, -1


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
    x = card_ids_to_combination(["black_a", "black_a", "green_a", "red_2", "black_2"])
    print(x)
    """ x = card_ids_to_combination(["black_a", "phoenix", "green_2", "red_2", "black_2"])
    print(x)
    x = card_ids_to_combination(["black_a", "green_a", "phoenix", "red_2", "black_2"])
    print(x)
    x = card_ids_to_combination(["black_k", "phoenix", "green_k", "red_q", "black_q"])
    print(x) """

    """ if x is None or y is None:
        pass
    else:
        print(x.beats(y)) """
