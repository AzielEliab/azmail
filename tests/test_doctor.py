from azmail.doctor import run_doctor


def test_doctor_passes(capsys):
    code = run_doctor(as_json=True)
    captured = capsys.readouterr().out
    assert code == 0
    assert '"ok": true' in captured.replace(" ", "").lower() or '"ok": true' in captured
