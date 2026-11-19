import asyncio
import json
import websockets
import random

import logging

from typing import Any

from cards import CARD_MAP
from combinations import card_ids_to_combination, Combination
from utils import (
    Message,
    GameState,
    CardsNotOnHandException,
    InvalidCombinationException,
    WrongCombinationException,
    LowCombinationException,
)
from entities import Player, Entity, Bot, RandomBot

UPDATE_RATE = 1 / 30
SOCKET_PORT = 5400

MIN_PLAYERS = 1
MAX_PLAYERS = 4

MOVE_ORDER: list[tuple[str, str]] = [("a", "a"), ("b", "a"), ("a", "b"), ("b", "b")]

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename=".log",
    level=logging.INFO,
    filemode="w+",
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class Game:
    def __init__(self) -> None:
        self.entities: list[Entity] = []
        self.teams: dict[str, dict[str, str | None]] = {
            "a": {"a": None, "b": None},
            "b": {"a": None, "b": None},
        }

        self.message_queue: list[Message] = list()
        self.is_running: bool = False

        self.move_count: int = 0
        self.move_offset: int = 0
        self.continous_pass_count: int = 0

        self.current_move_idx: int | None = None

        self.stack: list[Combination] = []
        self.current_combination: Combination | None = None

    # Must be JSON serializable
    def state(self) -> Any:
        public_state = [entity.get_public_state() for entity in self.entities]

        entity_at_move_keys = (
            MOVE_ORDER[self.current_move_idx]
            if self.current_move_idx is not None
            else None
        )

        entity_at_move_id = (
            self.get_entity_id_by_keys(entity_at_move_keys)
            if entity_at_move_keys is not None
            else None
        )

        current_combination = (
            self.current_combination.json()
            if self.current_combination is not None
            else None
        )

        return {
            "is_running": self.is_running,
            "entity_at_move_keys": entity_at_move_keys,
            "entity_at_move_id": entity_at_move_id,
            "teams": self.teams,
            "current_combination": current_combination,
            "public": public_state,
        }

    def get_entity_by_id(self, id: str) -> Entity | None:
        for entity in self.entities:
            if entity.id == id:
                return entity

        return None

    def get_entity_id_by_keys(self, keys: tuple[str, str]) -> str | None:
        team_key, player_key = keys

        return self.teams[team_key][player_key]

    def get_entity_by_keys(self, keys: tuple[str, str]) -> Entity | None:
        entity_id = self.get_entity_id_by_keys(keys)

        if not entity_id:
            return

        return self.get_entity_by_id(entity_id)

    def get_entity_at_move(self) -> Entity | None:
        if self.current_move_idx is None:
            return None
        return self.get_entity_by_keys(MOVE_ORDER[self.current_move_idx])

    def get_entities_amount(self) -> int:
        return len(self.entities)

    def get_entities_ready(self) -> bool:
        for entity in self.entities:
            if not entity.get_ready():
                return False

        return True

    def set_starter(self) -> None:
        if self.current_move_idx is None:
            for entitiy in self.entities:
                if entitiy.has_mahong():
                    self.move_offset = MOVE_ORDER.index(
                        (entitiy.team_key, entitiy.entity_key)
                    )

                    self.move_count = 0
                    self.current_move_idx = self.move_offset

                    break

    def add_entity_to_team(self, entity_id: str) -> tuple[str, str] | None:
        for team_key in self.teams:
            team = self.teams[team_key]

            for player_key in team:
                if team[player_key] is None:
                    team[player_key] = entity_id

                    return (team_key, player_key)

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)
        keys = self.add_entity_to_team(entity.id)

        if keys is None:
            # Lobby full :(
            return

        team_key, player_key = keys
        entity.set_keys(team_key, player_key)

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

    def next_turn(self) -> None:
        if self.continous_pass_count == 3:
            self.continous_pass_count = 0
            self.current_combination = None

        self.move_count += 1
        self.current_move_idx = (self.move_count + self.move_offset) % 4

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

    def can_play(self, hand: list[str], card_ids: list[str]) -> Combination:
        if len(set(card_ids)) != len(card_ids):
            raise InvalidCombinationException

        if any(card not in hand for card in card_ids):
            raise CardsNotOnHandException

        combination = card_ids_to_combination(card_ids)

        if combination is None:
            raise InvalidCombinationException

        if self.current_combination != None and type(combination) != type(
            self.current_combination
        ):
            raise WrongCombinationException

        if self.current_combination != None and not combination.beats(
            self.current_combination, self.stack[-1] if len(self.stack) > 0 else None
        ):
            raise LowCombinationException

        return combination

    def try_play_cards(self, entity: Entity, card_ids: list[str]) -> None:
        combination = self.can_play(entity.hand, card_ids)

        if self.current_combination:
            self.stack.append(self.current_combination)

        self.current_combination = combination

        for card in card_ids:
            entity.hand.remove(card)

    def queue_bot_action(self) -> None:
        entity = self.get_entity_at_move()

        if not isinstance(entity, Bot):
            return

        self.message_queue.append(Message(entity.get_id(), entity.choose_action(self)))

    async def handle_game_messages(self) -> None:
        if not len(self.message_queue):
            return

        message = self.message_queue.pop(0)

        entity_at_move = self.get_entity_at_move()
        entity = self.get_entity_by_id(message.entity_id)
        if not entity or not entity_at_move or not entity.id == entity_at_move.id:
            return

        if message.payload.get("played_cards"):
            selected_card_ids = message.payload["played_cards"]

            try:
                self.try_play_cards(entity, selected_card_ids)
            except InvalidCombinationException:
                return
            except CardsNotOnHandException:
                return

            # Go to the next player
            self.continous_pass_count = 0
            self.next_turn()

        if message.payload.get("pass"):
            if message.payload.get("pass") is True:
                self.continous_pass_count += 1
                self.next_turn()

    def init_bots(self) -> None:
        for _ in range(MAX_PLAYERS - self.get_entities_amount()):
            self.add_entity(RandomBot())

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
        self.move_count = 0
        self.move_offset = 0
        self.continous_pass_count = 0

        self.current_move_idx = None

        self.stack = []
        self.current_combination = None

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
        self.queue_bot_action()

    async def game_loop(self) -> None:
        self.set_starter()

        while self.is_running:
            await self.update(UPDATE_RATE)

            for entity in self.entities:
                try:
                    await entity.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.remove_entity(entity)

            await asyncio.sleep(UPDATE_RATE)

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
