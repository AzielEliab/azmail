# AZMail

Public identity: **Aziel Eliab** only.

This is an APP 1.0 anti-phishing Mail Airlock. It is not a public MTA,
not AZ-OS, not Lumen, and not a mixnet.

Mesh is off by default. Product-local leftover `mesh_disable` is the easy
off-switch for the anonymous ring. Suite QNM (`/v1/mesh/*` PROXY) is a
separate rollup — default OFF; live|locked|isolated; no Node Gate; no
auto-heal; not anonymity. QNS-CD-1.0 (photon QNS1 packet transfer) is a
hub cite / Worker mesh cross-map only — not a Softwares-tab product; no
public qnsd proxy. Local qnsd is AzielEliab/qnm-node. Runtime cites live
in AzielEliab/aziel-runtime. Pair custody is AZInterface.

Agent path is FragGate only:
`POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call`
with `slug=azmail` and classify op `airlock_classify`.
The product Worker proxies `/v1/fraggate/list|describe|call` via
`AZIEL_RUNTIME`. Not a separate mail MCP. Human UI stays local / Worker.

Forks are welcome and always allowed. Apache-2.0.
