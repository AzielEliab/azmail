# AZMail download tracker

Cloudflare Worker `azmail-download-tracker`.

URL pattern after deploy (workers.dev + account subdomain, same as sibling products):

`https://azmail-download-tracker.vibelock.workers.dev`

- `GET /` — complete mail UI (inbox / compose / airlock / trust badges / keyword alerts) + counted views
- `GET /download` — counted tarball (HTTP 200 gzip, no 302)
- `GET /count` — `{views, downloads, total}`
- `GET /v1/*` — classify / scrub / mesh stubs (does **not** increment downloads)

KV binding `DOWNLOADS` (create `AZMAIL_DOWNLOADS` on first deploy). Account `ac575a9b822bea2bed97d0ab73aed238`.

Mesh stubs point at aziel-runtime FragGate. Mesh is off by default; `POST /v1/mesh/disable` is the easy off-switch.

Author: Aziel Eliab. Apache-2.0.
