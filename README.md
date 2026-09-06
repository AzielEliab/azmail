# AZMail

Open-source **anti-phishing Mail Airlock** — APP 1.0. No message is
trusted until verified across identity, origin, structure, and behavior.

**Author:** Aziel Eliab only
**Date:** September 2026 · APP 1.0 / product v0.1.0
**License:** [Apache-2.0](LICENSE)

> Standalone software. Optional cross-links only. No hard dependency on
> AZ-OS, Lumen, or a separate “interface” product.

See the spec: [docs/whitepaper.md](docs/whitepaper.md).
Mesh contract: [docs/mesh.md](docs/mesh.md).
How to contribute: [CONTRIBUTING.md](CONTRIBUTING.md).

**Forks are welcome and always allowed.**

## Honest scope (read this)

v0.1 is a **local airlock + compose + mesh client helpers**. It is **not**
a public MTA. It does **not** send internet email. Hosted
`/v1/classify` and `/v1/scrub` are advisory demos and are not stored.
Anonymous mesh chat and mail ops run via
[aziel-runtime](https://github.com/AzielEliab/aziel-runtime) FragGate
([kernel](https://github.com/AzielEliab/fraggate)); the engine lands in a
sibling PR. This repo documents the contract and ships local helpers +
Worker OpenAPI stubs that point at the runtime.

SPF / DKIM / DMARC are **advisory parsers** of headers and record text
you already have. Live DNS is not queried unless you supply the record.

Performance copy is **aspirational**: &lt;1s inbox delay, parallel scan,
real-time link analysis. Not a measured SLA in v0.1.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
azmail ui
```

Open http://127.0.0.1:8876 (loopback only). Inbox / compose / airlock
queue / trust badges / keyword alerts. Then `azmail doctor`.

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
| `/v1/classify` | Advisory classify (no increment) |
| `/v1/scrub` | HTML scrub (no increment) |
| `/v1/mesh/disable` | Easy mesh off-switch |
| `/v1/skill` | Agent skill |
| `/openapi.json` | OpenAPI 3.1 |

- Homepage: [https://azmail-download-tracker.vibelock.workers.dev/](https://azmail-download-tracker.vibelock.workers.dev/)
- Direct tarball: [azmail-0.1.0.tar.gz](https://azmail-download-tracker.vibelock.workers.dev/download?asset=azmail-0.1.0.tar.gz)
- Sigil: [https://www.azielcorpuslibrary.net/sigil.png](https://www.azielcorpuslibrary.net/sigil.png)
- Cite: [cite.json](https://azmail-download-tracker.vibelock.workers.dev/cite.json) — Eliab, Aziel. (2026). AZMail 0.1.0 [Software]. Apache-2.0. Do not invent a DOI.

Isolated counter: Worker `azmail-download-tracker`, KV `AZMAIL_DOWNLOADS`. `/v1` does not increment downloads.

## Dual surface

1. **Human UI** — Worker homepage and `azmail ui` are complete software:
   inbox, compose (demo), airlock queue, trust badges, keyword alert
   settings, import/export, doctor/verify, counted download. Black / gold.
2. **Agent / MCP** — Discover and call through aziel-runtime FragGate
   (`runtime_skill` → `fraggate_list` → `fraggate_call`). This Worker may
   expose OpenAPI stubs that point at the runtime. Do not invent flat
   `{slug}_{op}` tools.

Works with ChatGPT (GPT Actions / OpenAI), Grok (xAI), Venice, Claude
(Anthropic), Cursor (MCP), Glama (MCP), Perplexity, Microsoft Copilot /
Bing, Google Gemini / Vertex, Mistral, Meta AI, Apple Intelligence
surfaces, Amazon Q tooling, DuckAssist, You.com, Cohere, and other
MCP/OpenAPI-capable assistants.

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

Off **by default**. Easy off-switch: `azmail mesh disable` or
`POST /v1/mesh/disable`.

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

Live mesh is FragGate, not this process. See [docs/mesh.md](docs/mesh.md).

## CLI

```bash
azmail version
azmail ui                 # 127.0.0.1:8876
azmail doctor
azmail classify --from 'a@b.com' --subject hello --body hi
azmail receive --from 'help@paypa1-verify.com' --subject 'URGENT verify' --body 'reset your password immediately'
azmail list airlock
azmail release AM-…
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
- FragGate: https://github.com/AzielEliab/fraggate
- Digital Library: https://www.azielcorpuslibrary.net/
- godlock.uk
- https://www.azieleliab.com

## License

Apache-2.0. See [LICENSE](LICENSE).

Forks are welcome and always allowed.
