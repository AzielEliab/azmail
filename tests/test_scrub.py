"""HTML metadata scrub."""

from azmail.scrub import scrub_html


SAMPLE = """
<html><head>
<script>alert(1)</script>
<meta http-equiv="refresh" content="0;url=https://evil.example">
</head>
<body onclick="bad()">
<img src="https://track.example/pixel.gif" width="1" height="1">
<img src="https://ok.example/photo.jpg" width="200" height="120">
<a href="javascript:steal()">x</a>
<a href="https://good.example/path?utm_source=mail&keep=1">ok</a>
<a style="display:none" href="https://hidden.example/redir">hidden</a>
<iframe src="https://ads.example"></iframe>
</body></html>
"""


def test_strips_script_pixel_handlers_hidden_redirect():
    out = scrub_html(SAMPLE)
    kinds = set(out["stripped_kinds"])
    assert "script" in kinds
    assert "tracking_pixel" in kinds
    assert "javascript_href" in kinds
    assert "hidden_redirect" in kinds
    assert "event_handler" in kinds
    assert "<script" not in out["html"].lower()
    assert "onclick" not in out["html"].lower()
    assert "utm_source" not in out["html"]
    assert "keep=1" in out["html"]
    assert "photo.jpg" in out["html"]
    assert out["changed"] is True


def test_shortener_rewritten():
    out = scrub_html('<a href="https://bit.ly/abc">x</a>')
    assert "shortener" in ",".join(out["stripped"])
    assert "azmail-isolated-shortener" in out["html"]


def test_plain_html_unchanged_enough():
    html = "<p>Hello <strong>friend</strong></p>"
    out = scrub_html(html)
    assert out["html"].strip() == html
    assert out["changed"] is False
