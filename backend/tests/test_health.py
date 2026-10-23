def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Bayora Isolation Lab" in data["service"]

def test_root_endpoint(client):
    response = client.get("/", headers={"accept": "application/json"})
    assert response.status_code == 200
    assert response.json()["status"] == "online"
