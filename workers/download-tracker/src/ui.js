/** Hosted AZMail homepage: counted download + mail Airlock UI. */
const HOST = "https://azmail-download-tracker.vibelock.workers.dev";
const INSTALL_LINE = `curl -fsSL ${HOST}/install.sh | bash`;
const SIGIL = "https://www.azielcorpuslibrary.net/sigil.png";
const ASSET = "azmail-0.1.0.tar.gz";

export function homeHtml({ views, downloads, github }) {
  const v = Number(views || 0).toLocaleString("en-US");
  const n = Number(downloads || 0).toLocaleString("en-US");
  const gh = github || {};
  const stars = Number(gh.stars || 0).toLocaleString("en-US");
  const forks = Number(gh.forks || 0).toLocaleString("en-US");
  const watchers = Number(gh.watchers || 0).toLocaleString("en-US");
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AZMail — Aziel Eliab</title>
<meta name="description" content="AZMail is a Mail Airlock. Download the package, or hold and release a message on this page.">
<meta name="author" content="Aziel Eliab">
<link rel="icon" href="${SIGIL}">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"SoftwareApplication","name":"AZMail","author":{"@type":"Person","name":"Aziel Eliab"},"codeRepository":"https://github.com/AzielEliab/azmail","downloadUrl":"${HOST}/download","license":"https://www.apache.org/licenses/LICENSE-2.0","url":"${HOST}/","description":"APP 1.0 Mail Airlock by Aziel Eliab. Hold a message, then release it on this computer."}
</script>
<style>
:root {
  color-scheme: dark;
  --bg: #0c0b0a;
  --text: #f4efe6;
  --muted: #c9c0b0;
  --panel: #161411;
  --line: #6f675b;
  --gold: #e6c35c;
  --gold-dim: #c9a227;
  --ok: #8fd9a8;
  --risk: #ffc1c1;
  --focus: #ffe08a;
  --input: #100e0c;
  --code: #e7dcc8;
  --link: #f0e2b8;
  --btn-bg: #f4efe4;
  --btn-fg: #14110a;
}
@media (prefers-color-scheme: dark) {
  :root { color-scheme: dark; }
}
@media (prefers-color-scheme: light) {
  :root {
    color-scheme: light;
    --bg: #f6f3ec;
    --text: #1c1914;
    --muted: #4a4338;
    --panel: #fffcf7;
    --line: #6f675c;
    --gold: #6b5010;
    --gold-dim: #6b5010;
    --ok: #0d5c2e;
    --risk: #8d1d1d;
    --focus: #1c1914;
    --input: #ffffff;
    --code: #3f3428;
    --link: #5c4a16;
    --btn-bg: #1c1914;
    --btn-fg: #f6f3ec;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); }
body { font: 16px/1.5 system-ui, "Segoe UI", sans-serif; overflow-wrap: anywhere; }
img { max-width: 100%; }
a { color: var(--link); }
code, pre, .mono { font-family: ui-monospace, Menlo, Consolas, monospace; }
.skip { position: absolute; left: -999px; top: 0; }
.skip:focus {
  left: 1rem; top: 1rem; z-index: 5;
  background: var(--btn-bg); color: var(--btn-fg);
  padding: .5rem .8rem; text-decoration: none; border-radius: 8px;
}
a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible, summary:focus-visible, label.ghost:focus-within {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}
.wrap { max-width: 58rem; margin: 0 auto; padding: 1.35rem 1.15rem 2.8rem; }
.brandrow { display: flex; align-items: center; gap: 12px; margin: 0 0 12px; }
.brandmark { width: 40px; height: 40px; border-radius: 10px; object-fit: cover; flex: 0 0 auto; box-shadow: 0 0 0 1px var(--line); }
.stamp { margin: 0; color: var(--gold); font-size: .88rem; letter-spacing: .02em; }
h1 { font-size: 2rem; letter-spacing: .02em; margin: 0 0 .2rem; line-height: 1.15; font-weight: 650; }
.motto { color: var(--gold); font-style: italic; margin: 0 0 .7rem; font-size: 1.08rem; }
.lede { color: var(--muted); margin: 0 0 1rem; max-width: 46rem; }
.scope { color: var(--muted); margin: 0 0 1rem; max-width: 46rem; font-size: .95rem; }
a.btn, button.btn {
  font: 700 .95rem/1.1 ui-monospace, Menlo, Consolas, monospace;
  letter-spacing: .03em;
  border-radius: 9px;
  cursor: pointer;
  text-decoration: none;
}
a.btn.block.primary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 3.4rem;
  margin: 0 0 .75rem;
  padding: 1.05rem 1.2rem;
  border: 1px solid transparent;
  background: var(--btn-bg);
  color: var(--btn-fg);
  text-align: center;
  font-size: 1.25rem;
}
a.btn.block.primary:hover { filter: brightness(1.06); }
.asset-note { color: var(--muted); font-size: .95rem; margin: 0 0 .35rem; }
.asset-note strong { color: var(--text); font-variant-numeric: tabular-nums; font-weight: 700; }
.features {
  display: grid;
  grid-template-columns: 1fr;
  gap: .55rem 1.2rem;
  margin: .9rem 0 1.15rem;
  padding: 0;
  list-style: none;
  max-width: 46rem;
}
.features li { margin: 0; padding-left: 1rem; position: relative; }
.features li::before {
  content: "";
  position: absolute;
  left: 0;
  top: .55em;
  width: .4rem;
  height: .4rem;
  border-radius: 50%;
  background: var(--gold);
}
.install-row { margin: 0 0 .75rem; }
button.btn.install {
  width: 100%;
  min-height: 2.75rem;
  padding: .7rem 1rem;
  background: transparent;
  color: var(--text);
  border: 1px solid var(--line);
}
button.btn.install:hover { background: var(--panel); }
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  background: var(--input);
  color: var(--code);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: .75rem .9rem;
  font-size: .82rem;
  max-width: 100%;
  margin: 0 0 .7rem;
}
.hint { color: var(--muted); font-size: .92rem; margin: 0; }
.kicker {
  display: block;
  font-size: .68rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: .15rem;
  font-family: ui-monospace, Menlo, Consolas, monospace;
}
.workspace, #meshStrip {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel);
  margin: 1.15rem 0 0;
}
.workspace { padding: 1.1rem 1.1rem 1.2rem; }
.workspace h2 { font-size: 1.12rem; margin: 0 0 .45rem; letter-spacing: .02em; font-weight: 650; }
.layout { display: grid; grid-template-columns: 1fr; min-width: 0; border-top: 1px solid var(--line); margin-top: .4rem; }
nav { display: flex; flex-wrap: wrap; gap: .4rem; padding: .75rem 0 .2rem; min-width: 0; }
nav button {
  width: auto;
  max-width: 100%;
  text-align: left;
  background: transparent;
  color: var(--text);
  border: 1px solid transparent;
  padding: .55rem .7rem;
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  min-height: 2.75rem;
}
nav button.active, nav button:hover { border-color: var(--gold-dim); color: var(--gold); background: var(--bg); }
main { padding: .8rem 0 .2rem; min-width: 0; }
main h2 { font-size: 1.15rem; margin: .2rem 0 .6rem; }
.card { background: var(--bg); border: 1px solid var(--line); border-radius: 12px; padding: 12px; margin-bottom: 10px; }
.badge { display: inline-block; font-size: .75rem; font-weight: 700; padding: .15rem .5rem; border-radius: 999px; border: 1px solid var(--gold-dim); color: var(--gold); }
.badge.verified { color: var(--ok); border-color: var(--ok); }
.badge.high-risk, .badge.quarantined { color: var(--risk); border-color: var(--risk); }
label { display: block; font-size: .8rem; color: var(--muted); margin: .4rem 0 .2rem; }
input, textarea, select {
  width: 100%;
  max-width: 100%;
  background: var(--input);
  color: var(--text);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: .5rem .6rem;
  font: inherit;
}
textarea { min-height: 80px; }
::placeholder { color: var(--muted); opacity: 1; }
.row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
button.act {
  background: var(--gold);
  color: var(--btn-fg);
  border: 0;
  border-radius: 8px;
  padding: .55rem .85rem;
  font-weight: 700;
  cursor: pointer;
  min-height: 2.75rem;
}
button.ghost, label.ghost {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: .55rem .85rem;
  cursor: pointer;
  min-height: 2.75rem;
}
label.ghost { display: inline-block; }
#meshStrip {
  padding: .85rem 1rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: .7rem 1rem;
  font-size: .88rem;
  color: var(--muted);
}
#meshStrip .live { color: var(--text); }
#meshStrip .live b { color: var(--gold); font-size: 1.35rem; margin-right: .35rem; }
#meshStrip .rollup b { color: var(--gold); }
#meshStrip button {
  font: 700 .78rem/1 ui-monospace, Menlo, Consolas, monospace;
  min-height: 2.75rem;
  padding: 0 .75rem;
  border-radius: 8px;
  background: transparent;
  color: var(--text);
  border: 1px solid var(--line);
  cursor: pointer;
}
#meshStrip button:hover { background: var(--bg); color: var(--gold); border-color: var(--gold-dim); }
#meshProducts { flex-basis: 100%; margin: 0; }
footer.quiet { color: var(--muted); font-size: .9rem; margin-top: 1.25rem; }
footer.quiet p { margin: .35rem 0; }
footer.quiet a { color: var(--link); }
footer.quiet .links a { display: inline-block; margin: .15rem .7rem .15rem 0; }
@media (min-width: 800px) {
  .features { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  button.btn.install { width: auto; min-width: 16rem; }
  .layout { grid-template-columns: 11.5rem minmax(0, 1fr); }
  nav { display: block; padding: .75rem .75rem 0 0; border-right: 1px solid var(--line); }
  nav button { display: block; width: 100%; }
  main { padding: .8rem 0 .2rem .9rem; }
}
</style>
</head>
<body>
<a class="skip" href="#downloadBtn">Skip to download</a>
<div class="wrap">
<header class="hero">
  <div class="brandrow">
    <img class="brandmark" src="${SIGIL}" width="40" height="40" alt="" decoding="async">
    <p class="stamp">Aziel Eliab</p>
  </div>
  <h1>AZMail</h1>
  <p class="motto">No message is trusted until verified.</p>
  <p class="lede">APP 1.0 Mail Airlock, v0.1.0, by Aziel Eliab only. A message waits until you release it.</p>
  <a class="btn block primary" id="downloadBtn" href="/download?asset=${ASSET}" aria-describedby="downloadNote">Download</a>
  <p class="asset-note" id="downloadNote"><strong>${n}</strong> downloads · <strong>${v}</strong> views · ${ASSET}</p>
  <p class="asset-note">Counted on this Worker for every branch and fork. /v1 does not increment.</p>
  <ul class="features">
    <li>Hold a message until you release it</li>
    <li>Classify and scrub run on this page</li>
    <li>One download link for every branch and fork</li>
  </ul>
  <p class="scope">The package and this page hold mail on this computer. Sending mail over the internet is outside v0.1.0.</p>
  <div class="install-row">
    <button class="btn install" id="install-btn" type="button">One-click install</button>
  </div>
  <pre id="install-cmd">${INSTALL_LINE}</pre>
  <p class="hint">Then run <code>azmail ui</code> and open http://127.0.0.1:8876 on this computer.</p>
</header>

<section class="workspace" id="mailbox" aria-label="Mailbox">
  <h2><span class="kicker">On this page</span>Mailbox</h2>
  <p class="lede">Inbox, airlock, compose, and receive stay in this browser. Classify posts to <code>/v1/airlock_classify</code>.</p>
  <div class="layout">
    <nav aria-label="Mailbox">
      <button class="active" data-view="inbox" type="button" aria-current="page">Inbox</button>
      <button data-view="airlock" type="button">Airlock queue</button>
      <button data-view="compose" type="button">Compose (demo)</button>
      <button data-view="receive" type="button">Receive</button>
      <button data-view="mesh" type="button">Mesh + keywords</button>
      <button data-view="doctor" type="button">Doctor / verify</button>
    </nav>
    <main id="main"></main>
  </div>
</section>

<div id="meshStrip" aria-label="Suite Live Nodes">
  <div class="live"><b id="meshLiveCount">0</b> Live Nodes</div>
  <div id="meshLine">Suite mesh: off (default). QNM-BUILD-1.0. QNS-CD-1.0. STW-1.0. CCS-1.0. Not an anonymity network.</div>
  <div class="rollup">live <b id="qnmLive">0</b> · locked <b id="qnmLocked">0</b> · isolated <b id="qnmIsolated">0</b></div>
  <div>No Node Gate · No auto-heal · Aziel Eliab only</div>
  <div>
    <button id="meshEnable" type="button" title="Enable suite mesh (operator bearer; default off)">Enable</button>
    <button id="meshDisable" type="button" title="Disable suite mesh (always allowed)">Disable</button>
    <button id="meshJoin" type="button" title="Join as azmail. Refused while mesh is OFF. No auto-join.">Join</button>
    <button id="meshLeave" type="button" title="Leave this node. No auto-heal.">Leave</button>
  </div>
  <p id="meshProducts">Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · QNS-CD-1.0 hub cite · SPLIT THE WIRES STW-1.0 · COLD-COPY SURVIVAL CCS-1.0 · hop default-off · not AnonBroadcast · not AZMail leftover ring · no public qnsd proxy</p>
</div>

<footer class="quiet">
  <p>Apache-2.0 · Aziel Eliab · AZMail v0.1.0</p>
  <p>This page is the human UI. Agents use FragGate with slug <code>azmail</code>.</p>
  <p class="links">
    <a href="https://github.com/AzielEliab/azmail">GitHub</a>
    <a href="/openapi.json">OpenAPI</a>
    <a href="/mcp">MCP</a>
    <a href="/v1/skill">Skill</a>
    <a href="/ai">Agents</a>
    <a href="/count">Count</a>
    <a href="/stats">Stats</a>
    <a href="/cite.json">Cite</a>
  </p>
  <p>GitHub stars ${stars} · forks ${forks} · watchers ${watchers}</p>
  <p class="links">
    <a href="https://www.azielcorpuslibrary.net/">Library</a>
    <a href="https://godlock.uk">godlock.uk</a>
    <a href="https://www.azieleliab.com">azieleliab.com</a>
    <a href="https://github.com/AzielEliab/fraggate">FragGate</a>
  </p>
</footer>
</div>
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
    document.querySelectorAll("nav button").forEach(function (x) {
      var on = x === b;
      x.classList.toggle("active", on);
      if (on) x.setAttribute("aria-current", "page");
      else x.removeAttribute("aria-current");
    });
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
    else if (j.status === "unavailable" || (j.ok === false && j.error)) line.textContent = "Suite mesh: off (unavailable). QNM-BUILD-1.0. QNS-CD-1.0. STW-1.0. CCS-1.0. Not an anonymity network.";
    else line.textContent = "Suite mesh: off (default). QNM-BUILD-1.0. QNS-CD-1.0. STW-1.0. CCS-1.0. Not an anonymity network.";
    var products = j.products_present || j.products || [];
    var names = Array.isArray(products) ? products.map(function (p) { return (typeof p === "string" ? p : (p && (p.product || p.slug)) || ""); }).filter(Boolean) : [];
    var nodes = Array.isArray(j.nodes) ? j.nodes : [];
    var extra = names.length ? " · products " + names.join(", ") : (nodes.length ? " · " + nodes.length + " node labels" : "");
    document.getElementById("meshProducts").textContent = "Catalog MCP mesh_* · FragGate slug=mesh · /v1/mesh/* PROXY · QNS-CD-1.0 hub cite · SPLIT THE WIRES STW-1.0 · COLD-COPY SURVIVAL CCS-1.0 · hop default-off · not AnonBroadcast · not AZMail leftover ring · no public qnsd proxy" + extra;
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
