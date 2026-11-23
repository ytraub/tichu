import json
import websockets
import uuid
import random

from itertools import combinations
from typing import Any

from utils import (
    Message,
    CardsNotOnHandException,
    InvalidCombinationException,
    WrongCombinationException,
    LowCombinationException,
)


class Entity:
    id: str
    hand: list[str]
    ready: bool = False

    schupfen: dict | None = None

    team_key: str
    entity_key: str

    def __init__(self, id, hand, ready) -> None:
        self.id = id
        self.hand = hand
        self.ready = ready

    def get_id(self) -> str:
        return self.id

    def get_ready(self) -> bool:
        return self.ready

    def get_schupfen(self) -> dict | None:
        return self.schupfen

    def get_public_state(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "card_amount": len(self.hand),
            "team_key": self.team_key,
            "entity_key": self.entity_key,
        }

    def has_mahong(self) -> bool:
        return "mahong" in self.hand

    def get_private_state(self) -> dict[str, Any]:
        return {"hand": self.hand, "schupfen": self.schupfen}

    def set_ready(self, state: bool) -> None:
        self.ready = state

    def set_schupfen(self, state: dict) -> None:
        self.schupfen = state

    def set_hand(self, cardIds: list[str]) -> None:
        self.hand = cardIds

    def set_keys(self, team_key: str, entity_key: str) -> None:
        self.team_key = team_key
        self.entity_key = entity_key

    async def send_state(self, game_state: Any) -> None:
        pass


class Player(Entity):
    client: websockets.ServerConnection

    def __init__(self, client: websockets.ServerConnection) -> None:
        super().__init__(str(uuid.uuid4()), [], False)
        self.client = client

    async def send_state(self, game_state: Any) -> None:
        state = {
            "game": game_state,
            "player": self.get_private_state() | self.get_public_state(),
        }

        await self.client.send(json.dumps(state))


class Bot(Entity):
    def __init__(self) -> None:
        super().__init__(str(uuid.uuid4()), [], True)

    def choose_action(self, game) -> dict[str, Any]:
        return {"pass": True}


class RandomBot(Bot):
    def choose_action(self, game) -> dict[str, Any]:
        legal: list[list[str]] = []

        for size in range(1, len(self.hand) + 1):
            for ids in combinations(self.hand, size):
                try:
                    game.can_play(self.hand, list(ids))
                except (
                    InvalidCombinationException,
                    WrongCombinationException,
                    LowCombinationException,
                    CardsNotOnHandException,
                ):
                    continue
                legal.append(list(ids))

        can_pass = game.current_combination is not None
        if can_pass and (not legal or random.random() < 0.3):
            return {"pass": True}

        return {"played_cards": random.choice(legal)}
