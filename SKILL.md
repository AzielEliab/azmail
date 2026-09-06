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

**Agent path is FragGate only.** MCP / agents call aziel-runtime — not a
separate mail MCP on this Worker, and not `POST /mcp` here.

```
POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call
{"slug":"azmail","op":"<airlock_classify|scrub|mesh_enable|mesh_disable|broadcast|listen|keyword_alerts>","payload":{}}
```

Same door as the `fraggate_call` MCP tool (`slug=azmail`). Kernel:
https://github.com/AzielEliab/fraggate. Live FragGate classify op is
`airlock_classify` (not leftover `classify`).

This Worker `/v1/fraggate/*` (list / describe / call) and `/v1/runtime/*`
PROXY to aziel-runtime via the `AZIEL_RUNTIME` service binding. Local ops
are `/v1/{op}` only.

**Human UI stays on this Worker / `azmail ui`.** AI path is FragGate.

Mesh is **off by default**. `mesh_disable` is the easy off-switch. Broadcasts
refuse doxxing and credential-harvest content. Handles are `anon-…` (no PII).
Keyword alerts fire without revealing identity.

## Human Worker (not the agent door)

Host: `https://azmail-download-tracker.vibelock.workers.dev`

| Method | Path | What |
|--------|------|------|
| GET | `/v1/health` | Liveness. Does not increment downloads. |
| GET | `/v1/skill` | This markdown. Does not increment downloads. |
| GET | `/v1/example` | Sample airlock payload. |
| POST | `/v1/airlock_classify` | Human-UI classify. Same name as FragGate op. Not stored. |
| POST | `/v1/classify` | Leftover alias of `airlock_classify`. |
| POST | `/v1/scrub` | Human-UI demo scrub. Not stored. |
| POST | `/v1/keyword-alerts` | Demo match. Agents use FragGate `keyword_alerts`. |
| POST | `/v1/mesh/*` | Stubs that point at FragGate. Off by default. |
| GET | `/v1/fraggate/list` | PROXY → aziel-runtime FragGate list. |
| GET | `/v1/fraggate/describe` | PROXY → aziel-runtime FragGate describe. |
| POST | `/v1/fraggate/call` | PROXY → aziel-runtime FragGate call. |

There is **no** AZMail MCP outside FragGate. `POST /mcp` on this host
returns a pointer to `/v1/fraggate/call`.

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude
(Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot / Bing,
Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence surfaces,
Amazon Q tooling, DuckAssist, You.com, Cohere, and other MCP/OpenAPI-capable
assistants — **via FragGate** (`fraggate_call` / `POST /v1/fraggate/call`).

## How to call (Mozilla/5.0)

Agent / MCP (FragGate only):

```bash
curl -s -A 'Mozilla/5.0' -X POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call \
  -H 'content-type: application/json' \
  -d '{"slug":"azmail","op":"airlock_classify","payload":{"from":"help@paypa1-verify.com","subject":"URGENT verify your account","body_text":"reset your password immediately"}}'
curl -s -A 'Mozilla/5.0' -X POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call \
  -H 'content-type: application/json' \
  -d '{"slug":"azmail","op":"mesh_disable","payload":{}}'
```

Human demo on this Worker (UI / curl; not the agent door):

```bash
curl -s -A 'Mozilla/5.0' https://azmail-download-tracker.vibelock.workers.dev/v1/health
curl -s -A 'Mozilla/5.0' -X POST https://azmail-download-tracker.vibelock.workers.dev/v1/airlock_classify \
  -H 'content-type: application/json' \
  -d '{"from":"help@paypa1-verify.com","subject":"URGENT verify","body_text":"reset your password immediately"}'
curl -s -A 'Mozilla/5.0' -X POST https://azmail-download-tracker.vibelock.workers.dev/v1/mesh/disable -d '{}'
```

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

- Product homepage (human UI): https://azmail-download-tracker.vibelock.workers.dev/
- Agent door: `POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call` body `{"slug":"azmail","op":"airlock_classify","payload":{}}`
- FragGate kernel: https://github.com/AzielEliab/fraggate
- Library: https://www.azielcorpuslibrary.net/
- godlock.uk · https://www.azieleliab.com
- Counted download: https://azmail-download-tracker.vibelock.workers.dev/download?asset=azmail-0.1.0.tar.gz
- GitHub: https://github.com/AzielEliab/azmail
