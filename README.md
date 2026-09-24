# AZMail

AZMail checks a message before it lands in your inbox, and holds anything risky until you release it.

**Author:** Aziel Eliab
**License:** [Apache-2.0](LICENSE)

## Start

1. Install.

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e .
```

2. Open the local app.

```bash
azmail ui
```

3. Go to http://127.0.0.1:8876/ and choose **Check a message**.

`azmail doctor` checks this install. `azmail --help` lists commands. Add `--json` when you need the machine record.

Same three steps are in [RUN.txt](RUN.txt). Spec: [docs/whitepaper.md](docs/whitepaper.md). Mesh contract: [docs/mesh.md](docs/mesh.md). Contributing: [CONTRIBUTING.md](CONTRIBUTING.md).

**Forks are welcome and always allowed.**

## Notes

v0.1 is a local airlock, compose, and mesh client helpers. It does not send internet email. Hosted `/v1/airlock_classify` (leftover alias `/v1/classify`) and `/v1/scrub` are advisory demos and are not stored. `/v1/fraggate/*` and `/v1/mesh/*` PROXY to aziel-runtime via the `AZIEL_RUNTIME` service binding. Suite QNM is default OFF (live|locked|isolated). Product-local leftover ring is `POST /v1/mesh_disable`, not `/v1/mesh/*`. **QNS-CD-1.0** (photon QNS1 packet transfer) is a hub cite / Worker mesh cross-map on `workers/download-tracker/src/mesh.js` — not a Softwares-tab product and not a public `qnsd` proxy. **SPLIT THE WIRES (STW-1.0)** and **COLD-COPY SURVIVAL (CCS-1.0)** are locked product-local mesh law in `azmail/mesh.py` and that Worker file. Mesh hop default-off stays. Local `qnsd` is coded in [qnm-node](https://github.com/AzielEliab/qnm-node). Runtime cites live in [aziel-runtime](https://github.com/AzielEliab/aziel-runtime). Pair custody is [AZInterface](https://github.com/AzielEliab/azinterface). Anonymous mesh chat and mail ops run via [aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate ([kernel](https://github.com/AzielEliab/fraggate)). This repo ships the local helpers.

SPF / DKIM / DMARC are advisory parsers of headers and record text you already have. Live DNS is not queried unless you supply the record.

Speed lines in the spec (&lt;1s inbox delay, parallel scan, real-time link analysis) are targets, not a measured promise in v0.1.

## One-click install

```bash
curl -fsSL https://azmail-download-tracker.vibelock.workers.dev/install.sh | bash
```

The script curls the **counted** tarball from this project's Worker
(`/download`, User-Agent `Mozilla/5.0`), extracts, makes a venv, and
`pip install -e .`. Then run `azmail ui`.

## Counted download (Cloudflare Worker)

**This is the counted download.** GitHub releases exist as a mirror.
The Worker serves the gzip itself (HTTP 200, no 302 to GitHub).

Worker name: `azmail-download-tracker`

URL pattern (same as sibling Aziel Eliab products):

`https://azmail-download-tracker.vibelock.workers.dev`

| Path | What |
|------|------|
| `/` | Complete mail UI + views |
| `/download` | Counted tarball |
| `/count` | `{views, downloads, total}` |
| `/v1/airlock_classify` | Advisory classify (FragGate op name; no increment) |
| `/v1/classify` | Leftover alias of `airlock_classify` |
| `/v1/scrub` | HTML scrub (no increment) |
| `/v1/fraggate/list` | PROXY → aziel-runtime FragGate list |
| `/v1/fraggate/describe` | PROXY → aziel-runtime FragGate describe |
| `/v1/fraggate/call` | PROXY → aziel-runtime FragGate call |
| `/v1/mesh` | PROXY → suite QNM status (default OFF) |
| `/v1/mesh_disable` | Leftover product-local easy off-switch |
| `/v1/skill` | Agent skill |
| `/openapi.json` | OpenAPI 3.1 |

- Homepage: [https://azmail-download-tracker.vibelock.workers.dev/](https://azmail-download-tracker.vibelock.workers.dev/)
- Direct tarball: [azmail-0.1.0.tar.gz](https://azmail-download-tracker.vibelock.workers.dev/download?asset=azmail-0.1.0.tar.gz)
- Sigil: [https://www.azielcorpuslibrary.net/sigil.png](https://www.azielcorpuslibrary.net/sigil.png)
- Cite: [cite.json](https://azmail-download-tracker.vibelock.workers.dev/cite.json) — Eliab, Aziel. (2026). AZMail 0.1.0 [Software]. Apache-2.0. Do not invent a DOI.

Isolated counter: Worker `azmail-download-tracker`, KV `AZMAIL_DOWNLOADS`. `/v1` does not increment downloads.

## Dual surface

1. **Human** — `azmail ui` on this computer: check a message, inbox, held mail, quarantine. Drafts, the anonymous ring, import/export, and notes are under Advanced. The page follows the system light or dark theme. The Worker homepage is a separate counted-download surface. Worker `/v1/airlock_classify` (alias `/v1/classify`) and `/v1/scrub` are demo HTTP, not an agent door. The classify path uses the FragGate op name `airlock_classify`.
2. **Agent / MCP — FragGate only.** There is **no separate AZMail MCP**
   outside the door. Do not `POST` this Worker's `/mcp`. Do not invent
   flat `{slug}_{op}` tools. Agents use aziel-runtime FragGate:

```bash
curl -s -A 'Mozilla/5.0' -X POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call \
  -H 'content-type: application/json' \
  -d '{"slug":"azmail","op":"airlock_classify","payload":{"from":"help@paypa1-verify.com","subject":"URGENT verify","body_text":"reset your password immediately"}}'
```

MCP clients already on aziel-runtime call `fraggate_call` with
`slug=azmail` (same door). Engine lands in a sibling runtime PR; until
then FragGate may refuse unknown-name / stub. Discover first:
`runtime_skill` → `fraggate_list` → `fraggate_describe slug=azmail`.

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude
(Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot /
Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence
surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other
MCP/OpenAPI-capable assistants — **through FragGate**, not a mail MCP of
their own.

## APP 1.0 layers (modeled in code + UI)

1. Source auth — SPF / DKIM / DMARC advisory parsers
2. Domain reputation — lookalike / new domain / known-phish heuristics
3. Identity continuity — display-name vs address deviation
4. Behavioral anomaly — urgency, credentials, unexpected attachments, payment language
5. Link / attachment isolation — sandbox preview URLs; SHA-256 attachments
6. Visual trust indicators — verified / unverified / high-risk / quarantined
7. Mail Airlock — receive → isolate → analyze → classify → release
8. Metadata scrubbing — strip tracking pixels, scripts, hidden redirects
9. User confirmation — required for high-risk messages

## Anonymous MCP mesh

Off **by default**. Easy off-switch: `azmail mesh disable` or leftover
`POST /v1/mesh_disable` (not suite QNM `POST /v1/mesh/disable`).

```bash
azmail mesh status          # enabled: false
azmail mesh enable          # local helper only
azmail mesh disable         # always works
azmail keywords set lighthouse invoice
```

- Broadcast / listen as an **anonymous** mesh mailer (handle `anon-…`, no PII)
- `keyword_alerts` fire without revealing identity
- Rate limit 10 / 60s locally
- Refuse doxxing and credential-harvest content

Live mesh for agents is FragGate only
(`POST /v1/fraggate/call` `slug=azmail`), not this process and not a
mail MCP on the product Worker. Suite Live Nodes advertise the
**QNS-CD-1.0** cross-map (`qns_cd` on mesh status / health / `/mcp`
pointer). **STW-1.0** + **CCS-1.0** (`split_the_wires`,
`cold_copy_survival`). See [docs/mesh.md](docs/mesh.md).

## CLI

People get short sentences. Add `--json` for the same machine record as before.

```bash
azmail
azmail --help
azmail ui
azmail doctor
azmail classify --from 'a@b.com' --subject hello --body hi
azmail receive --from 'help@paypa1-verify.com' --subject 'URGENT verify' --body 'reset your password immediately'
azmail list airlock
azmail release AM-…
azmail --json classify --from 'a@b.com' --subject hello --body hi
azmail scrub --html '<script>x</script>'
azmail import mailbox.json
azmail export --file mailbox.json
azmail verify
azmail mesh disable
```

## Tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Offline. Covers airlock classify, HTML scrub, and keyword alerts / mesh off-switch.

## iPhone & Android

Flutter sources: [`mobile/`](mobile/). Application id `com.azieeliab.azmail`.
Offline. No analytics. Dark matte / gold.

```bash
cd mobile
flutter create --org com.azieeliab --project-name azmail .
flutter pub get
flutter run
```

## Layout

```
azmail/          library (airlock, reputation, scrub, mesh, cli, doctor, ui)
tests/           pytest
docs/            APP 1.0 whitepaper + mesh contract
examples/        demo classify
workers/download-tracker/   Cloudflare Worker azmail-download-tracker
mobile/          Flutter scaffold
SKILL.md         agent skill (also GET /v1/skill)
```

## Cross-links (optional, not required)

- Runtime: https://github.com/AzielEliab/aziel-runtime · https://aziel-runtime.vibelock.workers.dev/
- QNM local node (qnsd): https://github.com/AzielEliab/qnm-node
- AZInterface (pair custody): https://github.com/AzielEliab/azinterface
- FragGate: https://github.com/AzielEliab/fraggate
- Digital Library: https://www.azielcorpuslibrary.net/
- godlock.uk
- https://www.azieleliab.com

## License

Apache-2.0. See [LICENSE](LICENSE).

Forks are welcome and always allowed.
