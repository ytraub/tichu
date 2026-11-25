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

    def get_hand(self) -> list[str]:
        return self.hand

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

    def choose_action(self, state: Any, game) -> dict[str, Any] | None:
        return {"pass": True}


class RandomBot(Bot):
    def choose_action(self, state: Any, game) -> dict[str, Any] | None:
        game_state = state["game_state"]

        match game_state:
            case "SCHUPFEN":
                if self.schupfen is not None:
                    return

                teams = state["teams"]

                mate_entity_key = "a" if self.entity_key == "b" else "b"

                opposing_team_key = "a" if self.team_key == "b" else "b"

                left_entity_key = (
                    ("b" if self.team_key == "a" else "a")
                    if self.entity_key == "a"
                    else ("a" if self.team_key == "a" else "b")
                )

                right_entity_key = (
                    ("a" if self.team_key == "a" else "b")
                    if self.entity_key == "a"
                    else ("b" if self.team_key == "a" else "a")
                )

                mate_id = teams[self.team_key][mate_entity_key]
                left_id = teams[opposing_team_key][left_entity_key]
                right_id = teams[opposing_team_key][left_entity_key]

                cards = random.sample(self.hand, 3)

                return {
                    "schupfen": {
                        mate_id: cards[0],
                        left_id: cards[1],
                        right_id: cards[2],
                    }
                }

            case "PLAYING":
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

                can_pass = state["current_combination"] is not None
                if can_pass and (not legal or random.random() < 0.3):
                    return {"pass": True}

                return {"played_cards": random.choice(legal)}


""" class LowerBot(Bot):
    def choose_action(self, state: Any, game) -> dict[str, Any] | None:
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
        if can_pass and not legal:
            return {"pass": True}

        best_hand: list[str] = []
        best_score = None

        for h in legal:
            values = []
            for cid in h:
                values.append[CARD_MAP[cid].value]

            score = (max(values), sum(values))
            if best_score is None or best_score > score:
                best_score = score
                best_hand = h

        return {"played_cards": best_hand}


class NeatBot(Bot):
    def choose_action(self, game) -> dict[str, Any]:
        return {"pass": True}
 """
