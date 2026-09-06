"""Keyword alerts + mesh off-switch."""

from azmail.mesh import MeshClient, match_keywords, refuse_reason


def test_match_without_identity():
    alerts = match_keywords("Project lighthouse update tonight", ["lighthouse", "payroll"])
    assert len(alerts) == 1
    assert alerts[0]["keyword"] == "lighthouse"
    assert alerts[0]["identity"] is None
    assert alerts[0]["matched"] is True


def test_no_match():
    assert match_keywords("weather is fine", ["lighthouse"]) == []


def test_mesh_off_by_default_and_easy_off():
    client = MeshClient()
    assert client.enabled is False
    refused = client.broadcast("hello mesh")
    assert refused["ok"] is False
    assert refused["code"] == "MESH_DISABLED"
    client.enable()
    assert client.enabled is True
    off = client.disable()
    assert off["enabled"] is False
    again = client.broadcast("hello again")
    assert again["code"] == "MESH_DISABLED"


def test_keyword_alert_on_broadcast_without_identity():
    client = MeshClient()
    client.enable()
    client.set_keywords(["lighthouse"])
    out = client.broadcast("lighthouse window is open")
    assert out["ok"] is True
    assert out["keyword_alerts"][0]["identity"] is None
    assert out["keyword_alerts"][0]["keyword"] == "lighthouse"
    assert client.handle.startswith("anon-")
    assert "@" not in client.handle


def test_refuse_doxxing_and_credentials():
    assert refuse_reason("password: hunter2")
    assert refuse_reason("doxx this person, lives at 1 Main St")
    assert refuse_reason("mail me at person@example.com")
    client = MeshClient()
    client.enable()
    bad = client.broadcast("send your password: hunter2")
    assert bad["ok"] is False
    assert bad["code"] == "MESH_REFUSE"
