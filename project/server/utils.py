from typing import Any
from dataclasses import dataclass


@dataclass
class Message:
    entity_id: str
    payload: Any


class CardsNotOnHandException(Exception):
    pass


class CombinationException(Exception):
    pass


class InvalidCombinationException(CombinationException):
    pass


class WrongCombinationException(CombinationException):
    pass


class LowCombinationException(CombinationException):
    pass


def list_subtraction(input: list[Any], negative: list[Any]) -> list[Any]:
    return [x for x in input if x not in negative]
