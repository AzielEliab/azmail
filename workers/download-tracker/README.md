# AZMail download tracker

Cloudflare Worker `azmail-download-tracker`.

URL pattern after deploy (workers.dev + account subdomain, same as sibling products):

`https://azmail-download-tracker.vibelock.workers.dev`

- `GET /` — complete mail UI (inbox / compose / airlock / trust badges / keyword alerts) + counted views
- `GET /download` — counted tarball (HTTP 200 gzip, no 302)
- `GET /count` — `{views, downloads, total}`
- `GET /v1/*` — health / skill / airlock_classify / scrub / leftover product-mesh stubs (does **not** increment downloads)
- `POST /v1/airlock_classify` — human-UI classify (FragGate op name). `/v1/classify` is a leftover alias.
- `/v1/fraggate/*`, `/v1/runtime/*`, and `/v1/mesh/*` — PROXY to aziel-runtime via `AZIEL_RUNTIME` (FragGate door + suite QNM)
- `POST /v1/mesh_disable` — leftover product-local easy off-switch (not suite QNM)

KV binding `DOWNLOADS` (create `AZMAIL_DOWNLOADS` on first deploy). Account `ac575a9b822bea2bed97d0ab73aed238`.
Service binding `AZIEL_RUNTIME` → Worker `aziel-runtime`.

Human UI is this Worker. Agent / MCP path is FragGate only:
`POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call` with
`{"slug":"azmail","op":"airlock_classify","payload":{}}`. There is no separate mail MCP
on this host (`POST /mcp` returns a pointer, including suite QNM
`mesh_*`). Suite mesh is off by default (`GET /v1/mesh` PROXY).
Product-local leftover ring: `POST /v1/mesh_disable`.

Author: Aziel Eliab. Apache-2.0.
