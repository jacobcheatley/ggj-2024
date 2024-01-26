from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

HTML_DIR = Path("ggj-2024/html")
STATIC_DIR = Path("ggj-2024/static")

MAX_PLAYERS = 4


class ConnectionManager:
    def __init__(self):
        self.server_websocket: WebSocket = None
        self.clients: dict[str, WebSocket] = {}

    async def connect_client(self, client_name: str, websocket: WebSocket):
        if client_name in self.clients:
            raise ValueError("Name already exists")
        if len(self.clients) >= MAX_PLAYERS:
            raise ValueError("Game full!")

        await websocket.accept()
        await websocket.send_json({"type": "message", "data": f"Welcome {client_name}"})
        await websocket.send_json({"type": "name", "data": client_name})
        await websocket.send_json({"type": "state", "data": "JOKE"})
        self.clients[client_name] = websocket

        await self.send_server({"type": "player_join", "data": client_name})
        await self.send_server({"type": "players", "data": list(self.clients.keys())})

    async def disconnect_client(self, client_name: str):
        self.clients.pop(client_name)

        await self.send_server({"type": "player_leave", "data": client_name})
        await self.send_server({"type": "players", "data": list(self.clients.keys())})

    async def connect_server(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_json({"type": "state", "data": "WAIT"})
        self.server_websocket = websocket

    def disconnect_server(self):
        pass  # IDK what to do here

    async def send_server(self, data: Any):
        await self.send(self.server_websocket, data)

    async def send(self, websocket: WebSocket, data: Any):
        await websocket.send_json(data)

    async def broadcast(self, data: Any):
        for client_name, websocket in self.clients.items():
            await websocket.send_json(data)


manager = ConnectionManager()

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
    await manager.connect_server(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Server sent {data}")
    except WebSocketDisconnect:
        manager.disconnect_server(websocket)


@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    try:
        await manager.connect_client(client_name, websocket)
    except ValueError as e:
        await websocket.accept()
        await websocket.send_json({"type": "error", "data": str(e)})
        await websocket.send_json({"type": "state", "data": "NAME"})
        await websocket.close(1000, str(e))
        return

    try:
        while True:
            data = await websocket.receive_text()
            print(f"{client_name} sent {data}")
    except WebSocketDisconnect:
        await manager.disconnect_client(client_name)
        print(f"{client_name} disconnected")
