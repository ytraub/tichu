import asyncio
import json
import websockets
import uuid
import random

import logging

from typing import Any
from dataclasses import dataclass

from cards import Card, CARD_MAP
from combinations import card_ids_to_combination, Combination
from utils import CardsNotOnHandException, InvalidCombinationException, WrongCombinationException, LowCombinationException

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


class Entity:
    id: str
    hand: list[str]
    ready: bool = False

    def __init__(self, id, hand, ready) -> None:
        self.id = id
        self.hand = hand
        self.ready = ready

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
        self.turn_count = 0

        self.stack: list[list[str]] = []
        self.current_combination: Combination | None = None

    # Must be JSON serializable
    def state(self) -> Any:
        return {
            "is_running": self.is_running,
            "entity_turn_id": self.entity_turn_id,
            "teams": self.teams,
            "stack": self.stack,
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

    def next_turn(self) -> None:
        team = "a" if self.turn_count % 2 == 0 else "b"
        entity = "a" if self.turn_count % 4 < 2 else "b"

        self.entity_turn_id = self.teams[team][entity]
        self.turn_count += 1

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
        try:
            self.entities.remove(entity)
        except ValueError:
            pass

        self.remove_entity_from_team(entity.id)

    async def client_recive(self, ws: websockets.ServerConnection) -> None:
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

    def try_play_cards(self, entity: Entity, card_ids: list[str]) -> None:
        combination = card_ids_to_combination(card_ids)

        if combination is None:
            raise InvalidCombinationException

        if self.current_combination != None and type(combination) != type(self.current_combination):
            raise WrongCombinationException

        if self.current_combination != None and not combination.beats(self.current_combination):
            raise LowCombinationException

        self.current_combination = combination

        # Now check if player actually has these card_ids
        for card in card_ids:
            if not card in entity.hand:
                raise CardsNotOnHandException

            entity.hand.remove(card)

    async def handle_game_messages(self) -> None:
        if not len(self.message_queue):
            return

        message = self.message_queue.pop(0)
        entity = self.get_entity_by_id(message.entity_id)

        if not entity:
            return

        if message.payload.get("selected_cards"):
            selected_card_ids = message.payload["selected_cards"]

            try:
                self.try_play_cards(entity, selected_card_ids)
            except InvalidCombinationException:
                return
            except CardsNotOnHandException:
                return

            self.stack.append(selected_card_ids)

            # Go to the next player
            self.next_turn()

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

    def init_game(self) -> None:
        self.entity_turn_id = None
        self.turn_count = 0
        self.stack = []

    async def start_game(self) -> None:
        self.init_game()

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
        await self.start_game()

    async def update(self, dt) -> None:
        await self.handle_game_messages()

    async def game_loop(self) -> None:
        self.next_turn()

        while self.is_running:
            await self.update(UPDATE_RATE)

            for entity in self.entities:
                try:
                    await entity.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.remove_entity(entity)

            await asyncio.sleep(UPDATE_RATE)


async def main():
    game = Game()

    async with websockets.serve(
        game.client_recive,
        "localhost",
        SOCKET_PORT,
    ):
        print("Server listening on port", SOCKET_PORT)
        await game.start_game()


if __name__ == "__main__":
    asyncio.run(main())
