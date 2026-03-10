import pytest

import app as status_app


@pytest.fixture()
def client():
    status_app.app.testing = True
    return status_app.app.test_client()


def test_index_response_structure(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.is_json
    assert response.mimetype == "application/json"

    data = response.get_json()
    for key in ["client", "server", "request", "environment", "diagnostics"]:
        assert key in data

    assert "ip_address" in data["client"]

    server = data["server"]
    for key in [
        "hostname",
        "ip_address",
        "datetime_utc",
        "node_id",
        "system_load_avg",
        "memory_usage",
    ]:
        assert key in server
    _assert_system_load(server["system_load_avg"])
    _assert_memory_usage(server["memory_usage"])

    request = data["request"]
    assert request["method"] == "GET"
    assert request["path"] == "/"
    assert isinstance(request["arguments"], dict)
    assert isinstance(request["headers"], dict)

    environment = data["environment"]
    assert isinstance(environment.get("python_version"), str)
    assert isinstance(environment.get("system"), str)

    diagnostics = data["diagnostics"]
    duration = diagnostics.get("request_processing_duration_ms")
    assert isinstance(duration, (int, float))
    assert duration >= 0


def test_forwarded_for_header(client):
    response = client.get("/", headers={"X-Forwarded-For": "203.0.113.10"})
    data = response.get_json()
    assert data["client"]["ip_address"] == "203.0.113.10"


def test_query_args_reflected(client):
    response = client.get("/?foo=bar&baz=1")
    data = response.get_json()
    args = data["request"]["arguments"]
    assert args["foo"] == "bar"
    assert args["baz"] == "1"


def _assert_system_load(system_load):
    if isinstance(system_load, dict):
        for key in ["1_min", "5_min", "15_min"]:
            assert key in system_load
            assert isinstance(system_load[key], (int, float))
    else:
        assert isinstance(system_load, str)


def _assert_memory_usage(memory_usage):
    if isinstance(memory_usage, dict):
        for key in ["total_mb", "available_mb", "used_mb", "usage_percent"]:
            assert key in memory_usage
            assert isinstance(memory_usage[key], (int, float))
    else:
        assert isinstance(memory_usage, str)
