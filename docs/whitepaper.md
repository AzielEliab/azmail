# AZMail Anti-Phishing Protocol (APP) 1.0

**Author:** Aziel Eliab only
**Software:** AZMail 0.1.0
**License:** Apache-2.0
**Date:** September 2026

## Abstract

APP 1.0 is a multi-layer defensive mail architecture. The core rule is
simple: **no message is trusted until verified across identity, origin,
structure, and behavior.**

AZMail implements APP as standalone software. It does not require AZ-OS,
Lumen, or a separate interface product. Cross-links to the Aziel Eliab
runtime and library are optional.

v0.1 is an honest local product: Mail Airlock, advisory parsers, demo
compose, and mesh *client helpers*. It is not a public mail transfer
agent and does not send internet email.

## Layers

### 1. Source authentication

Parse and validate SPF records, DKIM-Signature tags, DMARC policies, and
`Authentication-Results` / `Received-SPF` headers the operator already
has. Results are **advisory**. Live DNS and cryptographic DKIM verify
are out of scope unless the caller supplies the record or key.

### 2. Domain reputation

Heuristics for lookalike brands (edit distance, leet / homoglyph,
brand-plus-extra tokens), new or suspicious domains (hyphens, digit
ratio, risky TLDs, optional `domain_age_days`), and a small bundled
known-phish fixture list. Not a live threat feed.

### 3. Identity continuity

Flag first-seen senders, display-name / address mismatches against a
local contact book, and unexpected domains for a known display name.

### 4. Behavioral anomaly

Keyword heuristics for urgency, credential harvest, payment language,
and unexpected attachment types (executable / HTML attach). Not a
content-intent model.

### 5. Link and attachment isolation

Extract URLs and rewrite them to a contained `sandbox:preview` locator.
Hash attachments (SHA-256). Do not execute. Hosted and local UIs open
links in a sandbox preview, not a raw navigation.

### 6. Visual trust indicators

Four badges: **verified**, **unverified**, **high-risk**,
**quarantined**. The UI must show the badge before the body is treated
as ordinary mail.

### 7. Mail Airlock

Every inbound message walks:

`receive → isolate → analyze → classify → release`

High-risk messages stay in the queue until the user confirms. Known-phish
and strong credential-harvest cases go to quarantine.

### 8. Metadata scrubbing

Rendered HTML is rewritten: scripts, iframes, event handlers, 1×1 /
tracker pixels, `javascript:` / `data:text/html` hrefs, hidden
(`display:none` / `font-size:0`) redirects, meta-refresh, and common
tracking query parameters are stripped. URL shorteners are isolated.

### 9. User confirmation

High-risk classifications require an explicit confirm before release
into the inbox.

## Performance (aspirational)

- Inbox delay under one second
- Layers scanned in parallel
- Real-time link analysis at preview time

These are design targets. v0.1 does not claim a measured SLA.

## Dual surface

Human software (Worker UI, Flutter `mobile/`, local `azmail ui`, counted
`/download`) stays complete. Agent / MCP software runs through
aziel-runtime FragGate. Identity is Aziel Eliab only.

## Mesh

Anonymous MCP mesh mail is a product-side contract: off by default, easy
off-switch, keyword alerts without identity, no PII in handles, rate
limits, refuse doxxing and credential harvest. Live execution is
FragGate (sibling runtime PR). See [mesh.md](mesh.md).

## Independence

AZMail is complete without AZ-OS, Lumen, GodLock, or any other product
import. Optional links to the runtime, library, godlock.uk, and
azieleliab.com are documentation only.

## What this is not

Not a public MTA. Not SMTP/IMAP. Not a mixnet. Not a VPN. Not a
guaranteed phishing oracle. Not legal advice. Hosted `/v1` does not
store mail.

## Cite

Eliab, Aziel. (2026). AZMail 0.1.0 [Software]. Apache-2.0.
https://github.com/AzielEliab/azmail

Do not invent a DOI.
