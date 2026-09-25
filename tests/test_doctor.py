from azmail.doctor import run_doctor


def test_doctor_passes(capsys):
    code = run_doctor(as_json=True)
    captured = capsys.readouterr().out
    assert code == 0
    assert '"ok": true' in captured.replace(" ", "").lower() or '"ok": true' in captured
    assert '"name": "version"' in captured
    assert "limitation" in captured


def test_doctor_human_is_plain(capsys):
    code = run_doctor(as_json=False)
    out = capsys.readouterr().out
    assert code == 0
    assert "Doctor passed." in out
    assert "[ok] Version" in out
    assert "THIS IS NOT" not in out
