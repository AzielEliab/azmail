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
SPLIT THE WIRES (STW-1.0) + COLD-COPY SURVIVAL (CCS-1.0) are locked
mesh law on `src/mesh.js`. Hop default-off stays.

Author: Aziel Eliab. Apache-2.0.

## Human / bot schema (`/stats` and `/count`)

Additive dual-count (Whitestone canary). Classification lives in `src/classify.js`
and response shaping in `src/stats-shape.js`.

Invariant: `views === views_human + views_bot` and
`downloads === downloads_human + downloads_bot`.

Legacy strategy (b): existing KV totals are never reset. Pre-split remainder
is shown as bot on read (`views_bot = views - views_human`). Author: Aziel Eliab only.

