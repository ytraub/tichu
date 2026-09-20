import asyncio
import json
import websockets
import uuid
import random

import logging

from typing import Any
from dataclasses import dataclass

from cards import Card, CARD_MAP

UPDATE_RATE = 1 / 30
SOCKET_PORT = 5400

MIN_PLAYERS = 1
MAX_PLAYERS = 4

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@dataclass
class Message:
    entity_id: str
    payload: Any


@dataclass
class Entity:
    id: str
    hand: list[str]
    ready: bool = False

    def get_id(self) -> str:
        return self.id

    def get_ready(self) -> bool:
        return self.ready

    def get_public_state(self) -> dict[str, Any]:
        return {"id": self.id}

    def get_private_state(self) -> dict[str, Any]:
        return {"hand": self.hand}

    def set_ready(self, state: bool) -> None:
        self.ready = state

    def set_hand(self, cardIds: list[str]) -> None:
        self.hand = cardIds

    async def send_state(self, game_state: Any) -> None:
        pass


class Player(Entity):
    client: websockets.ServerConnection

    def __init__(self, client: websockets.ServerConnection) -> None:
        super().__init__(
            id=str(uuid.uuid4()),
            hand=[],
        )
        self.client = client

    async def send_state(self, game_state: Any) -> None:
        state = {
            "game": game_state,
            "player": self.get_private_state() | self.get_public_state(),
        }
        await self.client.send(json.dumps(state))


class Bot(Entity):
    def __init__(self) -> None:
        self.id = str(uuid.uuid4())
        self.ready = True

    async def send_state(self, game_state: Any) -> None:
        return await super().send_state(game_state)


class Game:
    def __init__(self) -> None:
        self.entities: list[Entity] = []
        self.teams: dict[str, dict[str, str | None]] = {
            "a": {"a": None, "b": None},
            "b": {"a": None, "b": None},
        }

        self.message_queue: list[Message] = list()
        self.is_running: bool = False

        self.entity_turn_id = None

    # Must be JSON serializable
    def state(self) -> Any:
        return {
            "is_running": self.is_running,
            "entity_turn_id": self.entity_turn_id,
            "teams": self.teams,
        }

    def get_entity_by_id(self, id: str) -> Entity | None:
        for entity in self.entities:
            if entity.id == id:
                return entity

        return None

    def get_entities_amount(self) -> int:
        return len(self.entities)

    def get_entities_ready(self) -> bool:
        for entity in self.entities:
            if not entity.get_ready():
                return False

        return True

    def add_entity_to_team(self, entity_id: str) -> None:
        for team in self.teams.values():
            for slot in team:
                if team[slot] is None:
                    team[slot] = entity_id
                    return

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)
        self.add_entity_to_team(entity.id)

    def remove_entity_from_team(self, entity_id: str) -> None:
        for team in self.teams.values():
            for slot, value in team.items():
                if value is entity_id:
                    team[slot] = None

    def remove_entity(self, entity: Entity) -> None:
        self.entities.remove(entity)
        self.remove_entity_from_team(entity.id)

    async def client_handler(self, ws: websockets.ServerConnection) -> None:
        player = Player(ws)
        self.add_entity(player)

        logger.info(f"{player.get_id()} connected")

        try:
            await player.send_state(self.state())

            async for payload in ws:
                logger.info(f"Recived: {payload}")

                decoded = json.loads(payload)
                message = Message(player.get_id(), decoded)

                self.message_queue.append(message)

        except websockets.ConnectionClosed:
            pass

        finally:
            self.remove_entity(player)

    async def handle_lobby_messages(self) -> None:
        if not len(self.message_queue):
            return

        message = self.message_queue.pop(0)
        entity = self.get_entity_by_id(message.entity_id)

        if not entity:
            return

        if message.payload.get("ready"):
            logger.info(f"{entity.get_id()} is ready")
            entity.set_ready(message.payload.get("ready"))

    def handle_game_messages(self) -> None:
        for message in self.message_queue:
            pass

    def init_bots(self) -> None:
        for _ in range(MAX_PLAYERS - self.get_entities_amount()):
            self.add_entity(Bot())

    def deal_cards(self) -> None:
        shuffled = list(CARD_MAP)
        random.shuffle(shuffled)

        hand_size = len(shuffled) // MAX_PLAYERS
        hands = [
            shuffled[i : i + hand_size] for i in range(0, len(shuffled), hand_size)
        ]

        for i, entity in enumerate(self.entities):
            entity.set_hand(hands[i])

    async def start(self) -> None:
        def is_game_ready() -> bool:
            return (
                self.get_entities_amount() >= MIN_PLAYERS and self.get_entities_ready()
            )

        # Wait for players and start when they are ready
        logger.info("Waiting for players...")
        while not is_game_ready():
            await self.handle_lobby_messages()
            await asyncio.sleep(0.1)

        self.init_bots()
        self.deal_cards()

        logger.info("Starting...")

        self.is_running = True
        await self.game_loop()

        # start new game
        await self.start()

    def update(self, dt) -> None:
        pass

    async def game_loop(self) -> None:
        while self.is_running:
            self.update(UPDATE_RATE)

            for entity in self.entities:
                try:
                    await entity.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.remove_entity(entity)

            await asyncio.sleep(UPDATE_RATE)


async def main():
    game = Game()

    async with websockets.serve(
        game.client_handler,
        "localhost",
        SOCKET_PORT,
    ):
        print("Server listening on port", SOCKET_PORT)
        await game.start()


if __name__ == "__main__":
    asyncio.run(main())
