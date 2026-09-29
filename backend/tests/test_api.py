import os
import uuid
os.environ["DATABASE_URL"] = "sqlite:///./test_landchain.db"
from fastapi.testclient import TestClient
from app.main import app

def test_root():
    with TestClient(app) as client:
        response=client.get("/")
        assert response.status_code==200
        assert response.json()["name"]=="LandChain API"

def test_health_shape():
    with TestClient(app) as client:
        data=client.get("/api/health").json()
        assert data["backend"]=="ok"
        assert "postgresql" in data and "blockchain" in data

def test_create_and_list_users():
    with TestClient(app) as client:
        key=uuid.uuid4().hex
        email=f"api-test-{key}@landchain.local"
        wallet="0x"+(key+uuid.uuid4().hex[:8]).lower()
        created=client.post("/api/users",json={"full_name":"API Test User","email":email,"wallet_address":wallet,"role":"Investor"})
        assert created.status_code==201
        assert created.json()["wallet_address"].lower()==wallet.lower()
        duplicate=client.post("/api/users",json={"full_name":"Duplicate","email":email,"wallet_address":"0x00000000000000000000000000000000000000a2","role":"Investor"})
        assert duplicate.status_code==409
        assert any(user["email"]==email for user in client.get("/api/users").json())
