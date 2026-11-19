from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from services.device_gateway.schemas import (
    CommandResponse,
    DeviceCommand,
    DeviceInfo,
    DeviceRegisterRequest,
)
from services.device_gateway.ws_manager import TelemetryConnectionManager

app = FastAPI(
    title="Autonomous IoT QA & Device Gateway",
    description="Cloud-native device control and automated testing service",
    version="0.5.0",
)

manager = TelemetryConnectionManager()

DEVICE_REGISTRY: Dict[str, DeviceInfo] = {
    "dev-001": DeviceInfo(device_id="dev-001", name="Living Room Soundbar", protocol="HTTP/SSDP", status="online"),
    "dev-002": DeviceInfo(device_id="dev-002", name="Smart TV Hub", protocol="WebSocket", status="online"),
}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "device_gateway"}


@app.get("/devices/discover", response_model=List[DeviceInfo])
async def discover_devices():
    return list(DEVICE_REGISTRY.values())


@app.post("/devices/register", response_model=DeviceInfo, status_code=status.HTTP_201_CREATED)
async def register_device(payload: DeviceRegisterRequest):
    if payload.device_id in DEVICE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Device '{payload.device_id}' is already registered",
        )

    new_device = DeviceInfo(
        device_id=payload.device_id,
        name=payload.name,
        protocol=payload.protocol,
    )
    DEVICE_REGISTRY[payload.device_id] = new_device
    await manager.broadcast_event({
        "event": "DEVICE_REGISTERED",
        "device_id": payload.device_id,
        "protocol": payload.protocol,
    })
    return new_device


@app.get("/devices/{device_id}", response_model=DeviceInfo)
async def get_device_status(device_id: str):
    if device_id not in DEVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return DEVICE_REGISTRY[device_id]


@app.post("/devices/{device_id}/command", response_model=CommandResponse)
async def send_device_command(device_id: str, command: DeviceCommand):
    if device_id not in DEVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    device = DEVICE_REGISTRY[device_id]
    action = command.action.upper()

    if action == "POWER_ON":
        device.power_state = "ON"
    elif action == "POWER_OFF":
        device.power_state = "OFF"
    elif action == "SET_VOLUME":
        if command.value is None:
            raise HTTPException(status_code=400, detail="SET_VOLUME requires a 'value' between 0 and 100")
        device.volume = command.value
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported command action: {command.action}")

    await manager.broadcast_event({
        "event": "COMMAND_EXECUTED",
        "device_id": device_id,
        "action": action,
        "power_state": device.power_state,
        "volume": device.volume,
    })

    return CommandResponse(
        device_id=device_id,
        executed_action=action,
        updated_state=device,
    )


@app.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_device(device_id: str):
    if device_id not in DEVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    del DEVICE_REGISTRY[device_id]
    await manager.broadcast_event({
        "event": "DEVICE_DEREGISTERED",
        "device_id": device_id,
    })
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/telemetry/history", response_model=List[Dict[str, Any]])
async def get_telemetry_history(
    device_id: Optional[str] = Query(None, description="Filter events by device ID"),
    limit: int = Query(20, ge=1, le=100, description="Max events to return"),
):
    return manager.get_history(device_id=device_id, limit=limit)


@app.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if message.strip().lower() == "ping":
                await websocket.send_json({"event": "PONG", "status": "connected"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
