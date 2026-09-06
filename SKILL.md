---
name: AZMail
description: >-
  Use when isolating, analyzing, or classifying mail through the APP 1.0
  Mail Airlock, or when toggling anonymous MCP mesh mail (off by default).
  Not a public MTA. Author Aziel Eliab.
---

# AZMail

Anti-phishing Mail Airlock (APP 1.0). No message is trusted until verified
across identity, origin, structure, and behavior.

Author: **Aziel Eliab** only.

**THIS IS:** local airlock + advisory SPF/DKIM/DMARC parsers + reputation /
identity / behavior heuristics + link sandbox + HTML scrub + trust badges +
user confirmation + mesh *client helpers*.

**THIS IS NOT:** a public MTA, SMTP/IMAP server, mixnet, VPN, AZ-OS, Lumen,
or a guaranteed phishing block. v0.1 does not send internet email.

Always send `User-Agent: Mozilla/5.0`. Cloudflare Workers may 403 an empty agent.

Anonymous mesh chat + mail ops run via
[aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate
([kernel](https://github.com/AzielEliab/fraggate)). Engine lands in a sibling
PR. This Worker exposes OpenAPI stubs that point at the runtime.

Mesh is **off by default**. `mesh_disable` is the easy off-switch. Broadcasts
refuse doxxing and credential-harvest content. Handles are `anon-…` (no PII).
Keyword alerts fire without revealing identity.

## Endpoints (this Worker)

Host: `https://azmail-download-tracker.vibelock.workers.dev`

| Method | Path | What |
|--------|------|------|
| GET | `/v1/health` | Liveness. Does not increment downloads. |
| GET | `/v1/skill` | This markdown. Does not increment downloads. |
| GET | `/v1/example` | Sample airlock payload. |
| POST | `/v1/classify` | Advisory APP classify. Not stored. |
| POST | `/v1/scrub` | Strip tracking pixels / scripts / hidden redirects. Not stored. |
| POST | `/v1/keyword-alerts` | Match keywords without revealing identity. |
| POST | `/v1/mesh/enable` | Stub → FragGate `mesh_enable`. |
| POST | `/v1/mesh/disable` | Off-switch (default / easy off). |
| POST | `/v1/mesh/broadcast` | Stub. Refuses when mesh is off, or doxxing / credential harvest. |
| POST | `/v1/mesh/listen` | Stub. Refuses when mesh is off. |

OpenAPI: https://azmail-download-tracker.vibelock.workers.dev/openapi.json

Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json

MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude
(Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing,
Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces,
Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable
assistants.

ChatGPT: GPT Actions → Import from URL (no auth). Grok: import the OpenAPI as
a custom tool, or MCP. Venice: HTTP tools. Claude, Cursor, Glama, and other
MCP clients: `POST` the catalog MCP URL. Other OpenAPI-capable assistants:
import the same OpenAPI.

## How to call (Mozilla/5.0)

```bash
curl -s -A 'Mozilla/5.0' https://azmail-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' -X POST https://azmail-download-tracker.vibelock.workers.dev/v1/classify \
  -H 'content-type: application/json' \
  -d '{"from":"help@paypa1-verify.com","subject":"URGENT verify your account","body_text":"reset your password immediately"}'
curl -s -A 'Mozilla/5.0' -X POST https://azmail-download-tracker.vibelock.workers.dev/v1/mesh/disable -d '{}'
```

Prefer FragGate for live mesh:

`fraggate_call name=azmail op=mesh_disable`

(Engine lands in a sibling aziel-runtime PR. Until then the Worker stub
keeps mesh off.)

## Local (after one-click install)

```bash
curl -fsSL https://azmail-download-tracker.vibelock.workers.dev/install.sh | bash
azmail ui
azmail doctor
```

Then open http://127.0.0.1:8876 (this computer only). Import JSON file
(`type=file`) and Export JSON. Then `azmail doctor`.

## Honest banner

THIS IS: a local Mail Airlock plus advisory APP 1.0 layers and mesh client
helpers. THIS IS NOT: a public MTA, SMTP/IMAP server, mixnet, VPN, or a
guaranteed phishing block. Author: Aziel Eliab only.

Apache-2.0. Forks are welcome and always allowed.

## Catalog + local UI

- Product homepage: https://azmail-download-tracker.vibelock.workers.dev/
- Catalog product: https://aziel-runtime.vibelock.workers.dev/p/azmail/
- Catalog OpenAPI: https://aziel-runtime.vibelock.workers.dev/openapi.json
- Catalog MCP: `POST https://aziel-runtime.vibelock.workers.dev/mcp`
- FragGate kernel: https://github.com/AzielEliab/fraggate
- Library: https://www.azielcorpuslibrary.net/
- godlock.uk · https://www.azieleliab.com
- Counted download: https://azmail-download-tracker.vibelock.workers.dev/download?asset=azmail-0.1.0.tar.gz
- GitHub: https://github.com/AzielEliab/azmail
