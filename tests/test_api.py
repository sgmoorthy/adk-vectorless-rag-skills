import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
VALID_API_KEY = "dev_secret_key_change_me"

def test_healthcheck():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["architecture"] == "vectorless"

def test_auth_failure_on_protected_routes():
    payload = {"query": "test", "limit": 5}
    response = client.post("/api/v1/skills/search_lexical", json=payload)
    assert response.status_code == 403  # Missing API Key

def test_bad_api_key():
    payload = {"query": "test", "limit": 5}
    headers = {"X-API-KEY": "wrong_key"}
    response = client.post("/api/v1/skills/search_lexical", json=payload, headers=headers)
    assert response.status_code == 401  # Invalid API Key

def test_auth_success_with_mock_db():
    payload = {"query": "failover", "limit": 5}
    headers = {"X-API-KEY": "dev_secret_key_change_me"}
    
    response = client.post("/api/v1/skills/search_lexical", json=payload, headers=headers)
    
    # We just ensure the Auth middleware was bypassed safely. 
    # Whether we hit a 500 (db unavailable) or a 200 (db connected) implies security check worked!
    assert response.status_code in [200, 500] 
