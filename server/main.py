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

    def get_state(self) -> dict[str, Any]:
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
        state = {"game": game_state, "player": self.get_state()}
        await self.client.send(json.dumps(state))


class Bot(Entity):
    def __init__(self) -> None:
        self.id = str(uuid.uuid4())
        self.ready = True

    async def send_state(self, game_state: Any) -> None:
        return await super().send_state(game_state)


class Game:
    def __init__(self) -> None:
        self.entities: list[Entity] = list()

        self.message_queue: list[Message] = list()
        self.is_running: bool = False

    def get_entity_by_id(self, id: str) -> Entity | None:
        for entity in self.entities:
            if entity.id == id:
                return entity

        return None

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

    def update(self, dt) -> None:
        pass

    def state(self) -> Any:
        return {"is_running": self.is_running}

    def get_entities_amount(self) -> int:
        return len(self.entities)

    def get_entities_ready(self) -> bool:
        for entity in self.entities:
            if not entity.get_ready():
                return False

        return True

    async def client_handler(self, ws: websockets.ServerConnection) -> None:
        player = Player(ws)
        self.entities.append(player)

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
            self.entities.remove(player)

    async def start(self) -> None:
        def is_game_ready() -> bool:
            # print(self.get_entities_amount(), MIN_PLAYERS, self.get_entities_ready())
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

    async def game_loop(self) -> None:
        while self.is_running:
            self.update(UPDATE_RATE)

            for entity in list(self.entities):
                try:
                    await entity.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.entities.remove(entity)

            await asyncio.sleep(UPDATE_RATE)

    def init_bots(self) -> None:
        for _ in range(MAX_PLAYERS - self.get_entities_amount()):
            self.entities.append(Bot())

    def deal_cards(self) -> None:
        shuffled = list(CARD_MAP)
        random.shuffle(shuffled)

        hand_size = len(shuffled) // MAX_PLAYERS
        hands = [
            shuffled[i : i + hand_size] for i in range(0, len(shuffled), hand_size)
        ]

        for i, entity in enumerate(self.entities):
            entity.set_hand(hands[i])


async def main():
    game = Game()

    async with websockets.serve(
        game.client_handler,
        "localhost",
        SOCKET_PORT,
    ):
        await game.start()


if __name__ == "__main__":
    asyncio.run(main())
