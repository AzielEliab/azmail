"""AZMail — APP 1.0 anti-phishing Mail Airlock. Author: Aziel Eliab only."""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
SPEC_STRING = "azmail-app-1.0"
ENGINE_VERSION = "0.1.0"

LIMITATION = (
    "THIS IS: a local Mail Airlock plus APP 1.0 layers "
    "(SPF/DKIM/DMARC checks on records and keys the operator supplies, "
    "domain reputation, identity continuity, behavioral heuristics, "
    "link/attachment isolation, HTML scrub, visual trust badges, "
    "user confirmation), an operator-gated SMTP submission client, "
    "and mesh *client helpers*. "
    "THIS IS NOT: a public MTA, an SMTP/IMAP server, a mixnet, a VPN, or a "
    "guaranteed phishing block. mta is true only after a complete relay "
    "config and a successful handshake on a transport the operator supplied. "
    "Unconfigured runs stay mta false and do not open a socket. "
    "The hosted Worker does not relay mail or query DNS. "
    "Hosted Worker is a counted download + human UI + demo HTTP. "
    "The AI / MCP path is FragGate only: POST "
    "https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call "
    "with slug=azmail — not a separate mail MCP. Engine lands in a "
    "sibling PR. No hard dependency on AZ-OS, Lumen, or a separate "
    "interface product. Author: Aziel Eliab only."
)

HONEST_BANNER = LIMITATION
LOOPBACK = "127.0.0.1"
DEFAULT_PORT = 8876
HOST_WORKER = "https://azmail-download-tracker.vibelock.workers.dev"
RUNTIME_HOST = "https://aziel-runtime.vibelock.workers.dev"
FRAGGATE_KERNEL = "https://github.com/AzielEliab/fraggate"
SIGIL_URL = "https://www.azielcorpuslibrary.net/sigil.png"

from azmail.airlock import (  # noqa: E402
    Classification,
    Envelope,
    classify,
    process,
    receive,
    release,
)
from azmail.mesh import MeshClient, mesh_disable, mesh_enable  # noqa: E402
from azmail.scrub import scrub_html  # noqa: E402

__all__ = [
    "Classification",
    "Envelope",
    "ENGINE_VERSION",
    "HONEST_BANNER",
    "HOST_WORKER",
    "LIMITATION",
    "LOOPBACK",
    "DEFAULT_PORT",
    "MeshClient",
    "RUNTIME_HOST",
    "SIGIL_URL",
    "SPEC_STRING",
    "__author__",
    "__version__",
    "classify",
    "mesh_disable",
    "mesh_enable",
    "process",
    "receive",
    "release",
    "scrub_html",
]
