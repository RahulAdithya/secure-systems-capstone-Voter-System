from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_route_requires_auth():
    r = client.get("/admin/ballots")
    assert r.status_code == 401


def test_admin_route_forbids_voter():
    r = client.get("/admin/ballots", headers={"Authorization": "Bearer voter-token"})
    assert r.status_code == 403


def test_admin_route_allows_admin():
    r = client.get("/admin/ballots", headers={"Authorization": "Bearer admin-token"})
    assert r.status_code == 200
    j = r.json()
    assert "ballots" in j and isinstance(j["ballots"], list)
