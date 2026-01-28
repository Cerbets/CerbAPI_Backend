from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ [WS] Новое подключение. Всего: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ [WS] Соединение удалено. Осталось: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        bad_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ Ошибка отправки (удаляем сокет): {e}")
                bad_connections.append(connection)

        for dead_conn in bad_connections:
            self.disconnect(dead_conn)


manager = ConnectionManager()