from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from comedy_court.lib.king import King

HTML_DIR = Path("comedy_court/html")
STATIC_DIR = Path("comedy_court/static")
AI_CONFIG_DIR = Path("ai_config")

MAX_PLAYERS = 2


class ConnectionManager:
    def __init__(self):
        self.server_websocket: WebSocket = None
        self.client_websockets: dict[str, WebSocket] = {}

    async def connect_client(self, client_name: str, websocket: WebSocket):
        self.client_websockets[client_name] = websocket
        await websocket.accept()
        await websocket.send_json({"type": "debug", "data": "Connected"})

    async def disconnect_client(self, client_name: str):
        self.client_websockets.pop(client_name)

    async def connect_server(self, websocket: WebSocket):
        self.server_websocket = websocket
        await websocket.accept()
        await websocket.send_json({"type": "debug", "data": "Connected"})

    def disconnect_server(self):
        pass  # IDK what to do here

    async def send_client(self, client_name: str, data: Any):
        await self._send(self.client_websockets[client_name], data)

    async def send_server(self, data: Any):
        await self._send(self.server_websocket, data)

    async def _send(self, websocket: WebSocket, data: Any):
        await websocket.send_json(data)

    async def broadcast(self, data: Any):
        for client_name, websocket in self.client_websockets.items():
            await websocket.send_json(data)

    def is_player_connected(self, client_name: str):
        return client_name in self.client_websockets


class Player:
    def __init__(self, name: str, color: str | None = None) -> None:
        self.name = name
        self.color = color


class Joke:
    def __init__(self, name: str, joke_text: str) -> None:
        self.name = name
        self.joke_text = joke_text

        self.joke_audio = None
        self.response_text = None
        self.response_audio = None
        self.relevance = None
        self.funniness = None
        self.points = None
        self.processed = False

    async def process(self, king: King, callback: Any):
        response = king.grade_joke(self.name, self.joke_text)
        self.response_text = response["response_text"]
        self.relevance = response["relevance"]
        self.funniness = response["funniness"]
        self.points = response["points"]

        self.joke_audio = "placeholder.mp3"  # TODO
        self.response_audio = "placeholder.mp3"  # TODO

        self.processed = True
        await callback(self)

    def to_dict(self):
        return self.__dict__


class Game:
    def __init__(self, connection: ConnectionManager, king: King) -> None:
        self.connection = connection
        self.king = king

        self.server_state = "INIT"
        self.players: dict[str, Player] = {}
        self.player_jokes: dict[str, Joke] = {}

    async def connect_server(self, websocket: WebSocket):
        await self.connection.connect_server(websocket)
        await websocket.send_json({"type": "state", "data": "WAIT_FOR_PLAYERS"})

    async def send_player(self, name: str, data: Any):
        await self.connection.send_client(name, data)

    async def send_server(self, data: Any):
        await self.connection.send_server(data)

    async def player_join(self, client_name: str, websocket: WebSocket):
        # if self.server_state != "WAITING_FOR_PLAYERS":
        #     raise ValueError("Game already in progress!")
        if len(self.players) >= MAX_PLAYERS:
            raise ValueError("Game full!")
        if client_name in self.players and self.connection.is_player_connected(client_name):
            raise ValueError("Name already exists")

        await self.connection.connect_client(client_name, websocket)
        self.players[client_name] = Player(client_name, "red")

        await self.connection.send_client(client_name, {"type": "message", "data": f"Welcome {client_name}"})
        await self.connection.send_client(client_name, {"type": "name", "data": client_name})
        await self.connection.send_client(client_name, {"type": "state", "data": "WAIT"})

        await self.send_server({"type": "player_join", "data": client_name})
        await self.send_server({"type": "players", "data": list(self.players.keys())})

        if len(self.players) >= MAX_PLAYERS:
            await self.goto_game_start()

    async def player_leave(self, client_name: str):
        await self.connection.disconnect_client(client_name)

        await self.send_server({"type": "player_leave", "data": client_name})
        await self.send_server({"type": "players", "data": list(self.players.keys())})

    async def process_server(self, data: dict[str, Any]):
        match data:
            case {"type": "state_set", "data": state}:
                self.server_state = state
                # match state:
                #     case "ASK_FOR_JOKE":
                #         await self.goto_ask_for_jokes()
            case {"type": "start"}:
                await self.goto_game_start()
            case {"type": "finished_start"}:
                await self.goto_ask_for_jokes()
            case {"type": "skip"}:
                await self.goto_tell_jokes()

    async def goto_game_start(self):
        await self.connection.send_server({"type": "state", "data": "START_GAME"})

    async def goto_ask_for_jokes(self):
        await self.connection.send_server({"type": "set_theme", "data": self.king.theme})
        await self.connection.send_server({"type": "state", "data": "ASK_FOR_JOKES"})
        await self.connection.broadcast({"type": "state", "data": "JOKE"})

    async def goto_tell_jokes(self):
        await self.connection.send_server(
            {"type": "set_jokes", "data": {k: v.to_dict() for k, v in self.player_jokes.items()}}
        )
        await self.connection.send_server({"type": "state", "data": "TELL_JOKES"})

    async def on_processed_joke(self, joke: Joke):
        self.player_jokes[joke.name] = joke
        if len(self.player_jokes) == len(self.players):
            await self.goto_tell_jokes()

    async def process_player(self, name: str, data: dict[str, Any]):
        player = self.players[name]
        match data:
            case {"type": "joke", "data": joke_text}:
                print(f"{name} told joke {joke_text}")
                await self.connection.send_server({"type": "submitted_joke", "data": {"player": player.name}})
                await Joke(name, joke_text).process(self.king, self.on_processed_joke)


king = King(AI_CONFIG_DIR)
connection = ConnectionManager()
game = Game(connection, king)
app = FastAPI()


@app.get("/")
async def get():
    with open(HTML_DIR / "client.html") as f:
        return HTMLResponse(f.read())


@app.get("/server")
async def get_server():
    with open(HTML_DIR / "server.html") as f:
        return HTMLResponse(f.read())


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.websocket("/ws_server")
async def server_websocket_endpoint(websocket: WebSocket):
    await game.connect_server(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Server sent {data}")
            await game.process_server(data)

    except WebSocketDisconnect:
        connection.disconnect_server()
        print("Server disconnected")


@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    try:
        # await connection.connect_client(client_name, websocket)
        await game.player_join(client_name, websocket)
    except ValueError as e:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": str(e)})
        await websocket.send_json({"type": "state", "data": "NAME"})
        await websocket.close(1000, str(e))
        return

    try:
        while True:
            data = await websocket.receive_json()
            print(f"{client_name} sent {data}")
            await game.process_player(client_name, data)

    except WebSocketDisconnect:
        await game.player_leave(client_name)
        print(f"{client_name} disconnected")
