/** Hosted AZMail homepage: counted download + complete mail Airlock UI. */
import { LIMITATION } from "./engine.js";

const HOST = "https://azmail-download-tracker.vibelock.workers.dev";
const INSTALL_LINE = `curl -fsSL ${HOST}/install.sh | bash`;
const SIGIL = "https://www.azielcorpuslibrary.net/sigil.png";
const ASSET = "azmail-0.1.0.tar.gz";

export function homeHtml({ views, downloads, github }) {
  const v = Number(views || 0).toLocaleString("en-US");
  const n = Number(downloads || 0).toLocaleString("en-US");
  const gh = github || {};
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AZMail — Aziel Eliab</title>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"SoftwareApplication","name":"AZMail","author":{"@type":"Person","name":"Aziel Eliab"},"codeRepository":"https://github.com/AzielEliab/azmail","downloadUrl":"${HOST}/download","license":"https://www.apache.org/licenses/LICENSE-2.0","url":"${HOST}/","description":"APP 1.0 anti-phishing Mail Airlock by Aziel Eliab. Not a public MTA."}
</script>
<style>
:root { color-scheme: dark; --bg:#0b0b0b; --card:#141414; --gold:#c9a227; --gold-dim:#8a7219; --ivory:#e8e0d0; --muted:#9a927e; --line:#2a2414; --ok:#7dcf9a; }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.45 system-ui,sans-serif; background:var(--bg); color:var(--ivory); }
header { display:flex; align-items:center; gap:12px; padding:14px 18px; border-bottom:1px solid var(--line); }
header img { width:40px; height:40px; }
h1 { margin:0; font-size:1.4rem; color:var(--gold); }
.motto { color:var(--muted); font-size:.9rem; }
.banner { margin:12px 18px 0; border:1px solid #5c4a1a; background:#241c0d; color:#f0d78c; padding:.75rem 1rem; border-radius:8px; font-size:.88rem; }
.nums { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; margin:12px 18px; }
.count { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; font-size:2rem; font-weight:700; }
.count span { display:block; font-size:.9rem; font-weight:500; color:var(--muted); }
.btns { display:grid; grid-template-columns:1fr 1fr; gap:.75rem; margin:0 18px 1rem; }
@media (max-width:640px){ .btns,.nums,.layout{grid-template-columns:1fr;} }
a.btn, button.btn { display:block; text-align:center; font:inherit; font-weight:750; padding:1rem; border-radius:10px; border:0; cursor:pointer; text-decoration:none; }
a.btn.primary { background:var(--ivory); color:#0b0b0b; }
button.btn.install { background:var(--gold); color:#14110a; }
.layout { display:grid; grid-template-columns:190px 1fr; min-height:50vh; border-top:1px solid var(--line); }
nav { padding:12px; border-right:1px solid var(--line); }
nav button { display:block; width:100%; text-align:left; background:transparent; color:var(--ivory); border:1px solid transparent; padding:.5rem .65rem; border-radius:8px; margin-bottom:6px; cursor:pointer; font:inherit; }
nav button.active, nav button:hover { border-color:var(--gold-dim); color:var(--gold); }
main { padding:14px 16px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; margin-bottom:10px; }
.badge { display:inline-block; font-size:.75rem; font-weight:700; padding:.15rem .5rem; border-radius:999px; border:1px solid var(--gold-dim); color:var(--gold); }
.badge.verified { color:var(--ok); border-color:#2d6a45; }
.badge.high-risk,.badge.quarantined { color:#ffb4b4; border-color:#b54a4a; }
label { display:block; font-size:.8rem; color:var(--muted); margin:.4rem 0 .2rem; }
input, textarea { width:100%; background:#1a1a1a; color:var(--ivory); border:1px solid var(--line); border-radius:8px; padding:.5rem .6rem; font:inherit; }
textarea { min-height:80px; }
.row { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
button.act { background:var(--gold); color:#14110a; border:0; border-radius:8px; padding:.5rem .85rem; font-weight:700; cursor:pointer; }
button.ghost { background:transparent; color:var(--gold); border:1px solid var(--gold-dim); border-radius:8px; padding:.5rem .85rem; cursor:pointer; }
pre { white-space:pre-wrap; word-break:break-word; font-size:.78rem; color:#cfc6ad; }
.iso { margin:0 18px 1rem; color:#7d8696; font-size:.85rem; }
.iso a { color:#c9d4ff; }
footer { padding:12px 18px 28px; color:var(--muted); font-size:.82rem; }
footer a { color:var(--gold); }
</style>
</head>
<body>
<header>
  <img src="${SIGIL}" alt="Aziel Eliab sigil">
  <div>
    <h1>AZMail</h1>
    <div class="motto">APP 1.0 Mail Airlock. No message is trusted until verified. Author: Aziel Eliab only.</div>
  </div>
</header>
<p class="banner">${LIMITATION}</p>
<div class="nums">
  <div class="count">${v}<span>Views</span></div>
  <div class="count">${n}<span>Downloads</span></div>
</div>
<div class="btns">
  <a class="btn primary" href="/download?asset=${ASSET}">Download ${ASSET}</a>
  <button class="btn install" id="install-btn" type="button">One-click install</button>
</div>
<pre id="install-cmd" class="iso">${INSTALL_LINE}
Then run: azmail ui  →  http://127.0.0.1:8876 (this computer only). v0.1 does not send internet email.</pre>
<p class="iso">Isolated counter: Worker <code>azmail-download-tracker</code>, KV AZMAIL_DOWNLOADS. /v1 does not increment.
GitHub stars ${gh.stars || 0} · forks ${gh.forks || 0} · watchers ${gh.watchers || 0}.
<a href="/count">/count</a> · <a href="/stats">/stats</a> · <a href="/openapi.json">OpenAPI</a> · <a href="/v1/skill">Skill</a> · <a href="/ai">AI runtime</a> · <a href="https://github.com/AzielEliab/azmail">GitHub</a></p>

<div class="layout">
  <nav>
    <button class="active" data-view="inbox">Inbox</button>
    <button data-view="airlock">Airlock queue</button>
    <button data-view="compose">Compose (demo)</button>
    <button data-view="receive">Receive</button>
    <button data-view="mesh">Mesh + keywords</button>
    <button data-view="doctor">Doctor / verify</button>
  </nav>
  <main id="main"></main>
</div>
<footer>
  Independent of AZ-OS / Lumen. Mesh via <a href="https://github.com/AzielEliab/aziel-runtime">aziel-runtime</a>
  FragGate (<a href="https://github.com/AzielEliab/fraggate">kernel</a>).
  <a href="https://www.azielcorpuslibrary.net/">library</a> ·
  <a href="https://godlock.uk">godlock.uk</a> ·
  <a href="https://www.azieleliab.com">azieleliab.com</a>.
  Apache-2.0. Forks always allowed.
  Cite: Eliab, Aziel. (2026). AZMail 0.1.0 [Software].
</footer>
<script>
(function () {
  var cmd = ${JSON.stringify(INSTALL_LINE)};
  var btn = document.getElementById("install-btn");
  if (btn) btn.addEventListener("click", function () {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(cmd).then(function () { btn.textContent = "Copied — paste in Terminal, then azmail ui"; });
    }
  });

  var box = { inbox: [], airlock: [], drafts: [], mesh: { enabled: false, keywords: ["invoice", "lighthouse"] } };
  try { box = JSON.parse(localStorage.getItem("azmail-demo") || "null") || box; } catch (e) {}
  function persist() { localStorage.setItem("azmail-demo", JSON.stringify(box)); }

  async function classify(msg) {
    const res = await fetch("/v1/classify", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(msg) });
    return res.json();
  }
  function badge(b) { return '<span class="badge ' + (b || "unverified") + '">' + (b || "unverified") + "</span>"; }
  function list(items, empty) {
    if (!items.length) return "<p>" + empty + "</p>";
    return items.map(function (row, i) {
      return '<div class="card"><div>' + badge(row.badge) + " <strong>" + (row.subject || "(no subject)").replace(/</g,"&lt;") +
        "</strong></div><div>" + (row.from || "").replace(/</g,"&lt;") + "</div><div>" + (row.body_text || "").slice(0,140).replace(/</g,"&lt;") +
        "</div>" + (row.needsConfirm ? '<div class="row"><button class="act" data-rel="' + i + '">Confirm release</button></div>' : "") + "</div>";
    }).join("");
  }
  var view = "inbox";
  function render() {
    var main = document.getElementById("main");
    if (view === "inbox") main.innerHTML = "<h2>Inbox</h2>" + list(box.inbox, "No released mail. Receive into the airlock first.");
    if (view === "airlock") main.innerHTML = "<h2>Airlock — receive → isolate → analyze → classify → release</h2>" + list(box.airlock, "Queue empty.");
    if (view === "compose") main.innerHTML = '<h2>Compose (demo — does not send internet email)</h2><div class="card"><label>To</label><input id="c-to"><label>Subject</label><input id="c-sub"><label>Body</label><textarea id="c-body"></textarea><div class="row"><button class="act" id="c-go">Save local draft</button></div><pre id="c-out"></pre></div>';
    if (view === "receive") main.innerHTML = '<h2>Receive into airlock</h2><div class="card"><label>From</label><input id="r-from" placeholder="PayPal Billing &lt;help@paypa1-verify.com&gt;"><label>Subject</label><input id="r-sub"><label>Body</label><textarea id="r-body"></textarea><label>HTML</label><textarea id="r-html"></textarea><label>Authentication-Results</label><input id="r-auth" placeholder="spf=pass; dkim=pass; dmarc=pass"><div class="row"><button class="act" id="r-go">Classify + isolate</button></div><pre id="r-out"></pre></div>';
    if (view === "mesh") main.innerHTML = '<h2>Anonymous mesh</h2><div class="card"><p>Off by default. Easy off-switch. Live ops via FragGate (sibling runtime PR). This page only stores a local flag.</p><p>enabled: <strong>' + (box.mesh.enabled ? "on" : "OFF") + '</strong></p><div class="row"><button class="act" id="m-on">mesh_enable</button><button class="ghost" id="m-off">mesh_disable</button></div><label>Broadcast</label><textarea id="m-text"></textarea><div class="row"><button class="act" id="m-send">Broadcast stub</button></div><label>Keywords (alert without identity)</label><input id="m-keys" value="' + (box.mesh.keywords || []).join(", ") + '"><div class="row"><button class="ghost" id="m-keys-set">Save keywords</button></div><pre id="m-out"></pre></div>';
    if (view === "doctor") main.innerHTML = '<h2>Doctor / verify / import-export</h2><div class="card"><div class="row"><button class="act" id="d-health">GET /v1/health</button><button class="ghost" id="d-ex">Export JSON</button><label class="ghost" style="padding:.5rem .85rem;border:1px solid var(--gold-dim);border-radius:8px;cursor:pointer;">Import JSON<input id="d-im" type="file" accept="application/json" style="display:none"></label></div><pre id="d-out"></pre></div>';
  }
  document.querySelector("nav").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    document.querySelectorAll("nav button").forEach(function (x) { x.classList.toggle("active", x === b); });
    view = b.dataset.view; render();
  });
  document.getElementById("main").addEventListener("click", async function (e) {
    var t = e.target;
    if (t.dataset.rel != null) {
      var item = box.airlock.splice(Number(t.dataset.rel), 1)[0];
      if (item) { item.needsConfirm = false; box.inbox.push(item); persist(); render(); }
      return;
    }
    if (t.id === "c-go") {
      var draft = { to: document.getElementById("c-to").value, subject: document.getElementById("c-sub").value, body_text: document.getElementById("c-body").value, demo: true };
      box.drafts.push(draft); persist();
      document.getElementById("c-out").textContent = JSON.stringify({ ok: true, demo: true, note: "Not sent to the internet.", draft: draft }, null, 2);
    }
    if (t.id === "r-go") {
      var msg = { from: document.getElementById("r-from").value, subject: document.getElementById("r-sub").value, body_text: document.getElementById("r-body").value, body_html: document.getElementById("r-html").value, headers: { "Authentication-Results": document.getElementById("r-auth").value } };
      var cls = await classify(msg);
      var scrub = await fetch("/v1/scrub", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ html: msg.body_html }) }).then(function (r) { return r.json(); });
      var row = Object.assign({ badge: cls.badge, needsConfirm: !!cls.requires_confirmation }, msg, { classification: cls, scrub: scrub });
      if (cls.verdict === "release") box.inbox.push(row);
      else box.airlock.push(row);
      persist();
      document.getElementById("r-out").textContent = JSON.stringify({ classification: cls, scrub_kinds: scrub.stripped_kinds }, null, 2);
    }
    if (t.id === "m-on") {
      box.mesh.enabled = true; persist();
      document.getElementById("m-out").textContent = JSON.stringify(await fetch("/v1/mesh/enable", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }).then(function (r) { return r.json(); }), null, 2);
      render();
    }
    if (t.id === "m-off") {
      box.mesh.enabled = false; persist();
      document.getElementById("m-out").textContent = JSON.stringify(await fetch("/v1/mesh/disable", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }).then(function (r) { return r.json(); }), null, 2);
      render();
    }
    if (t.id === "m-send") {
      var text = document.getElementById("m-text").value;
      var path = box.mesh.enabled ? "/v1/mesh/broadcast" : "/v1/mesh/broadcast";
      document.getElementById("m-out").textContent = JSON.stringify(await fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: text }) }).then(function (r) { return r.json(); }), null, 2);
    }
    if (t.id === "m-keys-set") {
      box.mesh.keywords = document.getElementById("m-keys").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      persist();
      var sample = await fetch("/v1/keyword-alerts", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: "lighthouse invoice", keywords: box.mesh.keywords }) }).then(function (r) { return r.json(); });
      document.getElementById("m-out").textContent = JSON.stringify({ saved: box.mesh.keywords, sample: sample }, null, 2);
    }
    if (t.id === "d-health") {
      document.getElementById("d-out").textContent = JSON.stringify(await fetch("/v1/health").then(function (r) { return r.json(); }), null, 2);
    }
    if (t.id === "d-ex") {
      var a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([JSON.stringify(box, null, 2)], { type: "application/json" }));
      a.download = "azmail-demo.json";
      a.click();
    }
  });
  document.getElementById("main").addEventListener("change", function (e) {
    if (e.target.id === "d-im" && e.target.files[0]) {
      e.target.files[0].text().then(function (t) { box = JSON.parse(t); persist(); render(); document.getElementById("d-out").textContent = "imported"; });
    }
  });
  render();
})();
</script>
</body></html>`;
}
