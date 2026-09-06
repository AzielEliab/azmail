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
#meshStrip { margin:0 18px 1rem; border:1px solid var(--line); background:#101010; border-radius:12px; padding:10px 12px; display:flex; flex-wrap:wrap; align-items:center; gap:10px 16px; font-size:.82rem; color:var(--muted); }
#meshStrip .live { color:var(--ivory); }
#meshStrip .live b { color:var(--gold); font-size:1.25rem; margin-right:6px; }
#meshStrip .rollup span { margin-right:10px; }
#meshStrip .rollup b { color:var(--gold); }
#meshStrip button { background:transparent; color:var(--gold); border:1px solid var(--gold-dim); border-radius:8px; padding:.35rem .7rem; cursor:pointer; font:inherit; }
#meshStrip button:hover { border-color:var(--gold); }
#meshProducts { flex-basis:100%; margin:0; }
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
<strong>Human UI is this page.</strong> Classify button posts <code>/v1/airlock_classify</code> (FragGate op). Door paths
<code>/v1/fraggate/list|describe|call</code> and <code>/v1/mesh/*</code> PROXY to aziel-runtime. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. No Node Gate. No auto-heal. Not anonymity.
AI / MCP path is FragGate only — no separate mail MCP:
<code>POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call</code> body <code>{"slug":"azmail","op":"airlock_classify","payload":{}}</code>.
Catalog MCP <code>mesh_*</code> · FragGate <code>slug=mesh</code>. Product-local leftover ring is <code>/v1/mesh_disable</code>.
GitHub stars ${gh.stars || 0} · forks ${gh.forks || 0} · watchers ${gh.watchers || 0}.
<a href="/count">/count</a> · <a href="/stats">/stats</a> · <a href="/v1/skill">Skill</a> · <a href="/ai">AI / FragGate</a> · <a href="/openapi.json">OpenAPI</a> · <a href="/mcp">/mcp</a> · <a href="https://github.com/AzielEliab/azmail">GitHub</a></p>
<div id="meshStrip" aria-label="Suite Live Nodes">
  <div class="live"><b id="meshLiveCount">0</b> Live Nodes</div>
  <div id="meshLine">Suite mesh: off (default). QNM-BUILD-1.0. Not an anonymity network.</div>
  <div class="rollup">live <b id="qnmLive">0</b> · locked <b id="qnmLocked">0</b> · isolated <b id="qnmIsolated">0</b></div>
  <div>No Node Gate · No auto-heal · Aziel Eliab only</div>
  <div>
    <button id="meshEnable" type="button" title="Enable suite mesh (operator bearer; default off)">Enable</button>
    <button id="meshDisable" type="button" title="Disable suite mesh (always allowed)">Disable</button>
    <button id="meshJoin" type="button" title="Join as azmail. Refused while mesh is OFF. No auto-join.">Join</button>
    <button id="meshLeave" type="button" title="Leave this node. No auto-heal.">Leave</button>
  </div>
  <p id="meshProducts" class="iso" style="margin:0">Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · not AnonBroadcast · not AZMail leftover ring</p>
</div>

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
  Independent of AZ-OS / Lumen. This page is the human UI.
  Agents use FragGate only:
  <code>POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call</code>
  <code>{"slug":"azmail",…}</code>
  — not a mail MCP on this Worker
  (<a href="https://github.com/AzielEliab/fraggate">kernel</a>).
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
    const res = await fetch("/v1/airlock_classify", { method: "POST", headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" }, body: JSON.stringify(msg) });
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
    if (view === "receive") main.innerHTML = '<h2>Receive into airlock</h2><div class="card"><label>From</label><input id="r-from" placeholder="PayPal Billing &lt;help@paypa1-verify.com&gt;"><label>Subject</label><input id="r-sub"><label>Body</label><textarea id="r-body"></textarea><label>HTML</label><textarea id="r-html"></textarea><label>Authentication-Results</label><input id="r-auth" placeholder="spf=pass; dkim=pass; dmarc=pass"><div class="row"><button class="act" id="r-go">airlock_classify</button></div><pre id="r-out"></pre></div>';
    if (view === "mesh") main.innerHTML = '<h2>Anonymous mesh (product-local leftover)</h2><div class="card"><p>AZMail leftover ring. Off by default. Easy off-switch <code>POST /v1/mesh_disable</code>. <strong>Not suite QNM</strong> (that is the Live Nodes strip + <code>/v1/mesh/*</code> PROXY). <strong>Agents:</strong> <code>POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call</code> <code>{"slug":"azmail","op":"mesh_enable|mesh_disable|broadcast|listen"}</code>. Not a separate mail MCP. This tab is leftover local flag + stubs.</p><p>enabled: <strong>' + (box.mesh.enabled ? "on" : "OFF") + '</strong></p><div class="row"><button class="act" id="m-on">mesh_enable</button><button class="ghost" id="m-off">mesh_disable</button></div><label>Broadcast</label><textarea id="m-text"></textarea><div class="row"><button class="act" id="m-send">Broadcast stub</button></div><label>Keywords (alert without identity)</label><input id="m-keys" value="' + (box.mesh.keywords || []).join(", ") + '"><div class="row"><button class="ghost" id="m-keys-set">Save keywords</button></div><pre id="m-out"></pre></div>';
    if (view === "doctor") main.innerHTML = '<h2>Doctor / verify / import-export</h2><div class="card"><div class="row"><button class="act" id="d-health">GET /v1/health</button><button class="ghost" id="d-fg">GET /v1/fraggate/list</button><button class="ghost" id="d-mesh">GET /v1/mesh</button><button class="ghost" id="d-ex">Export JSON</button><label class="ghost" style="padding:.5rem .85rem;border:1px solid var(--gold-dim);border-radius:8px;cursor:pointer;">Import JSON<input id="d-im" type="file" accept="application/json" style="display:none"></label></div><pre id="d-out"></pre></div>';
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
      document.getElementById("m-out").textContent = JSON.stringify(await fetch("/v1/mesh_enable", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }).then(function (r) { return r.json(); }), null, 2);
      render();
    }
    if (t.id === "m-off") {
      box.mesh.enabled = false; persist();
      document.getElementById("m-out").textContent = JSON.stringify(await fetch("/v1/mesh_disable", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }).then(function (r) { return r.json(); }), null, 2);
      render();
    }
    if (t.id === "m-send") {
      var text = document.getElementById("m-text").value;
      document.getElementById("m-out").textContent = JSON.stringify(await fetch("/v1/broadcast", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text: text }) }).then(function (r) { return r.json(); }), null, 2);
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
    if (t.id === "d-fg") {
      document.getElementById("d-out").textContent = JSON.stringify(await fetch("/v1/fraggate/list", { headers: { "user-agent": "Mozilla/5.0" } }).then(function (r) { return r.json(); }), null, 2);
    }
    if (t.id === "d-mesh") {
      document.getElementById("d-out").textContent = JSON.stringify(await fetch("/v1/mesh", { headers: { "user-agent": "Mozilla/5.0" } }).then(function (r) { return r.json(); }), null, 2);
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
  function meshNum() {
    for (var i = 0; i < arguments.length; i++) {
      var raw = arguments[i];
      if (raw == null || raw === "") continue;
      var n = typeof raw === "number" ? raw : Number(String(raw).replace(/,/g, ""));
      if (Number.isFinite(n) && n >= 0) return Math.floor(n);
    }
    return 0;
  }
  function unwrapMesh(j) {
    if (!j || typeof j !== "object") return {};
    if (j.result && typeof j.result === "object") return Object.assign({}, j, j.result);
    if (j.mesh && typeof j.mesh === "object") return Object.assign({}, j, j.mesh);
    return j;
  }
  function paintMesh(raw) {
    var j = unwrapMesh(raw);
    var on = j.enabled === true || j.enabled === 1 || String(j.status || "").toLowerCase() === "on";
    var r = (j.rollup && typeof j.rollup === "object") ? j.rollup : {};
    var live = on ? meshNum(r.live, j.live_nodes, j.live) : 0;
    var locked = on ? meshNum(r.locked, j.locked_nodes, j.locked) : 0;
    var isolated = on ? meshNum(r.isolated, j.isolated_nodes, j.isolated) : 0;
    document.getElementById("meshLiveCount").textContent = String(live);
    document.getElementById("qnmLive").textContent = String(live);
    document.getElementById("qnmLocked").textContent = String(locked);
    document.getElementById("qnmIsolated").textContent = String(isolated);
    var line = document.getElementById("meshLine");
    if (on) line.textContent = "Suite mesh: on · live " + live + " · locked " + locked + " · isolated " + isolated + ". Not an anonymity network.";
    else if (j.status === "unavailable" || (j.ok === false && j.error)) line.textContent = "Suite mesh: off (unavailable). QNM-BUILD-1.0. Not an anonymity network.";
    else line.textContent = "Suite mesh: off (default). QNM-BUILD-1.0. Not an anonymity network.";
    var products = j.products_present || j.products || [];
    var names = Array.isArray(products) ? products.map(function (p) { return (typeof p === "string" ? p : (p && (p.product || p.slug)) || ""); }).filter(Boolean) : [];
    var nodes = Array.isArray(j.nodes) ? j.nodes : [];
    var extra = names.length ? " · products " + names.join(", ") : (nodes.length ? " · " + nodes.length + " node labels" : "");
    document.getElementById("meshProducts").textContent = "Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · not AnonBroadcast · not AZMail leftover ring" + extra;
  }
  async function meshGet(path) {
    var r = await fetch(path, { headers: { "user-agent": "Mozilla/5.0", accept: "application/json" } });
    return r.json();
  }
  async function meshPost(path, payload) {
    var r = await fetch(path, { method: "POST", headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" }, body: JSON.stringify(payload || {}) });
    return r.json();
  }
  async function refreshMesh() {
    try {
      var status = await meshGet("/v1/mesh");
      var merged = status;
      var on = status && (status.enabled === true || (status.result && status.result.enabled === true));
      if (on) {
        try {
          var nodes = await meshGet("/v1/mesh/nodes");
          merged = Object.assign({}, unwrapMesh(status), unwrapMesh(nodes));
        } catch (e) { /* status is enough */ }
      }
      paintMesh(merged);
      var nodeId = sessionStorage.getItem("azmail_mesh_node");
      if (on && nodeId) {
        try { await meshPost("/v1/mesh/heartbeat", { node_id: nodeId }); } catch (e) { /* no auto-heal */ }
      }
    } catch (e) {
      paintMesh({ ok: false, enabled: false, status: "unavailable", error: "mesh_unavailable" });
    }
  }
  var meshEnableBtn = document.getElementById("meshEnable");
  if (meshEnableBtn) meshEnableBtn.onclick = async function () { paintMesh(await meshPost("/v1/mesh/enable", {})); refreshMesh(); };
  var meshDisableBtn = document.getElementById("meshDisable");
  if (meshDisableBtn) meshDisableBtn.onclick = async function () { sessionStorage.removeItem("azmail_mesh_node"); paintMesh(await meshPost("/v1/mesh/disable", {})); refreshMesh(); };
  var meshJoinBtn = document.getElementById("meshJoin");
  if (meshJoinBtn) meshJoinBtn.onclick = async function () {
    var j = await meshPost("/v1/mesh/join", { product: "azmail", label: "AZMail Worker" });
    var inner = unwrapMesh(j);
    var id = inner.node_id || inner.id || (inner.session && inner.session.node_id);
    if (id) sessionStorage.setItem("azmail_mesh_node", String(id));
    paintMesh(j);
    refreshMesh();
  };
  var meshLeaveBtn = document.getElementById("meshLeave");
  if (meshLeaveBtn) meshLeaveBtn.onclick = async function () {
    var id = sessionStorage.getItem("azmail_mesh_node");
    if (id) await meshPost("/v1/mesh/leave", { node_id: id });
    sessionStorage.removeItem("azmail_mesh_node");
    refreshMesh();
  };
  window.addEventListener("pagehide", function () {
    var id = sessionStorage.getItem("azmail_mesh_node");
    if (!id || typeof navigator.sendBeacon !== "function") return;
    try { navigator.sendBeacon("/v1/mesh/leave", new Blob([JSON.stringify({ node_id: id })], { type: "application/json" })); } catch (e) { /* leave expires in 5 minutes */ }
  });
  refreshMesh();
  setInterval(refreshMesh, 30000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) refreshMesh(); });
  render();
})();
</script>
</body></html>`;
}
