/**
 * Prove FragGate / runtime door paths are proxied — never local ops.
 * Classify UI / leftover /v1/classify maps to FragGate op airlock_classify.
 * Author: Aziel Eliab only.
 */
import assert from "node:assert/strict";
import {
  classifyV1Path,
  DEFAULT_RUNTIME_ORIGIN,
  doorTargetUrl,
  localOpFromPath,
  mapDoorPath,
} from "../workers/download-tracker/src/door.js";
import { handleRuntimeApi, LOCAL_OP_ALIASES } from "../workers/download-tracker/src/runtime.js";
import { homeHtml } from "../workers/download-tracker/src/ui.js";

assert.equal(LOCAL_OP_ALIASES.classify, "airlock_classify");

assert.deepEqual(classifyV1Path("/v1/fraggate/call"), {
  kind: "door",
  path: "/v1/fraggate/call",
  originPath: "/v1/fraggate/call",
});
assert.deepEqual(classifyV1Path("/v1/fraggate/list"), {
  kind: "door",
  path: "/v1/fraggate/list",
  originPath: "/v1/fraggate/list",
});
assert.deepEqual(classifyV1Path("/v1/fraggate/describe"), {
  kind: "door",
  path: "/v1/fraggate/describe",
  originPath: "/v1/fraggate/describe",
});
assert.deepEqual(classifyV1Path("/v1/runtime/list"), {
  kind: "door",
  path: "/v1/runtime/list",
  originPath: "/v1/fraggate/list",
});
assert.deepEqual(classifyV1Path("/v1/runtime/call"), {
  kind: "door",
  path: "/v1/runtime/call",
  originPath: "/v1/fraggate/call",
});
assert.deepEqual(classifyV1Path("/v1/runtime/describe"), {
  kind: "door",
  path: "/v1/runtime/describe",
  originPath: "/v1/fraggate/describe",
});
assert.deepEqual(classifyV1Path("/v1/airlock_classify"), {
  kind: "local",
  path: "/v1/airlock_classify",
  op: "airlock_classify",
});
assert.deepEqual(classifyV1Path("/v1/classify"), {
  kind: "local",
  path: "/v1/classify",
  op: "classify",
});
assert.equal(localOpFromPath("/v1/fraggate/call"), null);
assert.equal(localOpFromPath("/v1/runtime/list"), null);
assert.equal(localOpFromPath("/v1/airlock_classify"), "airlock_classify");
assert.equal(mapDoorPath("/v1/runtime/list"), "/v1/fraggate/list");
assert.equal(mapDoorPath("/v1/runtime/describe"), "/v1/fraggate/describe");
assert.equal(
  doorTargetUrl("/v1/fraggate/call", "https://azmail-download-tracker.vibelock.workers.dev/v1/fraggate/call"),
  DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/call",
);
assert.equal(
  doorTargetUrl("/v1/runtime/list", "https://example.test/v1/runtime/list?x=1"),
  DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/list?x=1",
);
assert.equal(classifyV1Path("/v1/mesh").kind, "door");
assert.equal(classifyV1Path("/v1/mesh/nodes").kind, "door");
assert.equal(classifyV1Path("/v1/mesh/disable").kind, "door");
assert.equal(classifyV1Path("/v1/mesh_disable").kind, "local");
assert.equal(classifyV1Path("/v1/mesh_disable").op, "mesh_disable");
assert.equal(localOpFromPath("/v1/mesh"), null);
assert.equal(classifyV1Path("/v1/not/a/door").kind, "multi");
assert.equal(classifyV1Path("/count").kind, "none");
assert.equal(classifyV1Path("/stats").kind, "none");
assert.equal(classifyV1Path("/download").kind, "none");

const envOrigin = "https://aziel-runtime.example.test";
assert.equal(
  doorTargetUrl("/v1/fraggate/call", "https://local/v1/fraggate/call", { AZIEL_RUNTIME_ORIGIN: envOrigin }),
  envOrigin + "/v1/fraggate/call",
);

const page = homeHtml({ views: 1, downloads: 1, github: {} });
assert.match(page, /\/v1\/airlock_classify/);
assert.match(page, />airlock_classify</);
assert.doesNotMatch(page, /fetch\("\/v1\/classify"/);

const fetches = [];
const previousFetch = globalThis.fetch;
globalThis.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  fetches.push({ url, method: (init && init.method) || (input && input.method) || "GET" });
  return new Response(JSON.stringify({ ok: true, door: "fraggate", proxied: true, origin: url }), {
    status: 200,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
};

try {
  const callReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/fraggate/call", {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" },
    body: JSON.stringify({ slug: "azmail", op: "airlock_classify", payload: {} }),
  });
  const callRes = await handleRuntimeApi(callReq, new URL(callReq.url), {});
  assert.ok(callRes, "door path must be handled");
  const callBody = await callRes.json();
  assert.notEqual(callBody.code, "FG-HALLUC-TOOL");
  assert.notEqual(callBody.op, "fraggate/call");
  assert.notEqual(callBody.error, "unknown op");
  assert.equal(callBody.ok, true);
  assert.equal(callBody.proxied, true);
  assert.equal(callRes.headers.get("X-Aziel-Door"), "proxy");
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/call" && f.method === "POST"));

  fetches.length = 0;
  const listReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/fraggate/list", {
    method: "GET",
    headers: { "user-agent": "Mozilla/5.0" },
  });
  const listRes = await handleRuntimeApi(listReq, new URL(listReq.url), {});
  const listBody = await listRes.json();
  assert.notEqual(listBody.code, "FG-HALLUC-TOOL");
  assert.equal(listBody.ok, true);
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/list"));

  fetches.length = 0;
  const descReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/fraggate/describe?slug=azmail", {
    method: "GET",
    headers: { "user-agent": "Mozilla/5.0" },
  });
  const descRes = await handleRuntimeApi(descReq, new URL(descReq.url), {});
  const descBody = await descRes.json();
  assert.equal(descBody.ok, true);
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/describe?slug=azmail"));

  fetches.length = 0;
  const aliasReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/runtime/call", {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" },
    body: JSON.stringify({ slug: "azmail", op: "airlock_classify", payload: {} }),
  });
  const aliasRes = await handleRuntimeApi(aliasReq, new URL(aliasReq.url), {});
  const aliasBody = await aliasRes.json();
  assert.notEqual(aliasBody.code, "FG-HALLUC-TOOL");
  assert.notEqual(aliasBody.op, "runtime/call");
  assert.ok(fetches.some((f) => f.url === DEFAULT_RUNTIME_ORIGIN + "/v1/fraggate/call"));

  const bindingFetches = [];
  const bindingEnv = {
    AZIEL_RUNTIME: {
      fetch: async (input) => {
        const url = typeof input === "string" ? input : input.url;
        bindingFetches.push(url);
        return new Response(JSON.stringify({ ok: true, via: "binding" }), {
          headers: { "content-type": "application/json" },
        });
      },
    },
  };
  const bindReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/fraggate/call", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ slug: "azmail", op: "skill", payload: {} }),
  });
  const bindRes = await handleRuntimeApi(bindReq, new URL(bindReq.url), bindingEnv);
  const bindBody = await bindRes.json();
  assert.equal(bindBody.via, "binding");
  assert.ok(bindingFetches[0].endsWith("/v1/fraggate/call"));

  const payload = {
    from: "help@paypa1-verify.com",
    subject: "URGENT verify your account",
    body_text: "reset your password immediately",
  };
  const localReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/airlock_classify", {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" },
    body: JSON.stringify(payload),
  });
  const localRes = await handleRuntimeApi(localReq, new URL(localReq.url), {});
  const localBody = await localRes.json();
  assert.equal(localBody.ok, true);
  assert.equal(localBody.op, "airlock_classify");
  assert.equal(localBody.product, "azmail");
  assert.ok(localBody.verdict);

  const leftoverReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/classify", {
    method: "POST",
    headers: { "content-type": "application/json", "user-agent": "Mozilla/5.0" },
    body: JSON.stringify(payload),
  });
  const leftoverRes = await handleRuntimeApi(leftoverReq, new URL(leftoverReq.url), {});
  const leftoverBody = await leftoverRes.json();
  assert.equal(leftoverBody.op, "airlock_classify");
  assert.equal(leftoverBody.verdict, localBody.verdict);

  const healthReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/health", {
    method: "GET",
    headers: { "user-agent": "Mozilla/5.0" },
  });
  const healthRes = await handleRuntimeApi(healthReq, new URL(healthReq.url), {});
  const healthBody = await healthRes.json();
  assert.equal(healthBody.ok, true);
  assert.equal(healthBody.product, "azmail");
  assert.equal(healthBody.classify_op, "airlock_classify");

  const meshReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/mesh_disable", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  const meshRes = await handleRuntimeApi(meshReq, new URL(meshReq.url), {});
  const meshBody = await meshRes.json();
  assert.equal(meshBody.ok, true);
  assert.equal(meshBody.enabled, false);
  assert.equal(meshBody.product, "azmail");

  const multiReq = new Request("https://azmail-download-tracker.vibelock.workers.dev/v1/not/a/door", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: "{}",
  });
  const multiRes = await handleRuntimeApi(multiReq, new URL(multiReq.url), {});
  const multiBody = await multiRes.json();
  assert.equal(multiBody.code, "NOT_LOCAL_OP");
  assert.notEqual(multiBody.code, "FG-HALLUC-TOOL");
  assert.notEqual(multiBody.op, "not/a/door");

  for (const path of ["/count", "/stats", "/download", "/"]) {
    const req = new Request("https://azmail-download-tracker.vibelock.workers.dev" + path, { method: "GET" });
    const res = await handleRuntimeApi(req, new URL(req.url), {});
    assert.equal(res, null, path + " must stay on the download tracker, not the runtime router");
  }
} finally {
  globalThis.fetch = previousFetch;
}

console.log("worker door proxy + airlock_classify smoke ok");
