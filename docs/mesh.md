# AZMail anonymous MCP mesh — product-side contract

Author: **Aziel Eliab** only. Apache-2.0. Forks always allowed.

Live anonymous mesh chat and mail ops run via
[aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate
([FG-0.1](https://github.com/AzielEliab/fraggate)). The in-process
engine lands in a **sibling PR**. This repository ships:

- the written contract
- Python client helpers (`azmail.mesh.MeshClient`)
- Worker leftover stubs under `/v1/mesh_enable`, `/v1/mesh_disable`,
  `/v1/broadcast`, `/v1/listen` that point at FragGate `slug=azmail`

Until the runtime engine is registered, leftover stubs keep the
anonymous ring **off** and `mesh_disable` is a no-op success.

**Suite QNM is a different surface.** Worker `GET|POST /v1/mesh/*`
PROXies to aziel-runtime (QNM-BUILD-1.0 live|locked|isolated, default
OFF, no Node Gate, no auto-heal, not anonymity). Catalog MCP `mesh_*`
+ FragGate `slug=mesh`. That is not this product-local ring.

**QNS-CD-1.0** (photon QNS1 packet transfer) is a hub cite / Worker mesh
cross-map only — not a Softwares-tab product. `QNS_CD_SPEC` / `QNS_CD`
live in `workers/download-tracker/src/mesh.js` and appear on mesh
status / Live Nodes / health / `/mcp` pointer payloads. Local `qnsd` is
coded in [qnm-node](https://github.com/AzielEliab/qnm-node). Runtime
cites + catalog field live in
[aziel-runtime](https://github.com/AzielEliab/aziel-runtime)
([QNM-WP-1.0](https://github.com/AzielEliab/aziel-runtime/blob/main/docs/designs/QNM-WP-1.0.md),
[NODE_MESH](https://github.com/AzielEliab/aziel-runtime/blob/main/docs/NODE_MESH.md)).
Pair custody is [AZInterface](https://github.com/AzielEliab/azinterface).
This Worker does **not** implement qnsd and does **not** expose a public
qnsd proxy. Mesh stays default OFF.

## Off by default / easy off-switch

| Action | Local CLI | Worker stub | FragGate (when live) |
|--------|-----------|-------------|----------------------|
| Status | `azmail mesh status` | — | `fraggate_call name=azmail op=status` |
| Enable | `azmail mesh enable` | leftover `POST /v1/mesh_enable` | `op=mesh_enable` |
| **Disable** | `azmail mesh disable` | leftover `POST /v1/mesh_disable` | `op=mesh_disable` |
| Broadcast | `azmail mesh broadcast --text …` | leftover `POST /v1/broadcast` | `op=broadcast` |
| Listen | `azmail mesh listen` | leftover `POST /v1/listen` | `op=listen` |
| Suite QNM status | — | `GET /v1/mesh` PROXY | FragGate `slug=mesh` `op=status` |
| Keywords | `azmail keywords set a b` | `POST /v1/keyword-alerts` | `op=keyword_alerts` |
| Classify | `azmail classify` | `POST /v1/airlock_classify` (alias `/v1/classify`) | `op=airlock_classify` |

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
