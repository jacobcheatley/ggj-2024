from http import client
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

STATIC_DIR = Path("ggj-2024/static")
with open(STATIC_DIR / "client.html") as f:
    CLIENT_HTML = f.read()
with open(STATIC_DIR / "server.html") as f:
    SERVER_HTML = f.read()


class ConnectionManager:
    def __init__(self):
        self.server_websocket: WebSocket = None
        self.clients: dict[str, WebSocket] = {}

    async def connect_server(self, websocket: WebSocket):
        await websocket.accept()
        self.server_websocket = websocket

    async def connect_client(self, websocket: WebSocket, client_name: str):
        if client_name in self.clients:
            raise ValueError("Client already exists")
        await websocket.accept()
        self.clients[client_name] = websocket

    def disconnect_client(self, client_name: str):
        self.clients.pop(client_name)

    def disconnect_server(self):
        pass  # IDK what to do here

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for client_name, websocket in self.clients.items():
            await websocket.send_text(message)


manager = ConnectionManager()

app = FastAPI()


@app.get("/")
async def get():
    return HTMLResponse(CLIENT_HTML)


@app.get("/server")
async def get_server():
    return HTMLResponse(SERVER_HTML)


@app.websocket("/ws/server")
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
    await manager.connect_client(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"{client_name} sent {data}")
    except WebSocketDisconnect:
        manager.disconnect_client(client_name)
        print(f"{client_name} disconnected")
