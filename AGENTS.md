# AZMail

Public identity: **Aziel Eliab** only.

This is an APP 1.0 anti-phishing Mail Airlock. It is not a public MTA,
not AZ-OS, not Lumen, and not a mixnet.

Mesh is off by default. `mesh_disable` is the easy off-switch.

Agent path is FragGate only:
`POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call`
with `slug=azmail`. Not a separate mail MCP. Human UI stays local / Worker.

Forks are welcome and always allowed. Apache-2.0.
