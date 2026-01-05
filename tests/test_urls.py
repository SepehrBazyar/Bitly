def test_shorten(client):
    response = client.post("/shorten", json={"long_url": "https://example.com/very-long-url"})
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    short_code = data["short_code"]

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"] == "https://example.com/very-long-url"

    stats_response = client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    assert stats_response.json()["visit_count"] >= 1
