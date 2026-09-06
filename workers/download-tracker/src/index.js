import { handleRuntimeApi } from "./runtime.js";
import { homeHtml } from "./ui.js";

/**
 * AZMail download tracker (Cloudflare Worker).
 *
 * GET / increments page-view counter, complete mail UI + Views/Downloads
 * GET /download increments downloads, serves tarball via env.ASSETS.fetch (no 302)
 * GET /count {views, downloads, total}
 * /v1 does not increment.
 *
 * Isolated: Worker azmail-download-tracker, KV AZMAIL_DOWNLOADS.
 */

const PROJECT = "azmail";
const DEFAULT_ASSET = "azmail-0.1.0.tar.gz";
const DEFAULT_OWNER = "AzielEliab";
const DEFAULT_REPO = "azmail";
const DEFAULT_BRANCH = "main";
const HOST = "https://azmail-download-tracker.vibelock.workers.dev";
const GITHUB_REPO = "https://github.com/AzielEliab/azmail";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Protocol-Version, mcp-session-id, User-Agent, Authorization",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}

function splitOwnerRepo(value, fallbackOwner, fallbackRepo) {
  if (typeof value === "string" && value.includes("/")) {
    const [o, r] = value.split("/").filter(Boolean);
    if (o && r) return { owner: o, repo: r };
  }
  return { owner: fallbackOwner, repo: fallbackRepo };
}

function parseDims(src) {
  const get = (k) => {
    if (src == null) return null;
    if (typeof src.get === "function") {
      const v = src.get(k);
      return v == null || v === "" ? null : v;
    }
    const v = src[k];
    return v == null || v === "" ? null : v;
  };
  let owner = get("owner") || DEFAULT_OWNER;
  let repo = get("repo") || DEFAULT_REPO;
  if (typeof repo === "string" && repo.includes("/")) {
    const split = splitOwnerRepo(repo, owner, DEFAULT_REPO);
    owner = split.owner;
    repo = split.repo;
  }
  const branch = get("branch") || DEFAULT_BRANCH;
  const tag = get("tag") || "latest";
  const asset = get("asset") || "";
  const forkRaw = get("fork");
  let fork = "0";
  if (forkRaw === 1 || forkRaw === true || forkRaw === "1" || forkRaw === "true") fork = "1";
  else if (typeof forkRaw === "string" && forkRaw.includes("/")) {
    const split = splitOwnerRepo(forkRaw, owner, repo);
    owner = split.owner;
    repo = split.repo;
    fork = "1";
  } else if (forkRaw != null && forkRaw !== 0 && forkRaw !== false && forkRaw !== "0" && forkRaw !== "false") {
    fork = "1";
  }
  if (`${owner}/${repo}`.toLowerCase() !== `${DEFAULT_OWNER}/${DEFAULT_REPO}`.toLowerCase()) fork = "1";
  return { project: PROJECT, owner, repo, branch, fork, tag, asset };
}

function kvKey(dims) {
  return `${dims.project}|${dims.owner}|${dims.repo}|${dims.branch}|${dims.fork}`;
}
function totalKey() { return PROJECT + "|__total__"; }
function viewsKey() { return PROJECT + "|__views__"; }
function githubCacheKey() { return PROJECT + "|__github__"; }

async function increment(env, dims) {
  if (!env.DOWNLOADS) return 0;
  const key = kvKey(dims);
  const n = parseInt((await env.DOWNLOADS.get(key)) || "0", 10) + 1;
  await env.DOWNLOADS.put(key, String(n));
  const tot = parseInt((await env.DOWNLOADS.get(totalKey())) || "0", 10) + 1;
  await env.DOWNLOADS.put(totalKey(), String(tot));
  return tot;
}

async function incrementViews(env) {
  if (!env.DOWNLOADS) return 0;
  const n = parseInt((await env.DOWNLOADS.get(viewsKey())) || "0", 10) + 1;
  await env.DOWNLOADS.put(viewsKey(), String(n));
  return n;
}

async function listAllKeys(env) {
  if (!env.DOWNLOADS) return [];
  const keys = [];
  let cursor;
  do {
    const page = await env.DOWNLOADS.list(cursor ? { cursor } : {});
    keys.push(...page.keys);
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  return keys;
}

async function githubStats(env) {
  if (env.DOWNLOADS) {
    const cached = await env.DOWNLOADS.get(githubCacheKey());
    if (cached) {
      try {
        const obj = JSON.parse(cached);
        if (obj && obj.fetched_at && Date.now() - obj.fetched_at < 5 * 60 * 1000) return obj;
      } catch { /* ignore */ }
    }
  }
  const headers = { "User-Agent": "Mozilla/5.0 AZMail-download-tracker", Accept: "application/vnd.github+json" };
  let stars = 0, forks = 0, watchers = 0, release_download_count = 0;
  try {
    const repoRes = await fetch("https://api.github.com/repos/AzielEliab/azmail", { headers });
    if (repoRes.ok) {
      const repo = await repoRes.json();
      stars = Number(repo.stargazers_count) || 0;
      forks = Number(repo.forks_count) || 0;
      watchers = Number(repo.subscribers_count != null ? repo.subscribers_count : repo.watchers_count) || 0;
    }
  } catch { /* public API */ }
  const out = { stars, forks, watchers, release_download_count, fetched_at: Date.now() };
  try { if (env.DOWNLOADS) await env.DOWNLOADS.put(githubCacheKey(), JSON.stringify(out)); } catch { /* ignore */ }
  return out;
}

async function collectStats(env) {
  const keys = await listAllKeys(env);
  let summed = 0;
  const by_repo = {};
  const by_branch = {};
  const by_fork = { "0": 0, "1": 0 };
  const breakdown = [];
  for (const k of keys) {
    const name = k.name;
    if (name === viewsKey() || name === totalKey() || name === githubCacheKey()) continue;
    const n = parseInt((await env.DOWNLOADS.get(name)) || "0", 10);
    if (!Number.isFinite(n) || n <= 0) continue;
    const parts = name.split("|");
    if (parts.length < 5) continue;
    const [project, owner, repo, branch, fork] = parts;
    summed += n;
    const repoId = `${owner}/${repo}`;
    by_repo[repoId] = (by_repo[repoId] || 0) + n;
    by_branch[branch] = (by_branch[branch] || 0) + n;
    const forkFlag = fork === "1" ? "1" : "0";
    by_fork[forkFlag] = (by_fork[forkFlag] || 0) + n;
    breakdown.push({ project, owner, repo, branch, fork: forkFlag, count: n });
  }
  const downloadsDirect = env.DOWNLOADS ? parseInt((await env.DOWNLOADS.get(totalKey())) || "0", 10) : 0;
  const downloads = Number.isFinite(downloadsDirect) && downloadsDirect > 0 ? downloadsDirect : summed;
  const views = env.DOWNLOADS ? parseInt((await env.DOWNLOADS.get(viewsKey())) || "0", 10) || 0 : 0;
  const github = await githubStats(env);
  return {
    project: PROJECT,
    views,
    downloads,
    total: downloads,
    by_repo,
    by_branch,
    by_fork,
    breakdown,
    github: { stars: github.stars || 0, forks: github.forks || 0, watchers: github.watchers || 0, release_download_count: github.release_download_count || 0 },
    note: "Isolated AZMail counter. /v1 does not increment.",
  };
}

function installScript() {
  return `#!/usr/bin/env bash
# AZMail one-click install. Counted download via this Worker.
set -euo pipefail
HOST="${HOST}"
ASSET="${DEFAULT_ASSET}"
WORKDIR="\${AZMAIL_HOME:-\$HOME/azmail}"
mkdir -p "\$WORKDIR"
cd "\$WORKDIR"
echo "Downloading counted tarball from \${HOST}/download (User-Agent Mozilla/5.0)…"
curl -fsSL -A 'Mozilla/5.0' "\${HOST}/download?asset=\${ASSET}" -o "\${ASSET}"
tar -xzf "\${ASSET}"
DIR="\$(find . -maxdepth 1 -type d -name 'azmail-*' | head -n 1)"
if [ -n "\${DIR}" ]; then
  cd "\${DIR}"
fi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
echo
echo "Installed AZMail."
echo "Run: azmail ui"
echo "Then open http://127.0.0.1:8876 (loopback only)"
echo "v0.1 does not send internet email. Author: Aziel Eliab."
`;
}

async function serveAsset(request, env, asset, { head = false } = {}) {
  if (!env.ASSETS) return json({ error: "assets binding missing" }, 500);
  const assetUrl = new URL("/" + asset, request.url);
  const assetRes = await env.ASSETS.fetch(new Request(assetUrl, { method: "GET" }));
  if (!assetRes.ok) return json({ error: "asset not hosted", asset, status: assetRes.status }, 404);
  const headers = new Headers();
  headers.set("Content-Type", "application/gzip");
  headers.set("Content-Disposition", 'attachment; filename="' + asset.replaceAll('"', "") + '"');
  headers.set("Cache-Control", "private, no-store");
  const len = assetRes.headers.get("Content-Length");
  if (len) headers.set("Content-Length", len);
  for (const [k, v] of Object.entries(corsHeaders())) headers.set(k, v);
  if (head) return new Response(null, { status: 200, headers });
  return new Response(assetRes.body, { status: 200, headers });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders() });

    const runtime = await handleRuntimeApi(request, url, env);
    if (runtime) return runtime;

    if ((url.pathname === "/install.sh" || url.pathname === "/install.sh/") && (request.method === "GET" || request.method === "HEAD")) {
      return new Response(request.method === "HEAD" ? null : installScript(), {
        status: 200,
        headers: { "Content-Type": "text/x-shellscript; charset=utf-8", "Cache-Control": "private, no-store", ...corsHeaders() },
      });
    }

    if (url.pathname === "/" && request.method === "GET") {
      await incrementViews(env);
      const stats = await collectStats(env);
      return new Response(homeHtml({ views: stats.views, downloads: stats.downloads, github: stats.github }), {
        headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() },
      });
    }
    if (url.pathname === "/" && request.method === "HEAD") {
      return new Response(null, { status: 200, headers: { "Content-Type": "text/html; charset=utf-8", ...corsHeaders() } });
    }

    if (url.pathname === "/count" && request.method === "GET") {
      const stats = await collectStats(env);
      return json({ project: PROJECT, views: stats.views || 0, downloads: stats.downloads || 0, total: stats.total || 0 });
    }
    if (url.pathname === "/stats" && request.method === "GET") return json(await collectStats(env));

    if (url.pathname === "/event" && request.method === "POST") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "JSON body required" }, 400); }
      const dims = parseDims(body || {});
      const count = await increment(env, dims);
      return json({ ok: true, key: kvKey(dims), count, owner: dims.owner, repo: dims.repo, branch: dims.branch, fork: dims.fork, asset: dims.asset || null });
    }

    if ((url.pathname === "/download" || url.pathname.startsWith("/download/") || url.pathname === "/go") && (request.method === "GET" || request.method === "HEAD")) {
      const dims = parseDims(url.searchParams);
      if (!dims.asset && url.pathname.startsWith("/download/")) {
        dims.asset = decodeURIComponent(url.pathname.slice("/download/".length));
      }
      const asset = dims.asset || DEFAULT_ASSET;
      dims.asset = asset;
      if (request.method === "GET") await increment(env, dims);
      return serveAsset(request, env, asset, { head: request.method === "HEAD" });
    }

    if ((url.pathname === "/robots.txt" || url.pathname === "/robots.txt/") && request.method === "GET") {
      const body = ["User-agent: *", "Allow: /", "Sitemap: " + HOST + "/sitemap.xml", ""].join("\n");
      return new Response(body, {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8", ...corsHeaders() },
      });
    }
    if ((url.pathname === "/sitemap.xml" || url.pathname === "/sitemap.xml/") && request.method === "GET") {
      const locs = [HOST + "/", HOST + "/download", HOST + "/install.sh", HOST + "/v1/skill", HOST + "/v1/fraggate/list", HOST + "/v1/mesh", HOST + "/openapi.json", HOST + "/mcp", GITHUB_REPO];
      const xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + locs.map((u) => "  <url><loc>" + u + "</loc></url>").join("\n")
        + "\n</urlset>\n";
      return new Response(xml, {
        status: 200,
        headers: { "Content-Type": "application/xml; charset=utf-8", ...corsHeaders() },
      });
    }
    if ((url.pathname === "/cite.json" || url.pathname === "/cite.json/") && request.method === "GET") {
      return json({
        author: "Aziel Eliab",
        title: "AZMail",
        version: "0.1.0",
        github: GITHUB_REPO,
        download: HOST + "/download",
        license: "Apache-2.0",
        catalog: "https://aziel-runtime.vibelock.workers.dev/",
        note: "Do not invent a DOI.",
      });
    }
    return json({ error: "not found" }, 404);
  },
};
