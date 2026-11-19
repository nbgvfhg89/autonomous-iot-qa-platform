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
        json={"action": "SET_VOLUME", "value": 65},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["executed_action"] == "SET_VOLUME"
    assert data["updated_state"]["volume"] == 65


def test_invalid_volume_rejected_by_pydantic():
    response = client.post(
        "/devices/dev-001/command",
        json={"action": "SET_VOLUME", "value": 150},
    )
    assert response.status_code == 422


def test_unknown_device_returns_404():
    response = client.post(
        "/devices/dev-999/command",
        json={"action": "POWER_ON"},
    )
    assert response.status_code == 404


def test_register_and_deregister_device_lifecycle():
    reg_res = client.post(
        "/devices/register",
        json={"device_id": "dev-test-99", "name": "Bedroom Speaker", "protocol": "MiIO"},
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["device_id"] == "dev-test-99"

    dup_res = client.post(
        "/devices/register",
        json={"device_id": "dev-test-99", "name": "Bedroom Speaker", "protocol": "MiIO"},
    )
    assert dup_res.status_code == 409

    del_res = client.delete("/devices/dev-test-99")
    assert del_res.status_code == 204

    get_res = client.get("/devices/dev-test-99")
    assert get_res.status_code == 404


def test_websocket_ping_pong():
    with client.websocket_connect("/ws/telemetry") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data == {"event": "PONG", "status": "connected"}


def test_websocket_receives_live_command_broadcast():
    with client.websocket_connect("/ws/telemetry") as websocket:
        client.post("/devices/dev-002/command", json={"action": "POWER_ON"})
        event = websocket.receive_json()
        assert event["event"] == "COMMAND_EXECUTED"
        assert event["device_id"] == "dev-002"
        assert event["action"] == "POWER_ON"
        assert event["power_state"] == "ON"
        assert "timestamp" in event


def test_telemetry_history_endpoint_and_filtering():
    client.post("/devices/dev-001/command", json={"action": "POWER_ON"})
    client.post("/devices/dev-002/command", json={"action": "SET_VOLUME", "value": 40})

    # Verify general history returns logged events
    all_res = client.get("/telemetry/history?limit=10")
    assert all_res.status_code == 200
    events = all_res.json()
    assert len(events) >= 2

    # Verify device_id filtering returns only dev-002 events
    filtered_res = client.get("/telemetry/history?device_id=dev-002&limit=5")
    assert filtered_res.status_code == 200
    filtered_events = filtered_res.json()
    assert len(filtered_events) >= 1
    assert all(e["device_id"] == "dev-002" for e in filtered_events)
