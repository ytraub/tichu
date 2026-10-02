from typing import Any


class CardsNotOnHandException(Exception):
    pass


class InvalidCombinationException(Exception):
    pass


def list_subtraction(input: list[Any], negative: list[Any]) -> list[Any]:
    return [x for x in input if x not in negative]
