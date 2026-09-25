"""Human CLI welcome, help, errors, and unchanged --json records."""

from __future__ import annotations

import json
from pathlib import Path

from azmail.airlock import classify
from azmail.cli import main


def test_bare_command_is_a_welcome(capsys):
    code = main([])
    out = capsys.readouterr().out
    assert code == 0
    assert "azmail ui" in out
    assert "azmail doctor" in out
    assert "Aziel Eliab" in out
    assert "required" not in out.lower()
    assert "THIS IS NOT" not in out


def test_help_lists_common_and_advanced(capsys):
    code = main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Common commands:" in out
    assert "Advanced commands:" in out
    assert "azmail ui" in out
    assert "mesh" in out
    assert "required: cmd" not in out
    assert "Not an MTA" not in out


def test_unknown_command_has_a_next_step(capsys):
    code = main(["bogus"])
    err = capsys.readouterr().err
    assert code == 2
    assert 'Unknown command "bogus".' in err
    assert "azmail --help" in err


def test_receive_without_sender_has_a_next_step(capsys):
    code = main(["receive"])
    err = capsys.readouterr().err
    assert code == 2
    assert "sender" in err.lower()
    assert "azmail receive --from" in err


def test_classify_json_matches_library(tmp_path: Path, capsys):
    payload = {
        "from": "alert@secure-paypal-login.tk",
        "subject": "Verify your account",
        "body_text": "Login now and send your password.",
    }
    path = tmp_path / "msg.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code = main(["classify", "--json", "--file", str(path)])
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out) == classify(payload).as_dict()


def test_classify_human_is_not_json(tmp_path: Path, capsys):
    payload = {
        "from": "alert@secure-paypal-login.tk",
        "subject": "Verify your account",
        "body_text": "Login now and send your password.",
    }
    path = tmp_path / "msg.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code = main(["classify", "--file", str(path)])
    out = capsys.readouterr().out
    assert code == 0
    assert not out.lstrip().startswith("{")
    assert "Quarantined" in out


def test_release_missing_json_shape(tmp_path: Path, capsys):
    box = tmp_path / "mailbox.json"
    code = main(["--json", "--mailbox", str(box), "release", "AM-missing"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out == {"ok": False, "error": "not in airlock", "id": "AM-missing"}


def test_release_missing_human(tmp_path: Path, capsys):
    box = tmp_path / "mailbox.json"
    code = main(["--mailbox", str(box), "release", "AM-missing"])
    err = capsys.readouterr().err
    assert code == 1
    assert "not in the airlock" in err
    assert "azmail list airlock" in err


def test_list_json_shape(tmp_path: Path, capsys):
    box = tmp_path / "mailbox.json"
    code = main(["--json", "--mailbox", str(box), "list", "inbox"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out == {"inbox": []}
