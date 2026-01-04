from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_shorten():
    response = client.post(
        "/shorten",
        json={
            "long_url": "https://example.com",
        },
    )
    assert response.status_code == 200
    assert "short_code" in response.json()
