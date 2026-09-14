/**
 * Suite mesh Live Nodes + QNM-BUILD-1.0 contract.
 * QNS-CD-1.0 photon QNS1 packet transfer — hub cite / Worker cross-map only.
 * Default OFF. live|locked|isolated. No Node Gate. No auto-heal. Not anonymity.
 * No public qnsd proxy. Product-local leftover ring stays off /v1/mesh/* .
 * Author: Aziel Eliab only.
 */
import assert from "node:assert/strict";
import {
  QNM_SPEC,
  QNS_CD_SPEC,
  QNS_CD,
  STW_SPEC,
  CCS_SPEC,
  STW,
  CCS,
  MESH_DEFAULT_OFF,
  MESH_ANONYMITY_NETWORK,
  MESH_NODE_GATE,
  MESH_AUTO_HEAL,
  MESH_HOP_DEFAULT_OFF,
  MESH_OPS,
  MESH_PATH,
  MESH_IDENTITY,
  MESH_NOTE,
  PRODUCT_MESH_DISABLE,
  DWELL_SEC,
  SOCKET_TICK,
  SOCKET_DWELL,
  admitPayload,
  alignLiveNodes,
  creatorGone,
  decideUpdate,
  emptyMesh,
  encodeTipTick,
  eraseTip,
  equivocationEndsPeer,
  hopEnable,
  liveBodySync,
  meshOpenApiPaths,
  meshPointer,
  meshStatusLine,
  multiplyColdCopies,
  parseMeshDoc,
  poisonRefuse,
  publicMesh,
  serverPull,
  socketsAreSplit,
} from "../workers/download-tracker/src/mesh.js";
import { classifyV1Path, DEFAULT_RUNTIME_ORIGIN, doorTargetUrl, localOpFromPath } from "../workers/download-tracker/src/door.js";
import { handleRuntimeApi } from "../workers/download-tracker/src/runtime.js";
import { homeHtml } from "../workers/download-tracker/src/ui.js";

assert.equal(QNM_SPEC, "QNM-BUILD-1.0");
assert.equal(QNS_CD_SPEC, "QNS-CD-1.0");
assert.equal(QNS_CD.spec, QNS_CD_SPEC);
assert.equal(QNS_CD.title, "photon QNS1 packet transfer");
assert.equal(QNS_CD.kind, "hub_cite");
assert.equal(QNS_CD.softwares_tab, false);
assert.equal(QNS_CD.engine, false);
assert.equal(QNS_CD.public_qnsd_proxy, false);
assert.equal(QNS_CD.node_gate, false);
assert.equal(QNS_CD.default_off, true);
assert.equal(QNS_CD.qnsd, "local qnm-node only");
assert.equal(QNS_CD.pair_custody, "azinterface");
assert.equal(QNS_CD.qnm_node, "https://github.com/AzielEliab/qnm-node");
assert.equal(QNS_CD.aziel_runtime, "https://github.com/AzielEliab/aziel-runtime");
assert.equal(QNS_CD.azinterface, "https://github.com/AzielEliab/azinterface");
assert.match(QNS_CD.designs.qnm_wp, /docs\/designs\/QNM-WP-1\.0\.md$/);
assert.match(QNS_CD.note, /QNS-CD-1\.0 photon QNS1 packet transfer/);
assert.match(MESH_NOTE, /QNS-CD-1\.0/);
assert.match(MESH_NOTE, /SPLIT THE WIRES STW-1\.0/);
assert.match(MESH_NOTE, /COLD-COPY SURVIVAL CCS-1\.0/);
assert.equal(STW_SPEC, "STW-1.0");
assert.equal(CCS_SPEC, "CCS-1.0");
assert.equal(STW.title, "SPLIT THE WIRES");
assert.equal(CCS.title, "COLD-COPY SURVIVAL");
assert.equal(STW.author, "Aziel Eliab");
assert.equal(CCS.author, "Aziel Eliab");
assert.equal(STW.hop_default_off, true);
assert.equal(CCS.keeps_split_the_wires, true);
assert.equal(MESH_HOP_DEFAULT_OFF, true);
assert.equal(DWELL_SEC, 777);
assert.equal(MESH_DEFAULT_OFF, true);
assert.equal(MESH_ANONYMITY_NETWORK, false);
assert.equal(MESH_NODE_GATE, false);
assert.equal(MESH_AUTO_HEAL, false);
assert.equal(MESH_IDENTITY, "Aziel Eliab");
assert.ok(MESH_OPS.includes("status") && MESH_OPS.includes("nodes"));
assert.equal(MESH_PATH, "/v1/mesh");
assert.equal(PRODUCT_MESH_DISABLE, "/v1/mesh_disable");

const empty = emptyMesh();
assert.equal(empty.enabled, false);
assert.deepEqual(empty.rollup, { live: 0, locked: 0, isolated: 0 });
assert.equal(empty.node_gate, false);
assert.equal(empty.auto_heal, false);
assert.equal(empty.anonymity_network, false);
assert.equal(empty.identity, "Aziel Eliab");
assert.equal(empty.qns_cd.spec, QNS_CD_SPEC);
assert.equal(empty.qns_cd.public_qnsd_proxy, false);
assert.equal(empty.split_the_wires.spec, STW_SPEC);
assert.equal(empty.cold_copy_survival.spec, CCS_SPEC);
assert.equal(empty.hop_default_off, true);

const qnm = parseMeshDoc({
  spec: "QNM-BUILD-1.0",
  enabled: true,
  rollup: { live: 2, locked: 1, isolated: 3 },
  nodes: [{ id: "a" }, { id: "b" }, { id: "c" }],
});
assert.deepEqual(qnm.rollup, { live: 2, locked: 1, isolated: 3 });
assert.equal(qnm.live_nodes, 2);
assert.equal(qnm.node_gate, false);
assert.equal(qnm.auto_heal, false);

const off = parseMeshDoc({ enabled: false, live_nodes: 9, nodes: [{ id: "stale" }] });
assert.equal(off.enabled, false);
assert.equal(off.live_nodes, 0);
assert.deepEqual(off.rollup, { live: 0, locked: 0, isolated: 0 });

const pub = publicMesh(qnm);
assert.equal(pub.nodes, undefined);
assert.equal(pub.slug, "mesh");
assert.equal(pub.product, "azmail");
assert.equal(pub.leftover_product_mesh.disable, "/v1/mesh_disable");
assert.equal(pub.qns_cd.spec, QNS_CD_SPEC);
assert.equal(pub.qns_cd.public_qnsd_proxy, false);
assert.equal(pub.qns_cd.softwares_tab, false);
assert.equal(pub.split_the_wires.spec, STW_SPEC);
assert.equal(pub.cold_copy_survival.spec, CCS_SPEC);
assert.equal(pub.hop_default_off, true);
assert.match(meshStatusLine(pub), /Suite mesh: on · live 2 · locked 1 · isolated 3/);
assert.match(meshStatusLine(emptyMesh()), /Suite mesh: off \(default\)\. QNM-BUILD-1\.0\. QNS-CD-1\.0/);
assert.equal(alignLiveNodes({ mesh: { enabled: true, rollup: { live: 4, locked: 1, isolated: 0 } } }), 4);
assert.equal(alignLiveNodes({ mesh: { enabled: false, live_nodes: 9 } }), 0);

const pointer = meshPointer();
assert.equal(pointer.enabled_default, false);
assert.equal(pointer.rollup, "live|locked|isolated");
assert.equal(pointer.fraggate_slug, "mesh");
assert.equal(pointer.node_gate, false);
assert.equal(pointer.auto_heal, false);
assert.equal(pointer.anonymity_network, false);
assert.equal(pointer.qns_cd.spec, QNS_CD_SPEC);
assert.equal(pointer.qns_cd.public_qnsd_proxy, false);
assert.equal(pointer.split_the_wires.spec, STW_SPEC);
assert.equal(pointer.cold_copy_survival.spec, CCS_SPEC);
assert.equal(pointer.hop_default_off, true);
assert.match(pointer.note, /Not AZMail's product-local ring/);
assert.match(pointer.note, /QNS-CD-1\.0/);
assert.match(pointer.note, /Not a public qnsd proxy/);

assert.equal(classifyV1Path("/v1/mesh").kind, "door");
assert.equal(classifyV1Path("/v1/mesh/nodes").originPath, "/v1/mesh/nodes");
assert.equal(classifyV1Path("/v1/mesh/enable").kind, "door");
assert.equal(localOpFromPath("/v1/mesh"), null);
assert.equal(localOpFromPath("/v1/mesh_disable"), "mesh_disable");
assert.equal(
  doorTargetUrl("/v1/mesh/nodes", "https://azmail-download-tracker.vibelock.workers.dev/v1/mesh/nodes"),
  DEFAULT_RUNTIME_ORIGIN + "/v1/mesh/nodes",
);

const html = homeHtml({ views: 0, downloads: 0, github: {} });
assert.match(html, /id="meshStrip"/);
assert.match(html, /id="meshLiveCount"/);
assert.match(html, /id="meshLine"/);
assert.match(html, /QNM-BUILD-1\.0/);
assert.match(html, /QNS-CD-1\.0/);
assert.match(html, /SPLIT THE WIRES/);
assert.match(html, /STW-1\.0/);
assert.match(html, /COLD-COPY SURVIVAL/);
assert.match(html, /CCS-1\.0/);
assert.match(html, /hop default-off/);
assert.match(html, /Live Nodes/);
assert.match(html, /No Node Gate/);
assert.match(html, /No auto-heal/);
assert.match(html, /Not an anonymity network/);
assert.match(html, /\/v1\/mesh/);
assert.match(html, /Aziel Eliab only/);
assert.match(html, /\/v1\/mesh_disable/);
assert.doesNotMatch(html, /id="node-gate"/);
assert.doesNotMatch(html, /href="\/node-gate"/);
assert.doesNotMatch(html, /auto-heal this node/);
assert.doesNotMatch(html, /\/v1\/qnsd/);
assert.doesNotMatch(html, /fetch\("\/v1\/mesh\/enable"/);
assert.match(html, /fetch\("\/v1\/mesh_enable"/);

const fetches = [];
const previousFetch = globalThis.fetch;
globalThis.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  fetches.push({ url, method: (init && init.method) || (input && input.method) || "GET" });
  return new Response(JSON.stringify({
    ok: true,
    enabled: false,
    mesh_default: "off",
    live_nodes: 0,
    rollup: { live: 0, locked: 0, isolated: 0 },
    proxied: true,
    origin: url,
  }), { status: 200, headers: { "content-type": "application/json; charset=utf-8" } });
};

try {
  const meshReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/mesh", {
    method: "GET",
    headers: { "user-agent": "Mozilla/5.0" },
  });
  const meshRes = await handleRuntimeApi(meshReq, new URL(meshReq.url), {});
  assert.ok(meshRes, "mesh path must be handled as a door proxy");
  const meshBody = await meshRes.json();
  assert.notEqual(meshBody.code, "FG-HALLUC-TOOL");
  assert.notEqual(meshBody.op, "mesh");
  assert.equal(meshBody.ok, true);
  assert.equal(meshRes.headers.get("X-Aziel-Door"), "proxy");
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/mesh" && f.method === "GET"));

  fetches.length = 0;
  const enableReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/mesh/enable", {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" },
    body: "{}",
  });
  const enableRes = await handleRuntimeApi(enableReq, new URL(enableReq.url), {});
  const enableBody = await enableRes.json();
  assert.notEqual(enableBody.code, "NOT_LOCAL_OP");
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/mesh/enable" && f.method === "POST"));

  fetches.length = 0;
  const leftoverReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/mesh_disable", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  const leftoverRes = await handleRuntimeApi(leftoverReq, new URL(leftoverReq.url), {});
  const leftoverBody = await leftoverRes.json();
  assert.equal(leftoverBody.ok, true);
  assert.equal(leftoverBody.enabled, false);
  assert.equal(leftoverBody.product, "azmail");
  assert.equal(fetches.length, 0, "leftover product mesh must not proxy to suite QNM");

  const bindingFetches = [];
  const bindingEnv = {
    AZIEL_RUNTIME: {
      fetch: async (input) => {
        const url = typeof input === "string" ? input : input.url;
        bindingFetches.push(url);
        return new Response(JSON.stringify({ ok: true, via: "binding", enabled: false }), {
          headers: { "content-type": "application/json" },
        });
      },
    },
  };
  const bindReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/mesh/nodes", {
    method: "GET",
    headers: { "user-agent": "Mozilla/5.0" },
  });
  const bindRes = await handleRuntimeApi(bindReq, new URL(bindReq.url), bindingEnv);
  const bindBody = await bindRes.json();
  assert.equal(bindBody.via, "binding");
  assert.ok(bindingFetches[0].endsWith("/v1/mesh/nodes"));

  const specReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/openapi.json", { method: "GET" });
  const specRes = await handleRuntimeApi(specReq, new URL(specReq.url), {});
  const spec = await specRes.json();
  assert.ok(spec.paths["/v1/mesh"]);
  assert.ok(spec.paths["/v1/mesh/nodes"]);
  assert.ok(spec.paths["/v1/mesh/enable"]);
  assert.ok(spec.paths["/v1/mesh_disable"]);
  assert.match(spec.info.description, /QNM-BUILD-1\.0/);
  assert.match(spec.info.description, /No Node Gate/);

  const mcpReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/mcp", { method: "GET" });
  const mcpRes = await handleRuntimeApi(mcpReq, new URL(mcpReq.url), {});
  const mcp = await mcpRes.json();
  assert.equal(mcp.mesh.pointer, true);
  assert.equal(mcp.mesh.enabled_default, false);
  assert.equal(mcp.mesh.fraggate_slug, "mesh");
  assert.equal(mcp.mesh.rollup, "live|locked|isolated");
  assert.equal(mcp.mesh.qns_cd.spec, "QNS-CD-1.0");
  assert.equal(mcp.mesh.qns_cd.public_qnsd_proxy, false);
  assert.equal(mcp.mesh.split_the_wires.spec, "STW-1.0");
  assert.equal(mcp.mesh.cold_copy_survival.spec, "CCS-1.0");
  assert.equal(mcp.mesh.hop_default_off, true);
  assert.match(mcp.note, /mesh_\*/);
  assert.match(mcp.note, /Product-local leftover ring/);

  const healthReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/health", { method: "GET" });
  const healthRes = await handleRuntimeApi(healthReq, new URL(healthReq.url), {});
  const health = await healthRes.json();
  assert.equal(health.mesh.enabled_default, false);
  assert.equal(health.mesh.identity, "Aziel Eliab");
  assert.equal(health.mesh.qns_cd.spec, "QNS-CD-1.0");
  assert.equal(health.mesh.qns_cd.public_qnsd_proxy, false);
  assert.equal(health.mesh.split_the_wires.spec, "STW-1.0");
  assert.equal(health.mesh.cold_copy_survival.spec, "CCS-1.0");
  assert.ok(health.door_proxy.includes("/v1/mesh"));
  assert.ok(health.leftover_product_mesh.includes("/v1/mesh_disable"));
  assert.ok(!health.door_proxy.includes("/v1/qnsd"));

  const openapiPaths = meshOpenApiPaths();
  assert.ok(openapiPaths["/v1/mesh"].get);
  assert.ok(openapiPaths["/v1/mesh/broadcast"].post);

  const tip = "ab".repeat(32);
  const tipB = "cd".repeat(32);
  const tick = encodeTipTick("live", tip);
  assert.equal(tick.ok, true);
  assert.equal(tick.bytes, 65);
  assert.equal(tick.payload, null);
  assert.equal(encodeTipTick("live", tip, "body").code, "STW_TIP_ONLY");
  assert.equal(admitPayload({ direction: "push" }).code, "STW_PULL_ONLY");
  assert.equal(admitPayload({ direction: "pull", hop_enabled: true }).code, "STW_HOP_DEFAULT_OFF");
  assert.equal(decideUpdate({ kind: "timer" }).apply, false);
  assert.equal(decideUpdate({ prev: tip, lockset: "LOCKSET-1" }).dwell_sec, 777);
  assert.equal(decideUpdate({ kind: "clock_desync" }).yes, false);
  assert.equal(decideUpdate({ kind: "ambiguous" }).isolate, true);
  assert.equal(equivocationEndsPeer("p", [tip, tipB]).ended, true);
  assert.equal(hopEnable().enabled, false);
  assert.equal(socketsAreSplit(SOCKET_TICK, SOCKET_DWELL).ok, true);
  assert.equal(multiplyColdCopies([{ hash: tip, cold: true }]).code, "CCS_MULTIPLY");
  assert.equal(multiplyColdCopies([{ hash: tip, cold: true }, { hash: tipB, cold: true }]).ok, true);
  assert.equal(liveBodySync().synced, false);
  assert.equal(eraseTip().erased, false);
  assert.equal(serverPull({ wipe_cold: true, replicas: [{}, {}] }).wiped, false);
  assert.equal(poisonRefuse(tip, [tip]).interpret, false);
  assert.equal(creatorGone("anon-dead", [{}, {}]).data_remains, true);
} finally {
  globalThis.fetch = previousFetch;
}

console.log("worker mesh Live Nodes / QNM / QNS-CD-1.0 / STW-1.0 / CCS-1.0 smoke ok");
