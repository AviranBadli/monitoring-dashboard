"""Tests for resource endpoints"""


def test_create_cloud(client):
    """Test creating a cloud provider"""
    response = client.post(
        "/api/v1/resources/clouds",
        json={"name": "AWS"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AWS"


def test_list_clouds(client):
    """Test listing clouds"""
    # Create a cloud first
    client.post("/api/v1/resources/clouds", json={"name": "AWS"})

    # List clouds
    response = client.get("/api/v1/resources/clouds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "AWS"


def test_create_team(client):
    """Test creating a team"""
    response = client.post(
        "/api/v1/resources/teams",
        json={
            "name": "ML Platform",
            "account_id": "ACC-001",
            "account_name": "ML Platform Account",
            "cost_center": "CC-1234",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ML Platform"
    assert data["account_id"] == "ACC-001"
    assert data["account_name"] == "ML Platform Account"
    assert data["cost_center"] == "CC-1234"


def test_create_team_without_optional_fields(client):
    """Test creating a team without optional account fields"""
    response = client.post(
        "/api/v1/resources/teams",
        json={"name": "Data Science"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Data Science"
    assert data["account_id"] is None
    assert data["account_name"] is None
    assert data["cost_center"] is None
