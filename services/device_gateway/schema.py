from pydantic import BaseModel, Field
from typing import Optional

class DeviceInfo(BaseModel):
    device_id: str
    name: str
    protocol: str
    status: str
    power_state: str = "OFF"
    volume: int = 20

class DeviceCommand(BaseModel):
    action: str = Field(..., description="Command action: POWER_ON, POWER_OFF, or SET_VOLUME")
    value: Optional[int] = Field(None, ge=0, le=100, description="Optional numeric value (0-100) for volume")

class CommandResponse(BaseModel):
    device_id: str
    executed_action: str
    updated_state: DeviceInfo