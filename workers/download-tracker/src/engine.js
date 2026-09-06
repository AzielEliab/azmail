/**
 * AZMail APP 1.0 — hosted advisory engine (demo).
 * Mirrors the Python airlock/scrub/mesh contract. Not a public MTA.
 */

export const VERSION = "0.1.0";
export const SPEC = "azmail-app-1.0";
export const LIMITATION =
  "THIS IS: a local Mail Airlock plus advisory APP 1.0 layers and mesh client helpers. THIS IS NOT: a public MTA, SMTP/IMAP server, mixnet, VPN, or a guaranteed phishing block. v0.1 does not send internet email. Hosted Worker is a counted download + human UI + demo HTTP. The AI / MCP path is FragGate only: POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call with slug=azmail — not a separate mail MCP. Engine lands in a sibling PR. No hard dependency on AZ-OS, Lumen, or a separate interface product. Author: Aziel Eliab only.";

export const RUNTIME = "https://aziel-runtime.vibelock.workers.dev";
export const FRAGGATE = "https://github.com/AzielEliab/fraggate";

const BRANDS = [
  "paypal", "apple", "microsoft", "google", "gmail", "amazon", "bankofamerica",
  "wellsfargo", "chase", "irs", "netflix", "facebook", "instagram", "whatsapp",
  "docusign", "adobe", "outlook", "office365", "icloud", "dropbox",
];
const KNOWN_PHISH = new Set([
  "secure-paypal-login.tk",
  "paypa1-verify.com",
  "g00gle-account.net",
  "micros0ft-support.xyz",
  "amaz0n-billing.cc",
  "phish.example",
  "login-appleid-secure.top",
]);
const URGENCY = ["urgent", "immediately", "act now", "account suspended", "verify within", "final notice", "within 24 hours", "your account will be closed"];
const CREDS = ["password", "passcode", "login", "sign in", "ssn", "otp", "2fa", "verify your account", "reset your password", "security code"];
const PAYMENT = ["wire transfer", "gift card", "bitcoin", "crypto", "invoice overdue", "payment required", "western union", "zelle"];

function domainOf(addr) {
  let t = String(addr || "").trim().toLowerCase();
  if (t.includes("@")) t = t.split("@").pop();
  t = t.replace(/[<>\s"']/g, "");
  if (t.startsWith("www.")) t = t.slice(4);
  return t;
}

function registrable(domain) {
  const parts = domainOf(domain).split(".").filter(Boolean);
  return parts.length >= 2 ? parts[parts.length - 2] : parts[0] || "";
}

function levenshtein(a, b) {
  if (a === b) return 0;
  const prev = [...Array(b.length + 1).keys()];
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] !== b[j - 1]));
    }
    for (let j = 0; j <= b.length; j++) prev[j] = cur[j];
  }
  return prev[b.length];
}

function foldLeet(s) {
  return s.replace(/0/g, "o").replace(/1/g, "l").replace(/3/g, "e").replace(/4/g, "a").replace(/5/g, "s").replace(/7/g, "t");
}

function lookalike(domain) {
  const name = registrable(domain);
  const folded = foldLeet(name);
  const matches = [];
  for (const brand of BRANDS) {
    if (name === brand) continue;
    if (folded === brand || name.replace(/-/g, "") === brand) {
      matches.push({ brand, reason: "homoglyph_or_leet" });
      continue;
    }
    if (name.includes(brand) && name !== brand) {
      matches.push({ brand, reason: "brand_plus_extra" });
      continue;
    }
    const dist = Math.min(levenshtein(name, brand), levenshtein(folded, brand));
    if (dist > 0 && dist <= 2 && name.length >= 4) matches.push({ brand, reason: "edit_distance", distance: dist });
  }
  return { domain: domainOf(domain), lookalike: matches.length > 0, matches: matches.slice(0, 5) };
}

function hits(text, list) {
  const low = String(text || "").toLowerCase();
  return list.filter((p) => low.includes(p));
}

export function adviseSourceAuth(headers) {
  const raw = String((headers && (headers["Authentication-Results"] || headers["authentication-results"])) || "");
  const results = {};
  for (const m of raw.matchAll(/\b(spf|dkim|dmarc)=(pass|fail|softfail|neutral|none|unknown)\b/gi)) {
    results[m[1].toLowerCase()] = m[2].toLowerCase();
  }
  let verdict = "unverified";
  if (results.spf === "pass") verdict = "pass";
  if (results.spf === "fail" || results.dkim === "fail" || results.dmarc === "fail") verdict = "fail";
  if (!raw) verdict = "unverified";
  return { layer: "source_auth", advisory: true, verdict, authentication_results: { spf: results.spf || "unknown", dkim: results.dkim || "unknown", dmarc: results.dmarc || "unknown" } };
}

export function classify(message) {
  const from = String(message.from || message.from_addr || "");
  const subject = String(message.subject || "");
  const body = String(message.body_text || message.body || "") + "\n" + String(message.body_html || message.html || "");
  const host = domainOf(from);
  const auth = adviseSourceAuth(message.headers || {});
  const alike = lookalike(host);
  const known = KNOWN_PHISH.has(host);
  const urgency = hits(subject + "\n" + body, URGENCY);
  const creds = hits(subject + "\n" + body, CREDS);
  const payment = hits(subject + "\n" + body, PAYMENT);
  const flags = [];
  let risk = 0;
  if (known) { flags.push("known_phish"); risk += 80; }
  if (alike.lookalike) { flags.push("lookalike"); risk += 40; }
  if (urgency.length) { flags.push("urgency"); risk += 20; }
  if (creds.length) { flags.push("credentials"); risk += 35; }
  if (payment.length) { flags.push("payment_language"); risk += 25; }
  if (auth.verdict === "fail") risk += 25;
  if (auth.verdict === "unverified" || auth.verdict === "unknown") { flags.push("source_unverified"); risk += 10; }
  risk = Math.min(100, risk);
  const credPhish = flags.includes("credentials") && (flags.includes("urgency") || alike.lookalike);
  let verdict = "hold";
  let badge = "unverified";
  let confirm = false;
  if (known || (credPhish && risk >= 70)) {
    verdict = "quarantine"; badge = "quarantined"; confirm = true;
  } else if (risk >= 45 || flags.includes("lookalike")) {
    verdict = "confirm"; badge = "high-risk"; confirm = true;
  } else if (auth.verdict === "pass" && risk < 20 && !flags.filter((f) => f !== "html_scrubbed").length) {
    verdict = "release"; badge = "verified"; confirm = false;
  }
  return {
    product: "azmail",
    version: VERSION,
    spec: SPEC,
    kv_increment: false,
    stored: false,
    limitation: LIMITATION,
    verdict,
    badge,
    risk,
    requires_confirmation: confirm,
    flags: [...new Set(flags)],
    layers: {
      source_auth: auth,
      reputation: { domain: host, known_phish: known, lookalike: alike, risk: known ? 80 : alike.lookalike ? 40 : 0 },
      behavior: { urgency, credentials: creds, payment, flags: flags.filter((f) => ["urgency", "credentials", "payment_language"].includes(f)) },
    },
    note: "No message is trusted until verified across identity, origin, structure, and behavior.",
    aspirational: { inbox_delay: "<1s (target)", scan: "parallel layers", link_analysis: "real-time sandbox rewrite" },
  };
}

export function scrubHtml(html) {
  const stripped = [];
  let text = String(html || "");
  const drop = (re, label) => {
    const m = text.match(re);
    if (m) {
      stripped.push(...Array(m.length).fill(label));
      text = text.replace(re, "");
    }
  };
  drop(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, "script");
  drop(/<(?:iframe|object|embed|form)\b[^>]*>[\s\S]*?<\/(?:iframe|object|embed|form)\s*>/gi, "embed");
  drop(/<meta\b[^>]*http-equiv\s*=\s*['"]?refresh[^>]*>/gi, "meta_refresh");
  if (/\son[a-z]+\s*=/i.test(text)) {
    stripped.push("event_handler");
    text = text.replace(/\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
  }
  if (/href\s*=\s*['"]\s*javascript:/i.test(text)) {
    stripped.push("javascript_href");
    text = text.replace(/href\s*=\s*['"]\s*javascript:[^'"]*['"]/gi, 'href="#azmail-blocked-javascript"');
  }
  text = text.replace(/<img\b[^>]*>/gi, (tag) => {
    const low = tag.toLowerCase();
    if (/(width|height)\s*=\s*['"]?1\b/.test(low) || low.includes("1x1") || low.includes("pixel") || low.includes("/track")) {
      stripped.push("tracking_pixel");
      return "<!-- azmail: tracking pixel stripped -->";
    }
    return tag;
  });
  text = text.replace(/<a\b[^>]*style\s*=\s*['"][^'"]*(display\s*:\s*none|font-size\s*:\s*0)[^'"]*['"][^>]*>[\s\S]*?<\/a\s*>/gi, () => {
    stripped.push("hidden_redirect");
    return "";
  });
  text = text.replace(/href\s*=\s*['"]([^'"]+)['"]/gi, (all, url) => {
    try {
      const u = new URL(url, "https://azmail.local");
      if (["bit.ly", "t.co", "tinyurl.com"].includes(u.hostname)) {
        stripped.push("shortener:" + u.hostname);
        return 'href="#azmail-isolated-shortener"';
      }
      let changed = false;
      for (const key of [...u.searchParams.keys()]) {
        if (/^(utm_|fbclid|gclid|mc_cid|mc_eid)/i.test(key)) {
          u.searchParams.delete(key);
          changed = true;
        }
      }
      if (changed) {
        stripped.push("tracking_query");
        return `href="${u.toString()}"`;
      }
    } catch {
      /* keep */
    }
    return all;
  });
  return {
    product: "azmail",
    version: VERSION,
    spec: SPEC,
    kv_increment: false,
    stored: false,
    limitation: LIMITATION,
    html: text,
    stripped,
    stripped_kinds: [...new Set(stripped)],
    changed: text !== String(html || ""),
  };
}

export function matchKeywords(text, keywords) {
  const blob = String(text || "").toLowerCase();
  return (keywords || [])
    .map((k) => String(k).trim().toLowerCase())
    .filter((k) => k && blob.includes(k))
    .map((keyword) => ({ keyword, matched: true, identity: null, note: "Alert without revealing identity." }));
}

export function refuseReason(text) {
  const blob = String(text || "");
  if (/\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b/i.test(blob)) return "mesh_refuse_pii: email-shaped handle or body";
  if (/\bpassword\s*[:=]/i.test(blob) || /\bapi[_-]?key\s*[:=]/i.test(blob)) return "mesh_refuse_credential_harvest";
  if (/\bdoxx|\blives at\b|\bhome address\b/i.test(blob)) return "mesh_refuse_doxxing";
  return null;
}

export function meshStub(op, payload, enabled) {
  const base = {
    product: "azmail",
    version: VERSION,
    door: "fraggate",
    runtime: RUNTIME,
    kernel: FRAGGATE,
    call: `POST https://aziel-runtime.vibelock.workers.dev/v1/fraggate/call {"slug":"azmail","op":"${op}","payload":{}}`,
    note: "Engine lands in a sibling aziel-runtime PR. This Worker stub does not run a live mesh.",
    limitation: LIMITATION,
    kv_increment: false,
    stored: false,
  };
  if (op === "mesh_disable") return { ok: true, enabled: false, ...base };
  if (op === "mesh_enable") return { ok: true, enabled: true, handle: "anon-hosted", ...base };
  if (!enabled && (op === "broadcast" || op === "listen")) {
    return { ok: false, code: "MESH_DISABLED", enabled: false, ...base };
  }
  const reason = refuseReason((payload && payload.text) || "");
  if (reason) return { ok: false, code: "MESH_REFUSE", reason, ...base };
  if (op === "keyword_alerts") {
    return { ok: true, alerts: matchKeywords(payload && payload.text, payload && payload.keywords), identity: null, ...base };
  }
  return { ok: true, enabled: !!enabled, queued: op === "broadcast", ...base };
}
