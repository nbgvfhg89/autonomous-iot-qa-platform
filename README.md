# Autonomous IoT QA & Device Control Platform

A cloud-native smart-home device gateway and autonomous quality-assurance platform built with **FastAPI, Docker, Qdrant RAG, and LangGraph agents**. Designed to replace local desktop testing suites with scalable REST/WebSocket control, automated CI/CD verification, and AI-driven root-cause log triage.

## Current Architecture (v0.4.0 - Week 1 Milestone)
- **Device Gateway (`services/device_gateway/`):** Asynchronous FastAPI microservice supporting device discovery (`HTTP/SSDP`, `WebSocket`, `MiIO`), dynamic registration (`201 Created` / `409 Conflict`), stateful command execution, and deregistration.
- **Data Validation (`schemas.py`):** Strict Pydantic v2 request/response contracts with automated range and type enforcement.
- **Automated Verification (`tests/`):** Pytest + FastAPI `TestClient` suite covering CRUD lifecycles and edge-case HTTP error codes.

## Quickstart (Local Development)
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the FastAPI server
uvicorn services.device_gateway.main:app --reload

# 4. Run automated test suite
pytest -v
```
Open `http://127.0.0` to explore the interactive Swagger API documentation.

## Roadmap
- [x] **Week 1:** FastAPI Device Gateway, Pydantic Schemas & Pytest CRUD Suite
- [ ] **Week 2:** Real-Time WebSocket Telemetry Stream & Event Logging
- [ ] **Week 3:** PostgreSQL Persistence & Redis State Caching
- [ ] **Week 4:** Multi-Container Docker Compose & AWS Deployment
