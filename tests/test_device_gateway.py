from fastapi.testclient import TestClient
from services.device_gateway.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "device_gateway"}

def test_discover_devices():
    response = client.get("/devices/discover")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) >= 2
    assert devices[0]["device_id"] == "dev-001"

def test_send_valid_command():
    response = client.post(
        "/devices/dev-001/command",
        json={"action": "SET_VOLUME", "value": 65}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["executed_action"] == "SET_VOLUME"
    assert data["updated_state"]["volume"] == 65

def test_invalid_volume_rejected_by_pydantic():
    response = client.post(
        "/devices/dev-001/command",
        json={"action": "SET_VOLUME", "value": 150}
    )
    assert response.status_code == 422

def test_unknown_device_returns_404():
    response = client.post(
        "/devices/dev-999/command",
        json={"action": "POWER_ON"}
    )
    assert response.status_code == 404

def test_register_and_deregister_device_lifecycle():
    reg_res = client.post(
        "/devices/register",
        json={"device_id": "dev-test-99", "name": "Bedroom Speaker", "protocol": "MiIO"}
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["device_id"] == "dev-test-99"

    dup_res = client.post(
        "/devices/register",
        json={"device_id": "dev-test-99", "name": "Bedroom Speaker", "protocol": "MiIO"}
    )
    assert dup_res.status_code == 409

    del_res = client.delete("/devices/dev-test-99")
    assert del_res.status_code == 204

    get_res = client.get("/devices/dev-test-99")
    assert get_res.status_code == 404
