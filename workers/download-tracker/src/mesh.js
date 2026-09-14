/**
 * Suite node mesh — QNM-BUILD-1.0 Live Nodes contract.
 * QNS-CD-1.0 (photon QNS1 packet transfer) is a hub cite / Worker
 * cross-map only — not a Softwares-tab product, not a public qnsd proxy.
 * Default OFF. Public rollup is live|locked|isolated counts only.
 * No Node Gate. No auto-heal. Not an anonymity network.
 * /v1/mesh/* PROXY to aziel-runtime (AZIEL_RUNTIME binding).
 * AZMail product-local leftover mesh stays at /v1/mesh_enable|mesh_disable|broadcast|listen.
 * SPLIT THE WIRES (STW-1.0) + COLD-COPY SURVIVAL (CCS-1.0) locked law.
 * Mesh hop default-off stays. Author: Aziel Eliab only.
 */
import { FRAGGATE_CALL, FRAGGATE_MCP, IDENTITY, RUNTIME } from "./engine.js";

export const QNM_SPEC = "QNM-BUILD-1.0";
export const QNS_CD_SPEC = "QNS-CD-1.0";
export const MESH_KERNEL = "NM-0.1";
export const MESH_DEFAULT_OFF = true;
export const MESH_ANONYMITY_NETWORK = false;
export const MESH_NODE_GATE = false;
export const MESH_AUTO_HEAL = false;
export const MESH_IDENTITY = IDENTITY;
export const MESH_SLUG = "mesh";
export const MESH_PRODUCT = "azmail";
export const MESH_PATH = "/v1/mesh";
export const MESH_STATUS_PATH = "/v1/mesh/status";
export const MESH_NODES_PATH = "/v1/mesh/nodes";
export const MESH_ENABLE_PATH = "/v1/mesh/enable";
export const MESH_DISABLE_PATH = "/v1/mesh/disable";
export const MESH_JOIN_PATH = "/v1/mesh/join";
export const MESH_HEARTBEAT_PATH = "/v1/mesh/heartbeat";
export const MESH_LEAVE_PATH = "/v1/mesh/leave";
export const MESH_BROADCAST_PATH = "/v1/mesh/broadcast";
export const ANON_BROADCAST = "https://github.com/AzielEliab/anon-broadcast";
export const QNM_NODE = "https://github.com/AzielEliab/qnm-node";
export const AZIEL_RUNTIME_REPO = "https://github.com/AzielEliab/aziel-runtime";
export const AZINTERFACE_REPO = "https://github.com/AzielEliab/azinterface";

/** Leftover product-local anonymous ring (not suite QNM). */
export const PRODUCT_MESH_ENABLE = "/v1/mesh_enable";
export const PRODUCT_MESH_DISABLE = "/v1/mesh_disable";
export const PRODUCT_MESH_BROADCAST = "/v1/broadcast";
export const PRODUCT_MESH_LISTEN = "/v1/listen";

/** QNS-CD-1.0 photon QNS1 packet transfer — hub cite / Worker mesh cross-map. */
export const QNS_CD = Object.freeze({
  spec: QNS_CD_SPEC,
  title: "photon QNS1 packet transfer",
  kind: "hub_cite",
  softwares_tab: false,
  engine: false,
  public_qnsd_proxy: false,
  node_gate: false,
  default_off: true,
  qnsd: "local qnm-node only",
  pair_custody: "azinterface",
  qnm_node: QNM_NODE,
  aziel_runtime: AZIEL_RUNTIME_REPO,
  azinterface: AZINTERFACE_REPO,
  designs: Object.freeze({
    qnm_wp: AZIEL_RUNTIME_REPO + "/blob/main/docs/designs/QNM-WP-1.0.md",
    node_ops: AZIEL_RUNTIME_REPO + "/blob/main/docs/designs/NODE-OPS-1.0.md",
    node_mesh: AZIEL_RUNTIME_REPO + "/blob/main/docs/NODE_MESH.md",
    qnm_build: QNM_NODE + "/blob/main/docs/QNM-BUILD-1.0.md",
  }),
  note: "QNS-CD-1.0 photon QNS1 packet transfer. Local qnsd is coded in AzielEliab/qnm-node. Runtime cites + catalog field live in AzielEliab/aziel-runtime. AZInterface has pair custody. Hub cite / Worker mesh cross-map only. Not a Softwares-tab product. No public qnsd proxy. Author: Aziel Eliab only.",
});

export const STW_SPEC = "STW-1.0";
export const CCS_SPEC = "CCS-1.0";
export const TICK_MIN_SEC = 0.5;
export const TICK_MAX_SEC = 1.0;
export const DWELL_SEC = 777;
export const TIP_HASH_HEX_LEN = 64;
export const TIP_TICK_BYTES = 65;
export const PLANE_TIP = "tip";
export const PLANE_PAYLOAD = "payload";
export const SOCKET_TICK = "tick_1s";
export const SOCKET_DWELL = "dwell_777s";
export const MESH_HOP_DEFAULT_OFF = true;
export const COLD_COPY_MIN = 2;
const PRESENCE_WIRE = Object.freeze({ live: "L", locked: "K", isolated: "I" });

export const STW = Object.freeze({
  spec: STW_SPEC,
  title: "SPLIT THE WIRES",
  author: MESH_IDENTITY,
  identity: MESH_IDENTITY,
  hop_default: false,
  hop_default_off: true,
  tick_min_sec: TICK_MIN_SEC,
  tick_max_sec: TICK_MAX_SEC,
  dwell_sec: DWELL_SEC,
  tip_only: true,
  tip_fields: Object.freeze(["presence", "tip_hash"]),
  tip_tick_bytes: TIP_TICK_BYTES,
  tip_hash_hex_len: TIP_HASH_HEX_LEN,
  payload_plane: "pull",
  update: "proof",
  cite: "prev+lockset",
  fail_closed: true,
  clock_desync_is_yes: false,
  ambiguous: "isolate",
  equivocation: "ends_peer",
  emit_last: "local",
  phoenix: "local_only",
  auto_splice: false,
  heartbeat_loss_is_poison: false,
  heartbeat_loss_applies_last_packet: false,
  sockets: Object.freeze({ [SOCKET_TICK]: TICK_MAX_SEC, [SOCKET_DWELL]: DWELL_SEC }),
  note: "SPLIT THE WIRES STW-1.0. Tip-only 0.5–1s tick (presence+tip hash fixed-size). Pull-only payload plane. Update is proof, not a timer (cite prev+lockset fail-closed; 777s dwell after valid cite; clock desync is not yes; ambiguous isolates). Equivocation ends peer. Emit last locally. Phoenix local only. Partition does not auto-splice. Heartbeat loss is not poison and does not apply the last packet. 1s tick socket is not the 777s dwell socket. Mesh hop default-off stays. Author: Aziel Eliab only.",
});

export const CCS = Object.freeze({
  spec: CCS_SPEC,
  title: "COLD-COPY SURVIVAL",
  author: MESH_IDENTITY,
  identity: MESH_IDENTITY,
  multiply: true,
  min_copies: COLD_COPY_MIN,
  live_body_sync: false,
  tip_erase: "expensive",
  server_pull_wipes_cold: false,
  poison: "hash_absolute_refuse",
  data_outlives_creators: true,
  keeps_split_the_wires: true,
  hop_default_off: true,
  note: "COLD-COPY SURVIVAL CCS-1.0. Multiply cold copies. Refuse live body sync. Tip is expensive to erase. Server pull cannot wipe cold replicas. Hash-absolute poison refuse (not interpret). Data outlives creators. Keeps SPLIT THE WIRES. Mesh hop default-off stays. Author: Aziel Eliab only.",
});

export const MESH_NOTE =
  "QNM-BUILD-1.0. QNS-CD-1.0 photon QNS1 packet transfer. SPLIT THE WIRES STW-1.0. COLD-COPY SURVIVAL CCS-1.0. Suite mesh default off. Hop default-off. Live|locked|isolated counts only. No Node Gate. No auto-heal. Not an anonymity network. No public qnsd proxy. Author: Aziel Eliab only.";

function hex64(value) {
  const digest = String(value || "").trim().toLowerCase();
  if (digest.length !== TIP_HASH_HEX_LEN) return null;
  if (!/^[0-9a-f]+$/.test(digest)) return null;
  return digest;
}

export function encodeTipTick(presence, tipHash, payload) {
  if (payload != null && payload !== "") {
    return { ok: false, code: "STW_TIP_ONLY", plane: PLANE_TIP, payload: null };
  }
  if (!PRESENCE_WIRE[presence]) {
    return { ok: false, code: "STW_PRESENCE_UNKNOWN", presence };
  }
  const digest = hex64(tipHash);
  if (!digest) return { ok: false, code: "STW_TIP_HASH_SIZE", want: TIP_HASH_HEX_LEN };
  const wire = PRESENCE_WIRE[presence] + digest;
  return {
    ok: true,
    code: "STW_OK",
    plane: PLANE_TIP,
    socket: SOCKET_TICK,
    presence,
    tip_hash: digest,
    wire,
    bytes: wire.length,
    payload: null,
  };
}

export function tickIntervalOk(seconds) {
  const dt = Number(seconds);
  return Number.isFinite(dt) && dt >= TICK_MIN_SEC && dt <= TICK_MAX_SEC;
}

export function admitPayload({ direction, plane = PLANE_PAYLOAD, socket = SOCKET_DWELL, hop_enabled = false } = {}) {
  if (hop_enabled) return { ok: false, code: "STW_HOP_DEFAULT_OFF", hop: false, enabled: false };
  if (plane !== PLANE_PAYLOAD) return { ok: false, code: "STW_PLANE_SPLIT", plane };
  if (socket !== SOCKET_DWELL) return { ok: false, code: "STW_SOCKET_SPLIT", note: "1s tick socket is not the 777s dwell socket" };
  if (String(direction || "").trim().toLowerCase() !== "pull") {
    return { ok: false, code: "STW_PULL_ONLY", direction, payload_plane: "pull" };
  }
  return { ok: true, code: "STW_OK", plane: PLANE_PAYLOAD, direction: "pull", socket: SOCKET_DWELL, hop: false };
}

export function decideUpdate(event) {
  const ev = event && typeof event === "object" ? event : {};
  const kind = String(ev.kind || ev.reason || "").trim().toLowerCase();
  if (ev.clock_desync || kind === "clock_desync" || kind === "desync") {
    return { ok: false, apply: false, yes: false, code: "STW_CLOCK_DESYNC_NOT_YES" };
  }
  if (ev.ambiguous || kind === "ambiguous") {
    return { ok: false, apply: false, isolate: true, code: "STW_AMBIGUOUS_ISOLATE" };
  }
  if (kind === "heartbeat_loss" || ev.heartbeat_loss) return heartbeatLoss();
  const timerOnly = !!ev.timer || kind === "timer";
  const prev = ev.prev || ev.cite_prev;
  const lockset = ev.lockset;
  if (timerOnly && !(prev && lockset)) return { ok: false, apply: false, code: "STW_UPDATE_NOT_TIMER" };
  if (!prev || !lockset || ev.valid_cite === false) {
    return { ok: false, apply: false, fail_closed: true, code: "STW_CITE_FAIL_CLOSED" };
  }
  return { ok: true, apply: true, dwell_sec: DWELL_SEC, fail_closed: false, code: "STW_OK", cite: "prev+lockset" };
}

export function equivocationEndsPeer(peer, tips) {
  const unique = new Set((tips || []).map((t) => String(t || "").trim().toLowerCase()).filter(Boolean));
  if (unique.size > 1) return { ok: true, peer, ended: true, apply: false, code: "STW_EQUIVOCATION_ENDS_PEER" };
  return { ok: true, peer, ended: false, code: "STW_OK" };
}

export function emitLast({ scope = "local" } = {}) {
  if (String(scope).trim().toLowerCase() !== "local") return { ok: false, relay: false, code: "STW_EMIT_LAST_LOCAL" };
  return { ok: true, emit: "last", scope: "local", relay: false, code: "STW_OK" };
}

export function phoenix({ scope = "local" } = {}) {
  if (String(scope).trim().toLowerCase() !== "local") return { ok: false, public_restore: false, code: "STW_PHOENIX_LOCAL_ONLY" };
  return { ok: true, scope: "local", public_restore: false, code: "STW_PHOENIX_LOCAL" };
}

export function partitionHeal({ auto_splice = false } = {}) {
  if (auto_splice) return { ok: false, splice: false, code: "STW_NO_AUTO_SPLICE" };
  return { ok: true, splice: false, code: "STW_PARTITION_HOLD" };
}

export function heartbeatLoss() {
  return { ok: true, poison: false, apply: false, apply_last_packet: false, code: "STW_HEARTBEAT_LOSS_NOT_POISON" };
}

export function socketsAreSplit(tickSocket, dwellSocket) {
  if (tickSocket === dwellSocket || tickSocket !== SOCKET_TICK || dwellSocket !== SOCKET_DWELL) {
    return { ok: false, code: "STW_SOCKET_SPLIT", note: "1s ≠ 777s sockets" };
  }
  return { ok: true, tick: SOCKET_TICK, dwell: SOCKET_DWELL, code: "STW_OK" };
}

export function hopEnable() {
  return { ok: false, enabled: false, default_off: true, code: "STW_HOP_DEFAULT_OFF", note: "Mesh hop default-off stays." };
}

export function multiplyColdCopies(copies) {
  const rows = (copies || []).filter((c) => c != null);
  const live = [];
  const hashes = [];
  for (const raw of rows) {
    if (raw && typeof raw === "object") {
      if (raw.cold === false || raw.live === true) live.push(raw);
      const digest = raw.hash || raw.body_hash || raw.tip_hash;
      if (digest) hashes.push(String(digest));
    } else if (raw) {
      hashes.push(String(raw));
    }
  }
  if (live.length) return { ok: false, code: "CCS_LIVE_BODY_SYNC_REFUSED", copies: rows.length };
  if (rows.length < COLD_COPY_MIN) return { ok: false, code: "CCS_MULTIPLY", min_copies: COLD_COPY_MIN, copies: rows.length };
  return { ok: true, code: "CCS_OK", copies: rows.length, min_copies: COLD_COPY_MIN, distinct: hashes.length ? new Set(hashes).size : rows.length, cold: true };
}

export function liveBodySync({ source = "live", target = "cold" } = {}) {
  return { ok: false, synced: false, source, target, code: "CCS_LIVE_BODY_SYNC_REFUSED", note: "Refuse live body sync. Cold copies stay cold." };
}

export function eraseTip({ expensive = false } = {}) {
  return { ok: false, erased: false, expensive: !!expensive, code: "CCS_TIP_ERASE_EXPENSIVE", note: "Tip is expensive to erase. Cheap wipe is refused." };
}

export function serverPull({ wipe_cold = false, replicas = [] } = {}) {
  const kept = Array.isArray(replicas) ? replicas.slice() : [];
  if (wipe_cold) {
    return { ok: false, wiped: false, replicas: kept, copies: kept.length, code: "CCS_SERVER_PULL_NO_WIPE", note: "Server pull cannot wipe cold replicas." };
  }
  return { ok: true, wiped: false, replicas: kept, copies: kept.length, direction: "pull", code: "CCS_OK" };
}

export function poisonRefuse(digest, poison) {
  const want = hex64(digest);
  if (!want) return { ok: false, apply: false, code: "CCS_POISON_HASH_ABSOLUTE" };
  const marked = new Set((poison || []).map((h) => hex64(String(h))).filter(Boolean));
  if (marked.has(want)) {
    return { ok: false, apply: false, interpret: false, hash: want, code: "CCS_POISON_HASH_ABSOLUTE", note: "Hash-absolute poison refuse. Not interpreted." };
  }
  return { ok: true, apply: false, interpret: false, hash: want, poison: false, code: "CCS_OK" };
}

export function creatorGone(creator, replicas) {
  const kept = Array.isArray(replicas) ? replicas.slice() : [];
  return { ok: true, creator, gone: true, wiped: false, replicas: kept, copies: kept.length, data_remains: true, code: "CCS_DATA_OUTLIVES_CREATORS", note: "Data outlives creators." };
}

export const MESH_OPS = Object.freeze([
  "status",
  "enable",
  "disable",
  "join",
  "heartbeat",
  "leave",
  "nodes",
  "broadcast",
]);

export const MESH_PROXY_ROUTES = Object.freeze([
  { path: MESH_PATH, methods: ["get", "head"], op: "status", summary: "PROXY to aziel-runtime GET /v1/mesh. Suite mesh status. Default OFF. Not a local op. Not AZMail's product-local ring." },
  { path: MESH_STATUS_PATH, methods: ["get"], op: "status", summary: "PROXY alias of GET /v1/mesh. Not a local op." },
  { path: MESH_NODES_PATH, methods: ["get"], op: "nodes", summary: "PROXY to aziel-runtime GET /v1/mesh/nodes. Live Nodes (5-minute presence). Not a local op." },
  { path: MESH_ENABLE_PATH, methods: ["post"], op: "enable", summary: "PROXY to aziel-runtime POST /v1/mesh/enable. Operator bearer required. Rate-limited. Not a local op. Not AZMail mesh_enable." },
  { path: MESH_DISABLE_PATH, methods: ["post"], op: "disable", summary: "PROXY to aziel-runtime POST /v1/mesh/disable. Always allowed. Not a local op. Product-local leftover is POST /v1/mesh_disable." },
  { path: MESH_JOIN_PATH, methods: ["post"], op: "join", summary: "PROXY to aziel-runtime POST /v1/mesh/join. Body {product, node_id?, label?, presence?}. Refused while OFF. Not a local op." },
  { path: MESH_HEARTBEAT_PATH, methods: ["post"], op: "heartbeat", summary: "PROXY to aziel-runtime POST /v1/mesh/heartbeat. Body {node_id}. Not a local op." },
  { path: MESH_LEAVE_PATH, methods: ["post"], op: "leave", summary: "PROXY to aziel-runtime POST /v1/mesh/leave. Body {node_id}. Not a local op. No auto-heal." },
  { path: MESH_BROADCAST_PATH, methods: ["post"], op: "broadcast", summary: "PROXY to aziel-runtime POST /v1/mesh/broadcast. SHA-256 receipt only. Not AnonBroadcast upload. Not AZMail leftover /v1/broadcast." },
]);

function firstNum(...vals) {
  for (const raw of vals) {
    if (raw == null || raw === "") continue;
    const n = typeof raw === "number" ? raw : Number(String(raw).replace(/,/g, ""));
    if (Number.isFinite(n) && n >= 0) return Math.floor(n);
  }
  return null;
}

function asList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === "object") return Object.values(value);
  return [];
}

function truthyEnabled(value) {
  if (value === true || value === 1) return true;
  const s = String(value || "").trim().toLowerCase();
  return s === "on" || s === "enabled" || s === "true" || s === "live";
}

export function emptyRollup() {
  return { live: 0, locked: 0, isolated: 0 };
}

export function meshRollup(mesh) {
  const m = mesh && typeof mesh === "object" ? mesh : {};
  const r = m.rollup && typeof m.rollup === "object" && !Array.isArray(m.rollup) ? m.rollup : {};
  return {
    live: firstNum(r.live, m.live_nodes, m.live) ?? 0,
    locked: firstNum(r.locked, m.locked_nodes, m.locked) ?? 0,
    isolated: firstNum(r.isolated, m.isolated_nodes, m.isolated) ?? 0,
  };
}

function parseRollup(inner, listedLive) {
  const r = inner.rollup && typeof inner.rollup === "object" && !Array.isArray(inner.rollup)
    ? inner.rollup
    : {};
  const live = firstNum(
    r.live,
    r.live_nodes,
    r.live_count,
    inner.live,
    inner.live_nodes,
    inner.mesh_live_nodes,
    inner.live_count,
    inner.count,
    inner.n,
    inner.node_count,
    listedLive,
  );
  const locked = firstNum(r.locked, r.locked_nodes, r.locked_count, inner.locked, inner.locked_nodes, inner.locked_count);
  const isolated = firstNum(r.isolated, r.isolated_nodes, r.isolated_count, inner.isolated, inner.isolated_nodes, inner.isolated_count);
  return {
    live: live != null ? live : 0,
    locked: locked != null ? locked : 0,
    isolated: isolated != null ? isolated : 0,
  };
}

export function emptyMesh(extra = {}) {
  const rollup = extra.rollup && typeof extra.rollup === "object"
    ? { ...emptyRollup(), ...extra.rollup }
    : emptyRollup();
  return {
    ok: true,
    spec: QNM_SPEC,
    kernel: MESH_KERNEL,
    enabled: false,
    default_off: true,
    live_nodes: 0,
    status: extra.status || "off",
    source: extra.source || "fallback",
    node_gate: false,
    auto_heal: false,
    anonymity_network: false,
    author: MESH_IDENTITY,
    identity: MESH_IDENTITY,
    note: MESH_NOTE,
    door: MESH_PATH,
    qns_cd: QNS_CD,
    split_the_wires: STW,
    cold_copy_survival: CCS,
    hop_default_off: true,
    ...extra,
    spec: QNM_SPEC,
    rollup,
    node_gate: false,
    auto_heal: false,
    anonymity_network: false,
    author: MESH_IDENTITY,
    identity: MESH_IDENTITY,
    qns_cd: QNS_CD,
    split_the_wires: STW,
    cold_copy_survival: CCS,
    hop_default_off: true,
  };
}

export function compactMeshNode(raw) {
  if (raw == null) return null;
  if (typeof raw === "string") {
    const id = raw.trim();
    return id ? { id } : null;
  }
  if (typeof raw !== "object") return null;
  const id = String(raw.id || raw.node_id || raw.session_id || raw.peer || raw.name || "").trim();
  const product = String(raw.product || raw.slug || raw.suite || "").trim();
  const seen = raw.last_utc || raw.last_seen || raw.seen_utc || raw.heartbeat_utc || "";
  if (!id && !product && !seen) return null;
  const out = {};
  if (id) out.id = id;
  if (product) out.product = product;
  if (seen) out.last_utc = String(seen);
  return out;
}

export function parseMeshDoc(body) {
  if (body == null) return emptyMesh({ status: "unavailable", source: "empty" });
  if (typeof body !== "object" || Array.isArray(body)) {
    return emptyMesh({ status: "unavailable", source: "empty" });
  }
  const inner = body.result && typeof body.result === "object" && !Array.isArray(body.result)
    ? { ...body, ...body.result }
    : (body.mesh && typeof body.mesh === "object" && !Array.isArray(body.mesh)
      ? { ...body, ...body.mesh }
      : body);
  const listed = asList(inner.nodes || inner.list || inner.peers || inner.live_nodes_list)
    .map(compactMeshNode)
    .filter(Boolean);
  const rollup = parseRollup(inner, listed.length ? listed.length : null);
  const enabled = truthyEnabled(inner.enabled)
    || truthyEnabled(inner.mesh_enabled)
    || String(inner.status || "").toLowerCase() === "on";
  const unavailable = inner.ok === false
    && !enabled
    && (inner.error || inner.status === "unavailable" || inner.status === "not_found");
  const status = enabled ? "on" : (unavailable ? "unavailable" : "off");
  const live = enabled ? rollup.live : 0;
  const locked = enabled ? rollup.locked : 0;
  const isolated = enabled ? rollup.isolated : 0;
  const products = asList(inner.products_present || inner.products)
    .map((p) => (typeof p === "string" ? p : (p && (p.product || p.slug || p.name)) || ""))
    .map((s) => String(s).trim())
    .filter(Boolean);
  return emptyMesh({
    ok: inner.ok !== false,
    enabled,
    default_off: inner.default_off !== false,
    live_nodes: live,
    rollup: { live, locked, isolated },
    products_present: products,
    nodes: listed,
    status,
    source: inner.source || "parsed",
    door: inner.door || MESH_PATH,
    note: enabled
      ? "QNM-BUILD-1.0. QNS-CD-1.0 photon QNS1 packet transfer. SPLIT THE WIRES STW-1.0. COLD-COPY SURVIVAL CCS-1.0. Suite mesh is on. Live|locked|isolated counts only. No Node Gate. No auto-heal. Not an anonymity network. No public qnsd proxy."
      : MESH_NOTE,
    qns_cd: QNS_CD,
    split_the_wires: STW,
    cold_copy_survival: CCS,
    hop_default_off: true,
  });
}

export function publicMesh(mesh) {
  const m = mesh && typeof mesh === "object" ? mesh : emptyMesh();
  const enabled = !!m.enabled;
  const rollup = enabled ? meshRollup(m) : emptyRollup();
  return {
    spec: QNM_SPEC,
    kernel: MESH_KERNEL,
    enabled,
    default_off: m.default_off !== false,
    live_nodes: enabled ? rollup.live : 0,
    rollup,
    status: enabled ? "on" : (m.status === "unavailable" ? "unavailable" : "off"),
    source: m.source || "fallback",
    node_gate: false,
    auto_heal: false,
    anonymity_network: false,
    author: MESH_IDENTITY,
    identity: MESH_IDENTITY,
    door: MESH_PATH,
    status_path: MESH_STATUS_PATH,
    nodes_path: MESH_NODES_PATH,
    join: MESH_JOIN_PATH,
    heartbeat: MESH_HEARTBEAT_PATH,
    enable: MESH_ENABLE_PATH,
    disable: MESH_DISABLE_PATH,
    leave: MESH_LEAVE_PATH,
    broadcast: MESH_BROADCAST_PATH,
    mcp: FRAGGATE_MCP,
    fraggate: FRAGGATE_CALL,
    slug: MESH_SLUG,
    product: MESH_PRODUCT,
    ops: MESH_OPS.slice(),
    origin: RUNTIME + MESH_PATH,
    leftover_product_mesh: {
      enable: PRODUCT_MESH_ENABLE,
      disable: PRODUCT_MESH_DISABLE,
      broadcast: PRODUCT_MESH_BROADCAST,
      listen: PRODUCT_MESH_LISTEN,
      note: "AZMail anonymous ring leftovers. Not suite QNM.",
    },
    qns_cd: QNS_CD,
    split_the_wires: STW,
    cold_copy_survival: CCS,
    hop_default_off: true,
    note: m.note || MESH_NOTE,
  };
}

export function meshStatusLine(mesh) {
  const m = mesh && typeof mesh === "object" ? mesh : emptyMesh();
  if (m.enabled) {
    const r = meshRollup(m);
    return "Suite mesh: on · live " + r.live + " · locked " + r.locked + " · isolated " + r.isolated + ". Not an anonymity network.";
  }
  if (m.status === "unavailable") {
    return "Suite mesh: off (unavailable). QNM-BUILD-1.0. QNS-CD-1.0. STW-1.0. CCS-1.0. Not an anonymity network.";
  }
  return "Suite mesh: off (default). QNM-BUILD-1.0. QNS-CD-1.0. STW-1.0. CCS-1.0. Not an anonymity network.";
}

/** Public Live Nodes count. Never auto-heal a visiting floor. */
export function alignLiveNodes({ mesh } = {}) {
  if (mesh && mesh.enabled) return meshRollup(mesh).live;
  return 0;
}

export function meshPointer() {
  return {
    pointer: true,
    path: MESH_PATH,
    enabled_default: false,
    spec: QNM_SPEC,
    kernel: MESH_KERNEL,
    rollup: "live|locked|isolated",
    node_gate: false,
    auto_heal: false,
    anonymity_network: false,
    author: MESH_IDENTITY,
    identity: MESH_IDENTITY,
    catalog_mcp: FRAGGATE_MCP,
    fraggate_slug: MESH_SLUG,
    origin: RUNTIME + MESH_PATH,
    leftover_product_mesh: [PRODUCT_MESH_ENABLE, PRODUCT_MESH_DISABLE, PRODUCT_MESH_BROADCAST, PRODUCT_MESH_LISTEN],
    qns_cd: QNS_CD,
    split_the_wires: STW,
    cold_copy_survival: CCS,
    hop_default_off: true,
    note: "PROXY to aziel-runtime /v1/mesh/* via AZIEL_RUNTIME. Not a local op. Not AnonBroadcast. Not AZMail's product-local ring (leftover /v1/mesh_enable|mesh_disable|broadcast|listen; FragGate slug=azmail). Not a public qnsd proxy. " + MESH_NOTE,
    anon_broadcast: ANON_BROADCAST,
    anon_broadcast_publish_path: false,
  };
}

export function meshOpenApiPaths() {
  const paths = {};
  for (const route of MESH_PROXY_ROUTES) {
    const entry = paths[route.path] || {};
    for (const method of route.methods) {
      entry[method] = {
        operationId: "azmail_mesh_" + route.op + (method === "head" ? "_head" : "") + "_proxy",
        summary: route.summary,
        tags: ["mesh"],
        responses: { "200": { description: "aziel-runtime mesh envelope" } },
      };
      if (method === "post") {
        entry[method].requestBody = { content: { "application/json": { schema: { type: "object" } } } };
      }
    }
    paths[route.path] = entry;
  }
  return paths;
}
