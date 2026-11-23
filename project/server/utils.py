from enum import Enum
from typing import Any
from dataclasses import dataclass


@dataclass
class Message:
    entity_id: str
    payload: Any


class GameState(Enum):
    INIT = 0
    LOBBY = 1
    SCHUPFEN = 2
    PLAYING = 3


class SchupfenException(Exception):
    pass


class MissingSchupfenException(SchupfenException):
    pass

class InvalidCardException(SchupfenException):
    pass

class AlreadySchupfedException(SchupfenException):
    pass

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
