/**
 * Suite mesh Live Nodes + QNM-BUILD-1.0 contract.
 * Default OFF. live|locked|isolated. No Node Gate. No auto-heal. Not anonymity.
 * Product-local leftover ring stays off /v1/mesh/* .
 * Author: Aziel Eliab only.
 */
import assert from "node:assert/strict";
import {
  QNM_SPEC,
  MESH_DEFAULT_OFF,
  MESH_ANONYMITY_NETWORK,
  MESH_NODE_GATE,
  MESH_AUTO_HEAL,
  MESH_OPS,
  MESH_PATH,
  MESH_IDENTITY,
  PRODUCT_MESH_DISABLE,
  alignLiveNodes,
  emptyMesh,
  meshOpenApiPaths,
  meshPointer,
  meshStatusLine,
  parseMeshDoc,
  publicMesh,
} from "../workers/download-tracker/src/mesh.js";
import { classifyV1Path, DEFAULT_RUNTIME_ORIGIN, doorTargetUrl, localOpFromPath } from "../workers/download-tracker/src/door.js";
import { handleRuntimeApi } from "../workers/download-tracker/src/runtime.js";
import { homeHtml } from "../workers/download-tracker/src/ui.js";

assert.equal(QNM_SPEC, "QNM-BUILD-1.0");
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
assert.match(meshStatusLine(pub), /Suite mesh: on · live 2 · locked 1 · isolated 3/);
assert.match(meshStatusLine(emptyMesh()), /Suite mesh: off \(default\)\. QNM-BUILD-1\.0/);
assert.equal(alignLiveNodes({ mesh: { enabled: true, rollup: { live: 4, locked: 1, isolated: 0 } } }), 4);
assert.equal(alignLiveNodes({ mesh: { enabled: false, live_nodes: 9 } }), 0);

const pointer = meshPointer();
assert.equal(pointer.enabled_default, false);
assert.equal(pointer.rollup, "live|locked|isolated");
assert.equal(pointer.fraggate_slug, "mesh");
assert.equal(pointer.node_gate, false);
assert.equal(pointer.auto_heal, false);
assert.equal(pointer.anonymity_network, false);
assert.match(pointer.note, /Not AZMail's product-local ring/);

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
  assert.match(mcp.note, /mesh_\*/);
  assert.match(mcp.note, /Product-local leftover ring/);

  const healthReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/health", { method: "GET" });
  const healthRes = await handleRuntimeApi(healthReq, new URL(healthReq.url), {});
  const health = await healthRes.json();
  assert.equal(health.mesh.enabled_default, false);
  assert.equal(health.mesh.identity, "Aziel Eliab");
  assert.ok(health.door_proxy.includes("/v1/mesh"));
  assert.ok(health.leftover_product_mesh.includes("/v1/mesh_disable"));

  const openapiPaths = meshOpenApiPaths();
  assert.ok(openapiPaths["/v1/mesh"].get);
  assert.ok(openapiPaths["/v1/mesh/broadcast"].post);
} finally {
  globalThis.fetch = previousFetch;
}

console.log("worker mesh Live Nodes / QNM smoke ok");
