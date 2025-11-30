import os


def get_client():
    # Use in-memory sqlite for tests
    os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    # Import after env is set so engine is created with sqlite
    from app.main import app  # noqa: WPS433
    from fastapi.testclient import TestClient  # noqa: WPS433
    return TestClient(app)


def test_root_ok():
    client = get_client()
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data


def test_create_and_list_run():
    client = get_client()
    payload = {
        "date": "2025-01-01",
        "start_time": "07:00",
        "title": "Test Run",
        "notes": "",
        "distance_mi": 5.0,
        "duration": "00:40:00",
        "run_type": "easy",
    }
    cr = client.post("/runs/", json=payload)
    assert cr.status_code == 200, cr.text
    run = cr.json()
    assert run["pace"].endswith("/mi")

    # list within range
    lr = client.get("/runs/", params={"start_date": "2024-12-30", "end_date": "2025-01-02"})
    assert lr.status_code == 200
    arr = lr.json()
    assert any(r["title"] == "Test Run" for r in arr)

