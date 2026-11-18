from fastapi import FastAPI, HTTPException
from typing import Dict, List
from services.device_gateway.schema import DeviceInfo, DeviceCommand, CommandResponse

app = FastAPI(
    title="Autonomous IoT QA & Device Gateway",
    description="Cloud-native device control and automated testing service",
    version="0.3.0",
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

# TODO (Day 4): Add POST /devices/register endpoint so new simulated IoT devices can dynamically join the gateway
