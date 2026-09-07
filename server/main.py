import asyncio
import json
import websockets

from typing import Any

UPDATE_RATE = 1 / 30

SOCKET_PORT = 5400


class Player:
    def __init__(self, client: websockets.ServerConnection) -> None:
        self.client = client

        self.hand = ["phoenix", "red_2", "black_6", "blue_7"]

    async def send_state(self, game_state: Any) -> None:
        state = {"game": game_state, "player": self.state()}
        await self.client.send(json.dumps(state))

    def state(self):
        return {"hand": self.hand}


class Game:
    def __init__(self):
        self.players: set[Player] = set()
        self.bots = set()

    def update(self, dt):
        pass

    def state(self):
        return {}

    async def client_handler(self, ws: websockets.ServerConnection):
        player = Player(ws)
        self.players.add(player)

        try:
            await player.send_state(self.state())

            async for message in ws:
                data = json.loads(message)
                print("Client:", data)

        except websockets.ConnectionClosed:
            pass

        finally:
            self.players.remove(player)

    async def game_loop(self):
        while True:
            self.update(UPDATE_RATE)

            for player in list(self.players):
                try:
                    await player.send_state(self.state())
                except websockets.ConnectionClosed:
                    self.players.discard(player)

            await asyncio.sleep(UPDATE_RATE)


async def main():
    game = Game()

    async with websockets.serve(
        game.client_handler,
        "localhost",
        SOCKET_PORT,
    ):
        await game.game_loop()


asyncio.run(main())
