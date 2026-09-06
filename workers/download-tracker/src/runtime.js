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
const SIGIL = "https://www.azielcorpuslibrary.net/sigil.png";
const FRAGGATE_CALL = "https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call";

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

Same door as MCP \`fraggate_call\` (\`slug=azmail\`). Kernel: https://github.com/AzielEliab/fraggate. Engine lands in a sibling aziel-runtime PR.

**Human UI stays on this Worker / \`azmail ui\`.** AI path is FragGate.

Mesh is **off by default**. \`mesh_disable\` is the easy off-switch.

## Human Worker (not the agent door)

Host: \`https://azmail-download-tracker.vibelock.workers.dev\`

| Method | Path | What |
|--------|------|------|
| GET | \`/v1/health\` | Liveness. Does not increment downloads. |
| GET | \`/v1/skill\` | This markdown. Does not increment downloads. |
| GET | \`/v1/example\` | Sample airlock payload. |
| POST | \`/v1/classify\` | Human-UI demo classify. Not the agent door. |
| POST | \`/v1/scrub\` | Human-UI demo scrub. |
| POST | \`/v1/keyword-alerts\` | Demo match. Agents use FragGate. |
| POST | \`/v1/mesh/*\` | Stubs that point at FragGate. Off by default. |

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
      summary: "Human-UI demo only. Agents use FragGate POST /v1/fraggate/call slug=azmail. Not a mail MCP.",
      description: LIMITATION + " Agent path: POST " + RUNTIME + "/v1/fraggate/call {slug:azmail,op,payload}. This OpenAPI is not the agent door.",
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
<p>Human UI is this Worker. <strong>AI / MCP path is FragGate only</strong> — there is no separate AZMail MCP outside the door.</p>
<p>Agent door: <code>POST ${FRAGGATE_CALL}</code> body <code>{"slug":"azmail","op":"classify","payload":{…}}</code><br>
Skill: <a href="${origin}/v1/skill">${origin}/v1/skill</a><br>
Kernel: <a href="${FRAGGATE_SAFE()}">${FRAGGATE_SAFE()}</a></p>
<pre>curl -A Mozilla/5.0 -X POST ${FRAGGATE_CALL} -H 'content-type: application/json' \\
  -d '{"slug":"azmail","op":"classify","payload":{"from":"help@paypa1-verify.com","subject":"URGENT verify your account","body_text":"reset your password immediately"}}'
curl -A Mozilla/5.0 -X POST ${FRAGGATE_CALL} -H 'content-type: application/json' \\
  -d '{"slug":"azmail","op":"mesh_disable","payload":{}}'</pre>
<p>This host's /v1 is human-demo HTTP and does not increment downloads. POST /mcp here is not an agent door. Not an MTA.</p>
<p><a href="/">Downloads + inbox UI</a></p>
</body></html>`;
}

function FRAGGATE_SAFE() {
  return "https://github.com/AzielEliab/fraggate";
}

function handleMcp() {
  return json({
    ok: false,
    error: "not a mail MCP",
    door: "fraggate",
    agent_path: FRAGGATE_CALL,
    slug: "azmail",
    body: { slug: "azmail", op: "classify", payload: {} },
    note: "AZMail agents use FragGate only: POST /v1/fraggate/call with slug=azmail. Human UI is this Worker / azmail ui. There is no separate mail MCP outside the door.",
    limitation: LIMITATION,
  });
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
      agent_path: FRAGGATE_CALL,
      slug: "azmail",
      door: "fraggate",
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
    return new Response(`AZMail ${VERSION} by Aziel Eliab. Apache-2.0. ${LIMITATION}\nAgent path (FragGate only): POST ${FRAGGATE_CALL} {"slug":"azmail","op":"…","payload":{}}\nHuman UI: ${originOf(request)}/\nSkill: ${originOf(request)}/v1/skill\n`, {
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
