import httpx
import pytest

from app.api_client import APIClient, APIError


def make_client(handler):
    """Create an APIClient backed by a mock transport."""
    transport = httpx.MockTransport(handler)
    client = APIClient("http://test")
    client.client = httpx.Client(base_url="http://test", transport=transport)
    return client


def test_get_filters_none_params():
    def handler(request: httpx.Request):
        # None values should be excluded from query params
        assert "missing" not in str(request.url)
        assert "key=value" in str(request.url)
        return httpx.Response(200, json=[{"id": 1}])

    client = make_client(handler)
    result = client._get("/items", key="value", missing=None)
    assert result == [{"id": 1}]


def test_get_returns_empty_list_on_empty_body():
    def handler(request: httpx.Request):
        return httpx.Response(200, content=b"")

    client = make_client(handler)
    assert client._get("/items") == []


def test_api_error_on_4xx():
    def handler(request: httpx.Request):
        return httpx.Response(404, json={"detail": "Not found"})

    client = make_client(handler)
    with pytest.raises(APIError) as exc_info:
        client._get("/missing")
    assert exc_info.value.status_code == 404
    assert "Not found" in exc_info.value.message


def test_api_error_on_connect_error():
    def handler(request: httpx.Request):
        raise httpx.ConnectError("refused")

    client = make_client(handler)
    with pytest.raises(APIError) as exc_info:
        client._get("/anything")
    assert exc_info.value.status_code == 0
    assert "Cannot connect" in exc_info.value.message


def test_api_error_on_timeout():
    def handler(request: httpx.Request):
        raise httpx.ReadTimeout("timed out")

    client = make_client(handler)
    with pytest.raises(APIError) as exc_info:
        client._get("/anything")
    assert exc_info.value.status_code == 0
    assert "timed out" in exc_info.value.message


def test_post_sends_json():
    def handler(request: httpx.Request):
        assert request.method == "POST"
        body = request.read()
        assert b'"name"' in body
        return httpx.Response(200, json={"id": 1, "name": "test"})

    client = make_client(handler)
    result = client._post("/items", json={"name": "test"})
    assert result["name"] == "test"


def test_delete():
    def handler(request: httpx.Request):
        assert request.method == "DELETE"
        return httpx.Response(204)

    client = make_client(handler)
    client._delete("/items/1")


def test_health():
    def handler(request: httpx.Request):
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok"})

    client = make_client(handler)
    assert client.health() == {"status": "ok"}
