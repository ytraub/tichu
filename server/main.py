import asyncio
import json
import websockets
import uuid
import random

from typing import Any
from dataclasses import dataclass

from cards import Card, CARD_MAP

UPDATE_RATE = 1 / 30
SOCKET_PORT = 5400
PLAYER_AMOUNT = 4


@dataclass
class Message:
    player_id: str
    payload: Any


@dataclass
class Entity:
    id: str
    hand: list[str]

    def get_id(self) -> str:
        return self.id

    def get_state(self) -> dict[str, Any]:
        return {"hand": self.hand}

    def set_hand(self, cardIds: list[str]) -> Any:
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

    async def send_state(self, game_state: Any) -> None:
        return await super().send_state(game_state)


class Game:
    def __init__(self) -> None:
        self.entities: list[Entity] = list()

        self.message_queue: list[Message] = list()

    def update(self, dt) -> None:
        for message in self.message_queue:
            pass

    def state(self) -> Any:
        return {}

    async def client_handler(self, ws: websockets.ServerConnection) -> None:
        player = Player(ws)
        self.entities.append(player)

        try:
            await player.send_state(self.state())

            async for payload in ws:
                message = Message(player.get_id(), json.loads(payload))
                self.message_queue.append(message)

        except websockets.ConnectionClosed:
            pass

        finally:
            self.entities.remove(player)

    async def start(self) -> None:
        print("sleeping")
        await asyncio.sleep(5)
        print("start")
        
        self.init_bots()
        self.deal_cards()

        await self.game_loop()

    async def game_loop(self) -> None:
        while True:
            self.update(UPDATE_RATE)

            for entity in list(self.entities):
                try:
                    await entity.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.entities.remove(entity)

            await asyncio.sleep(UPDATE_RATE)

    def init_bots(self) -> None:
        print(self.entities)
        for _ in range(min(PLAYER_AMOUNT - len(self.entities), 4)):
            self.entities.append(Bot())

    def deal_cards(self) -> None:
        shuffled = list(CARD_MAP)
        random.shuffle(shuffled)

        hand_size = len(shuffled) // PLAYER_AMOUNT
        hands = [
            shuffled[i : i + hand_size] for i in range(0, len(shuffled), hand_size)
        ]
        
        print(len(hands), len(self.entities))

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


asyncio.run(main())
