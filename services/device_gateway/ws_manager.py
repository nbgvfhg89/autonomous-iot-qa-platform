from collections import deque
from datetime import datetime, timezone
from fastapi import WebSocket
from typing import Any, Deque, Dict, List, Optional


class TelemetryConnectionManager:
    def __init__(self, max_history: int = 100):
        self.active_connections: List[WebSocket] = []
        self.event_history: Deque[Dict[str, Any]] = deque(maxlen=max_history)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event: Dict[str, Any]):
        enriched_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        self.event_history.append(enriched_event)

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(enriched_event)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    def get_history(self, device_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        events = list(self.event_history)
        if device_id:
            events = [e for e in events if e.get("device_id") == device_id]
        return events[-limit:]
