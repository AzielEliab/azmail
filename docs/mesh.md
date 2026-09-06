# AZMail anonymous MCP mesh — product-side contract

Author: **Aziel Eliab** only. Apache-2.0. Forks always allowed.

Live anonymous mesh chat and mail ops run via
[aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate
([FG-0.1](https://github.com/AzielEliab/fraggate)). The in-process
engine lands in a **sibling PR**. This repository ships:

- the written contract
- Python client helpers (`azmail.mesh.MeshClient`)
- Worker OpenAPI stubs under `/v1/mesh/*` that point at the runtime

Until the runtime engine is registered, hosted stubs keep mesh **off**
and `mesh_disable` is a no-op success.

## Off by default / easy off-switch

| Action | Local CLI | Worker stub | FragGate (when live) |
|--------|-----------|-------------|----------------------|
| Status | `azmail mesh status` | — | `fraggate_call name=azmail op=status` |
| Enable | `azmail mesh enable` | `POST /v1/mesh/enable` | `op=mesh_enable` |
| **Disable** | `azmail mesh disable` | `POST /v1/mesh/disable` | `op=mesh_disable` |
| Broadcast | `azmail mesh broadcast --text …` | `POST /v1/mesh/broadcast` | `op=broadcast` |
| Listen | `azmail mesh listen` | `POST /v1/mesh/listen` | `op=listen` |
| Keywords | `azmail keywords set a b` | `POST /v1/keyword-alerts` | `op=keyword_alerts` |

Default `enabled=false`. Any `mesh_disable` call turns the microphone
off immediately. Broadcast and listen refuse with `MESH_DISABLED` while
off. This is the chaos off-switch.

## Anonymous handle

Handles are `anon-` + hex. They are not emails, legal names, or phone
numbers. The product refuses mailbox-shaped tokens on the mesh.

## Keyword alerts

Subscribe to keywords. A match returns `{keyword, matched, identity: null}`.
The alert must not reveal who subscribed or who broadcast.

## Rate limits

Local helper: 10 broadcasts / 60 seconds / handle. Runtime should keep
an equivalent or stricter cap.

## Refuse

The mesh refuses:

- doxxing language (`doxx`, `lives at`, `home address`, SSN-shaped tokens)
- credential harvest (`password:`, `api_key:`, bearer tokens)
- PII / mailbox-shaped content

This is a product refuse list, not a claim of global content moderation.

## Agent path (FragGate only)

There is **no separate AZMail MCP**. Humans use `azmail ui` / the Worker
homepage. Agents call aziel-runtime:

```
POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call
{"slug":"azmail","op":"mesh_disable","payload":{}}
```

MCP clients already on the runtime use `fraggate_call` with `slug=azmail`
(same door). Discover first:

```
runtime_skill
fraggate_list
fraggate_describe slug=azmail
fraggate_call slug=azmail op=mesh_disable
```

Do not invent flat `azmail_broadcast` tool names. Do not `POST` the
product Worker's `/mcp`. HTTP `POST /p/azmail/{op}` on the runtime is a
**proxy**, not exec, until the engine is live.

Compatible clients: ChatGPT, Grok, Venice, Claude, Cursor, Glama,
Perplexity, Copilot, Gemini, Mistral, Meta AI, Apple Intelligence,
Amazon Q, DuckAssist, You.com, Cohere, plus other MCP/OpenAPI-capable
assistants.
