from azmail.reputation import lookalike, reputation
from azmail.source_auth import advise_source_auth, parse_spf_record


def test_lookalike_leet():
    hit = lookalike("paypa1-verify.com")
    assert hit["lookalike"] is True
    brands = {m["brand"] for m in hit["matches"]}
    assert "paypal" in brands


def test_known_phish_list():
    rep = reputation("secure-paypal-login.tk")
    assert rep["known_phish"] is True
    assert rep["risk"] >= 80


def test_spf_parser():
    rec = parse_spf_record("v=spf1 include:_spf.google.com -all")
    assert rec["ok"] is True
    assert rec["qualifier_all"] == "-"


def test_auth_results_advisory():
    out = advise_source_auth(
        {"Authentication-Results": "mx; spf=pass; dkim=fail; dmarc=pass"}
    )
    assert out["advisory"] is True
    assert out["authentication_results"]["spf"] == "pass"
    assert out["authentication_results"]["dkim"] == "fail"
    assert out["verdict"] == "fail"
