def test_health_check(client):
    response = client.get("/api/v1/utils/health-check/")
    assert response.status_code == 200
    assert response.json() is True


def test_sample_app(client):
    response = client.get("/api/v1/sample/")
    assert response.status_code == 200
    assert "message" in response.json()
