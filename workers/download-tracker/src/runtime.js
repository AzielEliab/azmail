/**
 * AZMail hosted runtime. Demo classify/scrub + OpenAPI stubs that point at FragGate.
 * /v1 never touches DOWNLOADS KV. Not an MTA.
 */
import {
  LIMITATION,
  RUNTIME,
  SPEC,
  VERSION,
  classify,
  matchKeywords,
  meshStub,
  scrubHtml,
} from "./engine.js";

export const HOST = "https://azmail-download-tracker.vibelock.workers.dev";
const PRODUCT = "azmail";
const PROTOCOL = "2025-03-26";
const SIGIL = "https://www.azielcorpuslibrary.net/sigil.png";

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

Anonymous mesh chat + mail ops run via [aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate ([kernel](https://github.com/AzielEliab/fraggate)). Engine lands in a sibling PR. This Worker exposes OpenAPI stubs that point at the runtime.

Mesh is **off by default**. \`mesh_disable\` is the easy off-switch.

## Endpoints (this Worker)

Host: \`https://azmail-download-tracker.vibelock.workers.dev\`

| Method | Path | What |
|--------|------|------|
| GET | \`/v1/health\` | Liveness. Does not increment downloads. |
| GET | \`/v1/skill\` | This markdown. Does not increment downloads. |
| GET | \`/v1/example\` | Sample airlock payload. |
| POST | \`/v1/classify\` | Advisory APP classify. Not stored. |
| POST | \`/v1/scrub\` | Strip tracking pixels / scripts / hidden redirects. Not stored. |
| POST | \`/v1/keyword-alerts\` | Match keywords without revealing identity. |
| POST | \`/v1/mesh/enable\` | Stub → FragGate \`mesh_enable\`. |
| POST | \`/v1/mesh/disable\` | Off-switch (default / easy off). |
| POST | \`/v1/mesh/broadcast\` | Stub. Refuses when mesh is off, or doxxing / credential harvest. |
| POST | \`/v1/mesh/listen\` | Stub. Refuses when mesh is off. |

OpenAPI: https://azmail-download-tracker.vibelock.workers.dev/openapi.json

Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json

MCP: \`POST https://aziel-runtime.vibelock.workers.dev/mcp\` (FragGate door). Worker also serves \`POST /mcp\` for local classify/scrub.

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants.

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
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, mcp-session-id, User-Agent",
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

function openapiSpec(origin) {
  return {
    openapi: "3.1.0",
    info: {
      title: "AZMail runtime",
      version: VERSION,
      summary: "APP 1.0 Mail Airlock demo. Not a public MTA. Mesh stubs point at FragGate.",
      description: LIMITATION,
      license: { name: "Apache-2.0", identifier: "Apache-2.0" },
      contact: { name: "Aziel Eliab", url: "https://github.com/AzielEliab/azmail" },
    },
    servers: [{ url: origin }, { url: RUNTIME, description: "aziel-runtime FragGate catalog" }],
    paths: {
      "/v1/health": { get: { operationId: "azmail_health", summary: "Liveness. Does not increment downloads.", responses: { "200": { description: "ok" } } } },
      "/v1/skill": { get: { operationId: "azmail_skill", summary: "Skill markdown.", responses: { "200": { description: "markdown" } } } },
      "/v1/example": { get: { operationId: "azmail_example", summary: "Sample payload.", responses: { "200": { description: "ok" } } } },
      "/v1/classify": { post: { operationId: "azmail_classify", summary: "Advisory APP classify. Not stored.", requestBody: { required: true, content: { "application/json": { schema: { type: "object" }, example: EXAMPLE } } }, responses: { "200": { description: "classification" } } } },
      "/v1/scrub": { post: { operationId: "azmail_scrub", summary: "Scrub HTML. Not stored.", requestBody: { required: true, content: { "application/json": { schema: { type: "object", properties: { html: { type: "string" } } } } } }, responses: { "200": { description: "scrubbed" } } } },
      "/v1/keyword-alerts": { post: { operationId: "azmail_keyword_alerts", summary: "Match keywords without revealing identity.", requestBody: { content: { "application/json": { schema: { type: "object" } } } }, responses: { "200": { description: "alerts" } } } },
      "/v1/mesh/enable": { post: { operationId: "azmail_mesh_enable", summary: "Stub → FragGate mesh_enable. Mesh off by default.", responses: { "200": { description: "stub" } } } },
      "/v1/mesh/disable": { post: { operationId: "azmail_mesh_disable", summary: "Easy off-switch. Default state.", responses: { "200": { description: "off" } } } },
      "/v1/mesh/broadcast": { post: { operationId: "azmail_mesh_broadcast", summary: "Stub. Refuses when off / doxxing / credential harvest.", responses: { "200": { description: "stub or refuse" } } } },
      "/v1/mesh/listen": { post: { operationId: "azmail_mesh_listen", summary: "Stub. Refuses when mesh is off.", responses: { "200": { description: "stub" } } } },
    },
  };
}

function aiHtml(origin) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>AZMail — AI runtime</title>
<style>:root{color-scheme:dark}body{font:16px/1.45 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1.25rem;background:#0b0b0b;color:#e8e0d0}a{color:#c9a227}.banner{border:1px solid #5c4a1a;background:#241c0d;color:#f0d78c;padding:.85rem 1rem;border-radius:8px}pre{background:#141414;padding:.85rem 1rem;overflow:auto;border-radius:8px}</style></head>
<body>
<img src="${SIGIL}" alt="sigil" width="48" height="48">
<h1>AZMail runtime</h1>
<p class="banner">${LIMITATION}</p>
<p>Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude (Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable assistants.</p>
<p>OpenAPI: <a href="${origin}/openapi.json">${origin}/openapi.json</a><br>
Skill: <a href="${origin}/v1/skill">${origin}/v1/skill</a><br>
Catalog MCP: POST ${RUNTIME}/mcp<br>
FragGate: <a href="${FRAGGATE_SAFE()}">${FRAGGATE_SAFE()}</a></p>
<pre>curl -A Mozilla/5.0 ${origin}/v1/health
curl -A Mozilla/5.0 -X POST ${origin}/v1/classify -H 'content-type: application/json' \\
  -d '{"from":"help@paypa1-verify.com","subject":"URGENT verify your account","body_text":"reset your password immediately"}'
curl -A Mozilla/5.0 -X POST ${origin}/v1/mesh/disable -d '{}'</pre>
<p>/v1 never increments the download counter. Mesh stubs point at aziel-runtime. Not an MTA.</p>
<p><a href="/">Downloads + inbox UI</a></p>
</body></html>`;
}

function FRAGGATE_SAFE() {
  return "https://github.com/AzielEliab/fraggate";
}

function mcpTools() {
  return [
    { name: "azmail_health", description: "Liveness. Does not increment downloads. Not an MTA.", inputSchema: { type: "object" } },
    { name: "azmail_classify", description: "Advisory APP classify. Not stored.", inputSchema: { type: "object", additionalProperties: true } },
    { name: "azmail_scrub", description: "Scrub HTML. Not stored.", inputSchema: { type: "object", additionalProperties: true } },
    { name: "azmail_keyword_alerts", description: "Keyword alerts without revealing identity.", inputSchema: { type: "object", additionalProperties: true } },
    { name: "azmail_mesh_disable", description: "Easy mesh off-switch. Default is off.", inputSchema: { type: "object" } },
    { name: "azmail_skill", description: "AZMail skill markdown.", inputSchema: { type: "object" } },
  ];
}

async function handleMcp(request) {
  if (request.method === "GET") {
    return json({
      ok: true,
      transport: "JSON-RPC MCP-over-HTTP",
      endpoint: "POST /mcp",
      methods: ["initialize", "tools/list", "tools/call", "ping"],
      auth: "none (public)",
      note: "Prefer catalog FragGate at " + RUNTIME + "/mcp for mesh ops.",
      limitation: LIMITATION,
    });
  }
  if (request.method !== "POST") return json({ error: "POST JSON-RPC to /mcp" }, 405);
  let body;
  try {
    body = await request.json();
  } catch {
    return json({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });
  }
  const id = body && body.id !== undefined ? body.id : null;
  const method = body && body.method;
  const params = (body && body.params) || {};
  const result = (value) => json({ jsonrpc: "2.0", id, result: value });
  if (method === "initialize") {
    return result({
      protocolVersion: PROTOCOL,
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: PRODUCT, version: VERSION },
      instructions: LIMITATION,
    });
  }
  if (method === "notifications/initialized" || method === "initialized") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }
  if (method === "ping") return result({});
  if (method === "tools/list") return result({ tools: mcpTools() });
  if (method === "tools/call") {
    const name = params.name;
    const args = params.arguments || params.input || {};
    let payload;
    if (name === "azmail_health") payload = { ok: true, product: PRODUCT, version: VERSION, spec: SPEC, kv_increment: false, mta: false, limitation: LIMITATION };
    else if (name === "azmail_classify") payload = classify(args);
    else if (name === "azmail_scrub") payload = scrubHtml(args.html || args.text || "");
    else if (name === "azmail_keyword_alerts") payload = { alerts: matchKeywords(args.text, args.keywords || []), identity: null };
    else if (name === "azmail_mesh_disable") payload = meshStub("mesh_disable", {}, false);
    else if (name === "azmail_skill") payload = { markdown: SKILL_MD };
    else payload = { error: "unknown tool — use FragGate fraggate_call name=azmail", name, runtime: RUNTIME };
    return result({ content: [{ type: "text", text: JSON.stringify(payload) }], isError: Boolean(payload.error) });
  }
  return json({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } });
}

export { SKILL_MD };

export async function handleRuntimeApi(request, url) {
  const path = url.pathname.replace(/\/+$/, "") || "/";
  if (path === "/mcp") return handleMcp(request);
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
      author: "Aziel Eliab",
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
    return new Response(`AZMail ${VERSION} by Aziel Eliab. Apache-2.0. ${LIMITATION}\n${originOf(request)}/v1/skill\n${RUNTIME}/mcp\n`, {
      headers: { "Content-Type": "text/plain; charset=utf-8", ...corsHeaders() },
    });
  }

  if (path === "/v1/classify" && request.method === "POST") {
    let body;
    try { body = await request.json(); } catch { return json({ error: "JSON body required", limitation: LIMITATION }, 400); }
    return json(classify(body));
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
  if (path === "/v1/mesh/disable" && request.method === "POST") return json(meshStub("mesh_disable", {}, false));
  if (path === "/v1/mesh/enable" && request.method === "POST") return json(meshStub("mesh_enable", {}, true));
  if (path === "/v1/mesh/broadcast" && request.method === "POST") {
    let body = {};
    try { body = await request.json(); } catch { /* empty */ }
    return json(meshStub("broadcast", body, false));
  }
  if (path === "/v1/mesh/listen" && request.method === "POST") return json(meshStub("listen", {}, false));
  if (path.startsWith("/v1/") || path === "/v1") {
    return json({ error: "not found", hint: "GET /v1/health GET /v1/skill POST /v1/classify POST /v1/scrub POST /v1/mesh/disable", limitation: LIMITATION }, 404);
  }
  return null;
}
