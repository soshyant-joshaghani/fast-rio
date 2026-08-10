def test_login_superuser(client, superuser_token_headers):
    response = client.get(
        "/api/v1/base/login/me",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@example.com"
    assert body["is_superuser"] is True
