/**
 * AZMail hosted runtime. Demo airlock_classify/scrub + OpenAPI stubs.
 * /v1 never touches DOWNLOADS KV. Not an MTA.
 *
 * Door paths (`/v1/fraggate/*`, `/v1/runtime/*`, `/v1/mesh/*`) PROXY to
 * aziel-runtime via AZIEL_RUNTIME service binding (match azbrowser).
 * Local ops are single-segment `/v1/{op}` only. Leftover `/v1/classify`
 * aliases FragGate op `airlock_classify`. Leftover product-local mesh
 * is `/v1/mesh_enable|mesh_disable|broadcast|listen` — not suite QNM.
 */
import {
  FRAGGATE_CALL,
  FRAGGATE_MCP,
  IDENTITY,
  LIMITATION,
  RUNTIME,
  SPEC,
  VERSION,
  classify,
  matchKeywords,
  meshStub,
  scrubHtml,
} from "./engine.js";
import { classifyV1Path, doorTargetUrl } from "./door.js";
import { meshOpenApiPaths, meshPointer } from "./mesh.js";

export const HOST = "https://azmail-download-tracker.vibelock.workers.dev";
const PRODUCT = "azmail";
const SIGIL = "https://www.azielcorpuslibrary.net/sigil.png";

/** Leftover local route → FragGate LIVE_OPS name. */
export const LOCAL_OP_ALIASES = Object.freeze({
  classify: "airlock_classify",
});

const SKILL_MD = `---
name: AZMail
description: Use when isolating, analyzing, or classifying mail through the APP 1.0 Mail Airlock, or when toggling anonymous MCP mesh mail (off by default). Not a public MTA. Author Aziel Eliab.
---

# AZMail

Anti-phishing Mail Airlock (APP 1.0). No message is trusted until verified across identity, origin, structure, and behavior.

Author: **Aziel Eliab** only.

**THIS IS:** local airlock + advisory SPF/DKIM/DMARC parsers + reputation / identity / behavior heuristics + link sandbox + HTML scrub + trust badges + user confirmation + mesh *client helpers*.

**THIS IS NOT:** a public MTA, SMTP/IMAP server, mixnet, VPN, AZ-OS, Lumen, or a guaranteed phishing block. v0.1 does not send internet email.

Always send \`User-Agent: Mozilla/5.0\`. Cloudflare Workers may 403 an empty agent.

**Agent path is FragGate only.** There is no separate AZMail MCP outside the door. Do not POST this Worker's \`/mcp\`.

\`POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call\` body \`{"slug":"azmail","op":"…","payload":{}}\`

Same door as MCP \`fraggate_call\` (\`slug=azmail\`). Kernel: https://github.com/AzielEliab/fraggate.

This Worker \`/v1/fraggate/*\` (list / describe / call), \`/v1/runtime/*\`, and \`/v1/mesh/*\` PROXY to aziel-runtime via the \`AZIEL_RUNTIME\` service binding. Local ops are \`/v1/{op}\` only.

**Human UI stays on this Worker / \`azmail ui\`.** AI path is FragGate.

**Two meshes, kept separate:**
- Suite QNM (QNM-BUILD-1.0): \`GET /v1/mesh\` PROXY. Default OFF. live|locked|isolated. No Node Gate. No auto-heal. Not anonymity. Catalog MCP \`mesh_*\` + FragGate \`slug=mesh\`. **QNS-CD-1.0** (photon QNS1 packet transfer) is a hub cite / Worker mesh cross-map only — not a Softwares-tab product. Local qnsd lives in https://github.com/AzielEliab/qnm-node. Runtime cites + catalog field live in https://github.com/AzielEliab/aziel-runtime. Pair custody is AZInterface. No public qnsd proxy.
- AZMail product-local leftover ring: \`POST /v1/mesh_disable\` (easy off-switch). Agents: FragGate \`slug=azmail\` \`op=mesh_enable|mesh_disable|broadcast|listen\`.

Suite mesh is **off by default**. Product-local \`mesh_disable\` is the easy off-switch for the anonymous ring.

## Human Worker (not the agent door)

Host: \`https://azmail-download-tracker.vibelock.workers.dev\`

| Method | Path | What |
|--------|------|------|
| GET | \`/v1/health\` | Liveness. Does not increment downloads. |
| GET | \`/v1/skill\` | This markdown. Does not increment downloads. |
| GET | \`/v1/example\` | Sample airlock payload. |
| POST | \`/v1/airlock_classify\` | Human-UI classify. Same name as FragGate op. Not stored. |
| POST | \`/v1/classify\` | Leftover alias of \`airlock_classify\`. |
| POST | \`/v1/scrub\` | Human-UI demo scrub. |
| POST | \`/v1/keyword-alerts\` | Demo match. Agents use FragGate. |
| POST | \`/v1/mesh_enable\` | Leftover product-local ring stub (not suite QNM). |
| POST | \`/v1/mesh_disable\` | Leftover product-local easy off-switch. |
| POST | \`/v1/broadcast\` | Leftover product-local broadcast stub. |
| POST | \`/v1/listen\` | Leftover product-local listen stub. |
| GET | \`/v1/mesh\` | PROXY → aziel-runtime suite QNM status. Default OFF. |
| GET | \`/v1/mesh/nodes\` | PROXY → aziel-runtime Live Nodes roster. |
| GET | \`/v1/fraggate/list\` | PROXY → aziel-runtime FragGate list. |
| GET | \`/v1/fraggate/describe\` | PROXY → aziel-runtime FragGate describe. |
| POST | \`/v1/fraggate/call\` | PROXY → aziel-runtime FragGate call. |

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants — **through FragGate**, not a mail MCP of their own.

## Local

\`\`\`bash
curl -fsSL https://azmail-download-tracker.vibelock.workers.dev/install.sh | bash
azmail ui
azmail doctor
\`\`\`

Then open http://127.0.0.1:8876 (this computer only).

## Honest banner

${LIMITATION}

Apache-2.0. Forks are welcome and always allowed.

- Catalog: https://aziel-runtime.vibelock.workers.dev/p/azmail/
- Library: https://www.azielcorpuslibrary.net/
- FragGate: https://github.com/AzielEliab/fraggate
- godlock.uk · https://www.azieleliab.com
`;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, mcp-session-id, User-Agent, Authorization",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function html(body) {
  return new Response(body, {
    headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() },
  });
}

function originOf(request) {
  try {
    return new URL(request.url).origin;
  } catch {
    return HOST;
  }
}

const EXAMPLE = {
  from: "PayPal Billing <help@paypa1-verify.com>",
  to: "you@local",
  subject: "URGENT: verify your account immediately",
  body_text: "Your account will be closed. Reset your password now.",
  body_html: '<img src="https://track.example/pixel.gif" width="1" height="1"><a href="javascript:x()">login</a>',
  headers: { "Authentication-Results": "mx; spf=fail; dkim=none; dmarc=fail" },
};

function classifyBody(body) {
  const out = classify(body);
  return { ...out, op: "airlock_classify", ok: true };
}

function openapiSpec(origin) {
  const paths = {
    "/v1/health": { get: { operationId: "azmail_health", summary: "Liveness. Does not increment downloads.", responses: { "200": { description: "ok" } } } },
    "/v1/skill": { get: { operationId: "azmail_skill", summary: "Skill markdown.", responses: { "200": { description: "markdown" } } } },
    "/v1/example": { get: { operationId: "azmail_example", summary: "Sample payload.", responses: { "200": { description: "ok" } } } },
    "/v1/airlock_classify": { post: { operationId: "azmail_airlock_classify", summary: "Advisory APP classify. FragGate op name. Not stored.", requestBody: { required: true, content: { "application/json": { schema: { type: "object" }, example: EXAMPLE } } }, responses: { "200": { description: "classification" } } } },
    "/v1/classify": { post: { operationId: "azmail_classify", summary: "Leftover alias of airlock_classify.", requestBody: { required: true, content: { "application/json": { schema: { type: "object" }, example: EXAMPLE } } }, responses: { "200": { description: "classification" } } } },
    "/v1/scrub": { post: { operationId: "azmail_scrub", summary: "Scrub HTML. Not stored.", requestBody: { required: true, content: { "application/json": { schema: { type: "object", properties: { html: { type: "string" } } } } } }, responses: { "200": { description: "scrubbed" } } } },
    "/v1/keyword-alerts": { post: { operationId: "azmail_keyword_alerts", summary: "Match keywords without revealing identity.", requestBody: { content: { "application/json": { schema: { type: "object" } } } }, responses: { "200": { description: "alerts" } } } },
    "/v1/mesh_enable": { post: { operationId: "azmail_mesh_enable_leftover", summary: "Leftover product-local ring stub (FragGate slug=azmail op=mesh_enable). Not suite QNM.", responses: { "200": { description: "stub" } } } },
    "/v1/mesh_disable": { post: { operationId: "azmail_mesh_disable_leftover", summary: "Leftover product-local easy off-switch. Not suite QNM POST /v1/mesh/disable.", responses: { "200": { description: "off" } } } },
    "/v1/broadcast": { post: { operationId: "azmail_broadcast_leftover", summary: "Leftover product-local broadcast stub. Refuses when off / doxxing / credential harvest.", requestBody: { content: { "application/json": { schema: { type: "object" } } } }, responses: { "200": { description: "stub or refuse" } } } },
    "/v1/listen": { post: { operationId: "azmail_listen_leftover", summary: "Leftover product-local listen stub. Refuses when the anonymous ring is off.", responses: { "200": { description: "stub" } } } },
    "/v1/fraggate/list": { get: { operationId: "azmail_fraggate_list_proxy", summary: "PROXY to aziel-runtime GET /v1/fraggate/list. Not a local op.", responses: { "200": { description: "hashed registry" } } } },
    "/v1/fraggate/describe": { get: { operationId: "azmail_fraggate_describe_proxy", summary: "PROXY to aziel-runtime GET /v1/fraggate/describe. Not a local op.", responses: { "200": { description: "catalog describe" } } } },
    "/v1/fraggate/call": { post: { operationId: "azmail_fraggate_call_proxy", summary: "PROXY to aziel-runtime POST /v1/fraggate/call. Not a local op.", requestBody: { content: { "application/json": { schema: { type: "object" } } } }, responses: { "200": { description: "FragGate ResultEnvelope" } } } },
    "/v1/runtime/list": { get: { operationId: "azmail_runtime_list_proxy", summary: "Alias PROXY → origin /v1/fraggate/list.", responses: { "200": { description: "hashed registry" } } } },
    "/v1/runtime/describe": { get: { operationId: "azmail_runtime_describe_proxy", summary: "Alias PROXY → origin /v1/fraggate/describe.", responses: { "200": { description: "catalog describe" } } } },
    "/v1/runtime/call": { post: { operationId: "azmail_runtime_call_proxy", summary: "Alias PROXY → origin /v1/fraggate/call.", requestBody: { content: { "application/json": { schema: { type: "object" } } } }, responses: { "200": { description: "FragGate ResultEnvelope" } } } },
  };
  Object.assign(paths, meshOpenApiPaths());
  return {
    openapi: "3.1.0",
    info: {
      title: "AZMail runtime",
      version: VERSION,
      summary: "Human-UI demo only. Agents use FragGate POST /v1/fraggate/call slug=azmail op=airlock_classify. Not a mail MCP.",
      description: LIMITATION + " Agent path: POST " + RUNTIME + "/v1/fraggate/call {slug:azmail,op,payload}. This host /v1/fraggate/* and /v1/mesh/* PROXY to aziel-runtime. Suite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer (hub cite / Worker cross-map only; no public qnsd proxy). No Node Gate. No auto-heal. Not anonymity. Product-local leftover ring is /v1/mesh_disable. This OpenAPI is not the agent door. Author: " + IDENTITY + " only.",
      license: { name: "Apache-2.0", identifier: "Apache-2.0" },
      contact: { name: IDENTITY, url: "https://github.com/AzielEliab/azmail" },
    },
    servers: [{ url: origin }, { url: RUNTIME, description: "aziel-runtime FragGate catalog" }],
    paths,
  };
}

function aiHtml(origin) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>AZMail — AI runtime</title>
<style>:root{color-scheme:dark}body{font:16px/1.45 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1.25rem;background:#0b0b0b;color:#e8e0d0}a{color:#c9a227}.banner{border:1px solid #5c4a1a;background:#241c0d;color:#f0d78c;padding:.85rem 1rem;border-radius:8px}pre{background:#141414;padding:.85rem 1rem;overflow:auto;border-radius:8px}</style></head>
<body>
<img src="${SIGIL}" alt="sigil" width="48" height="48">
<h1>AZMail runtime</h1>
<p class="banner">${LIMITATION}</p>
<p>Human UI is this Worker. <strong>AI / MCP path is FragGate only</strong> — there is no separate AZMail MCP outside the door.</p>
<p>Agent door: <code>POST ${FRAGGATE_CALL}</code> body <code>{"slug":"azmail","op":"airlock_classify","payload":{…}}</code><br>
This host <code>/v1/fraggate/*</code> and <code>/v1/mesh/*</code> PROXY to aziel-runtime.<br>
Catalog MCP: <code>POST ${FRAGGATE_MCP}</code> (<code>mesh_*</code> + FragGate <code>slug=mesh</code>). This Worker <code>/mcp</code> is a pointer.<br>
Suite mesh: <code>GET ${origin}/v1/mesh</code> default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer (hub cite / Worker cross-map; no public qnsd proxy). No Node Gate. No auto-heal. Not anonymity.<br>
Product-local leftover ring: <code>POST ${origin}/v1/mesh_disable</code> (not suite QNM).<br>
Skill: <a href="${origin}/v1/skill">${origin}/v1/skill</a><br>
Kernel: <a href="${FRAGGATE_SAFE()}">${FRAGGATE_SAFE()}</a></p>
<pre>curl -A Mozilla/5.0 -X POST ${FRAGGATE_CALL} -H 'content-type: application/json' \\
  -d '{"slug":"azmail","op":"airlock_classify","payload":{"from":"help@paypa1-verify.com","subject":"URGENT verify your account","body_text":"reset your password immediately"}}'
curl -A Mozilla/5.0 -X POST ${FRAGGATE_CALL} -H 'content-type: application/json' \\
  -d '{"slug":"azmail","op":"mesh_disable","payload":{}}'
curl -A Mozilla/5.0 ${origin}/v1/mesh</pre>
<p>This host's /v1 is human-demo HTTP and does not increment downloads. POST /mcp here is not an agent door. Not an MTA.</p>
<p><a href="/">Downloads + inbox UI</a></p>
</body></html>`;
}

function FRAGGATE_SAFE() {
  return "https://github.com/AzielEliab/fraggate";
}

function handleMcp(origin) {
  return json({
    ok: false,
    error: "not a mail MCP",
    door: "fraggate",
    agent_path: FRAGGATE_CALL,
    catalog_mcp: FRAGGATE_MCP,
    slug: "azmail",
    identity: IDENTITY,
    body: { slug: "azmail", op: "airlock_classify", payload: {} },
    mesh: meshPointer(),
    mesh_body: { slug: "mesh", op: "status", payload: {} },
    openapi: (origin || HOST) + "/openapi.json",
    note: "AZMail agents use FragGate only: POST /v1/fraggate/call with slug=azmail. This host /v1/fraggate/*, /v1/runtime/*, and /v1/mesh/* PROXY to aziel-runtime. Catalog MCP: POST " + FRAGGATE_MCP + " (mesh_* + slug=mesh). Suite mesh default OFF. QNM rollup live|locked|isolated. QNS-CD-1.0 hub cite / Worker cross-map only. No Node Gate. No auto-heal. Not anonymity. No public qnsd proxy. Product-local leftover ring is /v1/mesh_disable. Human UI is this Worker / azmail ui. There is no separate mail MCP outside the door.",
    limitation: LIMITATION,
  });
}

function runtimeFetcher(env) {
  if (env && env.AZIEL_RUNTIME && typeof env.AZIEL_RUNTIME.fetch === "function") return env.AZIEL_RUNTIME;
  return null;
}

async function proxyDoor(request, url, env) {
  const dest = doorTargetUrl(url.pathname, request.url, env);
  if (!dest) {
    return json({ ok: false, error: "not a door path", path: url.pathname, limitation: LIMITATION }, 404);
  }
  const headers = new Headers();
  const pass = ["content-type", "accept", "authorization", "user-agent", "mcp-protocol-version", "mcp-session-id", "x-aziel-runtime-token"];
  for (const name of pass) {
    const v = request.headers.get(name);
    if (v) headers.set(name, v);
  }
  if (!headers.has("User-Agent")) headers.set("User-Agent", "Mozilla/5.0 AZMail/0.1.0");
  const init = { method: request.method, headers, redirect: "follow" };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = request.body;
    init.duplex = "half";
  }
  try {
    const fetcher = runtimeFetcher(env);
    const res = fetcher ? await fetcher.fetch(dest, init) : await fetch(dest, init);
    const outHeaders = new Headers(res.headers);
    for (const [k, v] of Object.entries(corsHeaders())) outHeaders.set(k, v);
    outHeaders.set("X-Aziel-Door", "proxy");
    outHeaders.set("X-Aziel-Door-Origin", dest);
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: outHeaders });
  } catch (exc) {
    return json({
      ok: false,
      error: "fraggate_proxy_failed",
      detail: String(exc).slice(0, 240),
      origin: dest,
      agent_path: FRAGGATE_CALL,
      limitation: LIMITATION,
    }, 502);
  }
}

export { SKILL_MD };

export async function handleRuntimeApi(request, url, env) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (path === "/mcp") return handleMcp(originOf(request));
  if (path === "/v1/health" && request.method === "GET") {
    return json({
      ok: true,
      product: PRODUCT,
      version: VERSION,
      spec: SPEC,
      runtime: true,
      kv_increment: false,
      stored: false,
      mta: false,
      mesh_default: false,
      limitation: LIMITATION,
      catalog: RUNTIME,
      agent_path: FRAGGATE_CALL,
      slug: "azmail",
      door: "fraggate",
      door_proxy: ["/v1/fraggate/list", "/v1/fraggate/describe", "/v1/fraggate/call", "/v1/mesh", "/v1/mesh/nodes", "/v1/mesh/enable", "/v1/mesh/disable"],
      leftover_product_mesh: ["/v1/mesh_enable", "/v1/mesh_disable", "/v1/broadcast", "/v1/listen"],
      mesh: meshPointer(),
      classify_op: "airlock_classify",
      author: IDENTITY,
      identity: IDENTITY,
      sigil: SIGIL,
    });
  }
  if (path === "/v1/example" && (request.method === "GET" || request.method === "HEAD")) {
    return json({ ok: true, product: PRODUCT, author: "Aziel Eliab", example: EXAMPLE, note: "Sample only. Does not increment downloads." });
  }
  if (path === "/v1/skill" && request.method === "GET") {
    return new Response(SKILL_MD, {
      status: 200,
      headers: { "Content-Type": "text/markdown; charset=utf-8", "Cache-Control": "private, no-store", ...corsHeaders() },
    });
  }
  if (path === "/openapi.json" && request.method === "GET") return json(openapiSpec(originOf(request)));
  if ((path === "/ai" || url.pathname === "/ai/") && request.method === "GET") return html(aiHtml(originOf(request)));
  if (path === "/llms.txt" || path === "/ai.txt") {
    return new Response(`AZMail ${VERSION} by ${IDENTITY}. Apache-2.0. ${LIMITATION}\nAgent path (FragGate only): POST ${FRAGGATE_CALL} {"slug":"azmail","op":"airlock_classify","payload":{}}\nThis Worker /v1/fraggate/*, /v1/runtime/*, and /v1/mesh/* PROXY to aziel-runtime. Local classify is POST /v1/airlock_classify (/v1/classify leftover alias).\nCatalog MCP: POST ${FRAGGATE_MCP} (mesh_* + slug=mesh)\nThis Worker /mcp is a pointer, not a second MCP.\nSuite mesh default OFF. QNM-BUILD-1.0 live|locked|isolated. QNS-CD-1.0 photon QNS1 packet transfer (hub cite / Worker cross-map only; no public qnsd proxy). No Node Gate. No auto-heal. Not anonymity.\nProduct-local leftover ring: POST /v1/mesh_disable (not suite QNM).\nHuman UI: ${originOf(request)}/\nSkill: ${originOf(request)}/v1/skill\nOpenAPI: ${originOf(request)}/openapi.json\n`, {
      headers: { "Content-Type": "text/plain; charset=utf-8", ...corsHeaders() },
    });
  }

  const classified = classifyV1Path(url.pathname);
  if (classified.kind === "door") {
    return proxyDoor(request, url, env);
  }

  if ((path === "/v1/airlock_classify" || path === "/v1/classify") && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "JSON body required", limitation: LIMITATION }, 400); }
    return json(classifyBody(body));
  }
  if (path === "/v1/scrub" && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "JSON body required", limitation: LIMITATION }, 400); }
    return json(scrubHtml(body.html || body.text || ""));
  }
  if (path === "/v1/keyword-alerts" && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "JSON body required", limitation: LIMITATION }, 400); }
    return json({ ok: true, alerts: matchKeywords(body.text, body.keywords || []), identity: null, limitation: LIMITATION, kv_increment: false });
  }
  if (path === "/v1/mesh_disable" && request.method === "POST") return json(meshStub("mesh_disable", {}, false));
  if (path === "/v1/mesh_enable" && request.method === "POST") return json(meshStub("mesh_enable", {}, true));
  if (path === "/v1/broadcast" && request.method === "POST") {
    let body = {};
    try { body = await request.json(); } catch { /* empty */ }
    return json(meshStub("broadcast", body, false));
  }
  if (path === "/v1/listen" && request.method === "POST") return json(meshStub("listen", {}, false));
  if (classified.kind === "multi") {
    return json({
      ok: false,
      error: "not a local op",
      code: "NOT_LOCAL_OP",
      path: classified.path,
      hint: "Local ops are POST|GET /v1/{op} only (single segment). FragGate door is /v1/fraggate/* (proxied to aziel-runtime). /v1/runtime/list, /v1/runtime/describe, and /v1/runtime/call alias that door. Suite mesh is /v1/mesh/* (proxied to aziel-runtime; default OFF). Product-local leftover ring is /v1/mesh_enable|mesh_disable|broadcast|listen.",
      agent_path: FRAGGATE_CALL,
      classify_op: "airlock_classify",
      limitation: LIMITATION,
    }, 404);
  }
  if (path.startsWith("/v1/") || path === "/v1") {
    return json({ error: "not found", hint: "GET /v1/health GET /v1/skill POST /v1/airlock_classify POST /v1/scrub POST /v1/mesh_disable GET /v1/mesh GET /v1/fraggate/list GET /v1/fraggate/describe POST /v1/fraggate/call", limitation: LIMITATION }, 404);
  }
  return null;
}
