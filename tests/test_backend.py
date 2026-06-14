import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)

def test_health_check():
    """Smoke test: check that health check responds correctly."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "orchestrator" in data["agents"]

def test_list_equipment():
    """Smoke test: verify list of available equipment ids and types."""
    response = client.get("/equipment")
    assert response.status_code == 200
    data = response.json()
    assert "equipment_ids" in data
    assert "equipment_types" in data
    assert "BF-001" in data["equipment_ids"]

def test_predictions():
    """Unit test: check predictions retrieval matches sensor telemetry metrics."""
    response = client.get("/predictions")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "total_equipment" in data
    assert len(data["predictions"]) > 0

def test_service_overdue():
    """Unit test: check service overdue schedules."""
    response = client.get("/service-overdue")
    assert response.status_code == 200
    data = response.json()
    assert "overdue" in data
    assert "total_overdue" in data
    assert "total_ok" in data

def test_plant_summary():
    """Unit test: check plant summary KPIs."""
    response = client.get("/summary")
    assert response.status_code == 200
    data = response.json()
    assert "plant_name" in data
    assert "total_equipment" in data
    assert data["total_equipment"] == 9

def test_guide_assistant_fallback():
    """Unit test: check guide endpoint handles custom inputs and responses."""
    # Test request
    response = client.post("/guide", json={
        "query": "How do I troubleshoot conveyor belt wear?",
        "chat_history": []
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0
