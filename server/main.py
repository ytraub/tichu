import asyncio
import websockets

async def handler(websocket):
    async for message in websocket:
        print("Received:", message)
        await websocket.send(f"Server received: {message}")

async def main():
    async with websockets.serve(handler, "localhost", 5400):
        print("WebSocket server running on ws://localhost:5400")
        await asyncio.Future()  # run forever

asyncio.run(main())
