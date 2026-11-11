from fastapi import FastAPI
from pydantic import BaseModel

# 1. Create the main FastAPI application
app = FastAPI()

# 2. Define the shape of our data using Pydantic
class DeviceInfo(BaseModel):
    device_id: str
    name: str
    status: str

# 3. Map the URL "/health" (HTTP GET) to a Python function
@app.get("/health")
async def health_check():
    # Returning a Python dict automatically converts it into JSON!
    return {"status": "healthy"}

# 4. Map "/devices/discover" and enforce the DeviceInfo structure
@app.get("/devices/discover", response_model=list[DeviceInfo])
async def discover_devices():
    return [
        DeviceInfo(device_id="dev-001", name="Soundbar", status="online")
    ]

