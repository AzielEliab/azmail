# Contributing to AZMail

**Forks are first-class.** This project is Apache-2.0; you do not need
permission to fork, patch, or redistribute.

**Forks are welcome and always allowed.**

## How to run tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

Python 3.10+. Engine is stdlib only. pytest is the dev extra.
No network. No ML. Not a public MTA.

## Ground rules

1. **Not a public MTA.** Do not add SMTP send, IMAP scrape, From:
   rotation, mixnet, or IP masking. v0.1 compose is a local draft.
2. **Mesh stays off by default.** `mesh_disable` must remain an easy
   off-switch. No PII in handles. Refuse doxxing and credential harvest.
3. **UI binds loopback only** (`127.0.0.1:8876`). Do not listen on
   `0.0.0.0`. No telemetry. No CDN.
4. **Do not mix the download tracker** with any other product's Worker
   or KV. Namespace `AZMAIL_DOWNLOADS` only.
5. **Public identity is Aziel Eliab only.** Do not add GodLock.AZ as an
   identity label.
6. **Independence.** Do not import AZ-OS, Lumen, or a required interface
   product. Optional documentation links are fine.
7. New behavior needs a test that fails without the change.
8. SPF/DKIM/DMARC stay advisory unless the operator already supplied
   the record or key. Do not pretend live DNS ran.

## Where to change things

- Airlock: `azmail/airlock.py`
- Reputation / auth / identity / behavior / isolate: matching modules
- Scrub: `azmail/scrub.py`
- Mesh helpers: `azmail/mesh.py`
- CLI / doctor / UI: `azmail/cli.py`, `azmail/doctor.py`, `azmail/ui.py`, `azmail/web/`
- Spec: `docs/whitepaper.md`, `docs/mesh.md`
- Skill: `SKILL.md` (same text at Worker `GET /v1/skill`)
- FragGate / suite-mesh door proxy: `workers/download-tracker/src/door.js` + `AZIEL_RUNTIME` binding (`/v1/fraggate/*`, `/v1/runtime/*`, `/v1/mesh/*`)
- Suite Live Nodes strip: `workers/download-tracker/src/mesh.js` + Worker homepage. Keep leftover product-local `/v1/mesh_disable` off `/v1/mesh/*`.
- Classify UI / Worker route must use FragGate op `airlock_classify` (`/v1/classify` is leftover alias only)
- Flutter: `mobile/`
- Isolated counter: `workers/download-tracker/`

## License of contributions

By submitting a change you agree it is licensed under Apache-2.0, the
same license as the rest of the tree. Keep the copyright lines honest.
Ship as Aziel Eliab.
