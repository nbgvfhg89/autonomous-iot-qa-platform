from fastapi import FastAPI, HTTPException, Response, status
from typing import Dict, List
from services.device_gateway.schemas import (
    DeviceRegisterRequest,
    DeviceInfo,
    DeviceCommand,
    CommandResponse,
)

app = FastAPI(
    title="Autonomous IoT QA & Device Gateway",
    description="Cloud-native device control and automated testing service",
    version="0.4.0",
)

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
    return Response(status_code=status.HTTP_204_NO_CONTENT)
