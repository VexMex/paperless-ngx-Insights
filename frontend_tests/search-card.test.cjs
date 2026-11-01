const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const { test } = require("node:test");
const source = readFileSync("custom_components/paperless_ngx_insights/www/paperless-ngx-insights.js", "utf8");
const settle = () => new Promise(resolve => setImmediate(resolve));

async function setup(callWS, config = {}) {
  const { Window } = await import("happy-dom");
  const window = new Window({ url: "http://ha-test.local/" });
  window.eval(source);
  const card = window.document.createElement("paperless-ngx-insights-search");
  card.setConfig({ entry_id: "entry-1", ...config });
  card.hass = { callWS };
  window.document.body.append(card);
  const submit = async text => {
    card.shadowRoot.querySelector("input").value = text;
    card.shadowRoot.querySelector("form").dispatchEvent(new window.Event("submit", { cancelable: true }));
    await settle();
  };
  return { window, card, submit, root: card.shadowRoot };
}

function page(count, number = 1, title = "Rechnung") {
  return { count, web_url: "http://paperless.test", documents: Array.from(
    { length: Math.min(5, Math.max(0, count - (number - 1) * 5)) },
    (_, index) => ({ id: (number - 1) * 5 + index + 1, title: `${title} ${index + 1}` })
  ) };
}

test("preview fetches with HA auth, downloads and releases blob on close", async () => {
  const { card, root, submit, window } = await setup(async () => page(1), { open_mode: "preview" });
  const revoked = [];
  window.URL.createObjectURL = () => "blob:http://ha-test.local/synthetic";
  window.URL.revokeObjectURL = url => revoked.push(url);
  let request;
  card.hass = { callWS: async () => page(1), callApiRaw: async (...args) => {
    request = args;
    return { ok: true, headers: new Map([["Content-Type", "application/pdf"]]),
      blob: async () => new window.Blob(["%PDF-1.7"], { type: "application/pdf" }) };
  } };
  await submit("invoice");
  const opener = root.querySelector("li a");
  opener.focus();
  opener.click();
  await settle();
  assert.equal(root.querySelector("dialog").open, true);
  assert.equal(request[1], "paperless_ngx_insights/entry-1/documents/1/preview");
  assert.ok(request[4]);
  assert.equal(root.querySelector("iframe").getAttribute("src"), "blob:http://ha-test.local/synthetic");
  assert.equal(root.querySelector(".preview-download").hidden, false);
  root.querySelector(".preview-close").click();
  assert.equal(root.querySelector("dialog").open, false);
  assert.deepEqual(revoked, ["blob:http://ha-test.local/synthetic"]);
  assert.equal(root.querySelector("iframe").hasAttribute("src"), false);
  assert.equal(root.activeElement, opener);
});

test("closing preview aborts requests and ignores late blobs", async () => {
  const { card, root, submit, window } = await setup(async () => page(1), { open_mode: "preview" });
  let resolve, signal;
  window.URL.createObjectURL = () => { throw new Error("must not create stale blob URL"); };
  card.hass = { callWS: async () => page(1), callApiRaw: (...args) => {
    signal = args[4];
    return new Promise(done => { resolve = done; });
  } };
  await submit("invoice");
  root.querySelector("li a").click();
  root.querySelector("dialog").dispatchEvent(new window.Event("cancel", { cancelable: true }));
  assert.equal(signal.aborted, true);
  resolve({ ok: true, headers: new Map([["Content-Type", "application/pdf"]]), blob: async () => new window.Blob(["%PDF-"]) });
  await settle();
  assert.equal(root.querySelector("iframe").hasAttribute("src"), false);
});

test("first-page image fallback keeps PDF download and releases both URLs", async () => {
  const { card, root, submit, window } = await setup(async () => page(1), { open_mode: "preview" });
  let created = 0;
  const revoked = [];
  window.URL.createObjectURL = () => `blob:http://ha-test.local/${++created}`;
  window.URL.revokeObjectURL = url => revoked.push(url);
  card.hass = { callWS: async () => page(1), callApiRaw: async (_, path) => ({
    ok: true,
    headers: new Map([["Content-Type", path.endsWith("thumbnail") ? "image/webp" : "application/pdf"]]),
    blob: async () => new window.Blob(["fixture"]),
  }) };
  await submit("invoice");
  root.querySelector("li a").click();
  await settle();
  root.querySelector(".show-thumbnail").click();
  await settle();
  assert.equal(root.querySelector("img").getAttribute("src"), "blob:http://ha-test.local/2");
  assert.equal(root.querySelector(".thumbnail-wrap").hidden, false);
  assert.equal(root.querySelector("iframe").hidden, true);
  assert.equal(root.querySelector(".preview-download").hidden, false);
  card.remove();
  assert.equal(revoked.length, 2);
});

test("unsupported or oversized previews keep the Paperless fallback", async () => {
  for (const status of [403, 413, 415, 502]) {
    const { card, root, submit } = await setup(async () => page(1), { open_mode: "preview" });
    card.hass = { callWS: async () => page(1), callApiRaw: async () => ({ ok: false, status }) };
    await submit("invoice");
    root.querySelector("li a").click();
    await settle();
    assert.equal(root.querySelector("iframe").hidden, true);
    assert.equal(root.querySelector(".paperless-link").href, "http://paperless.test/documents/1/details");
    assert.ok(root.querySelector(".preview-status").textContent.length > 20);
    root.querySelector(".preview-close").click();
  }
});

test("five titles, arrows and six-result pagination", async () => {
  const queries = [];
  const { root, submit } = await setup(async message => {
    queries.push(message);
    return page(6, message.page);
  });
  await submit("Strom");
  assert.equal(root.querySelectorAll("li").length, 5);
  assert.equal(root.querySelector(".range").textContent, "1–5 von 6");
  assert.equal(root.querySelector(".previous").disabled, true);
  assert.equal(root.querySelector(".next").disabled, false);
  root.querySelector(".next").click();
  await settle();
  assert.equal(queries[1].page, 2);
  assert.equal(root.querySelectorAll("li").length, 1);
  assert.equal(root.querySelector(".range").textContent, "6–6 von 6");
  assert.equal(root.querySelector(".next").disabled, true);
  await submit("Andere Rechnung");
  assert.equal(queries[2].page, 1);
});

test("document and configured titles are text, with safe external links", async () => {
  const malicious = '<img src=x onerror="window.pwned=1">';
  const { root, submit, window } = await setup(async () => page(1, 1, malicious), { title: malicious });
  await submit("test");
  assert.equal(root.querySelectorAll("li img,script,h2 img").length, 0);
  assert.equal(root.querySelector("h2").textContent, malicious);
  const link = root.querySelector("a");
  assert.equal(link.target, "_blank");
  assert.equal(link.rel, "noopener noreferrer");
  assert.equal(link.href, "http://paperless.test/documents/1/details");
  assert.equal(window.pwned, undefined);
});

test("mode change discards a delayed older response", async () => {
  let oldResolve;
  const { root, submit, window } = await setup(message => message.mode === "title"
    ? new Promise(resolve => { oldResolve = resolve; })
    : Promise.resolve(page(1, 1, "Aktuell")));
  await submit("test");
  root.querySelector("select").value = "text";
  root.querySelector("select").dispatchEvent(new window.Event("change"));
  await settle();
  oldResolve(page(1, 1, "Veraltet"));
  await settle();
  assert.match(root.querySelector(".title").textContent, /Aktuell/);
});

test("empty results and connection errors are readable", async () => {
  let fail = false;
  const { root, submit } = await setup(async () => {
    if (fail) throw { code: "invalid_auth" };
    return page(0);
  });
  await submit("nicht vorhanden");
  assert.match(root.querySelector(".status").textContent, /Keine Dokumente/);
  assert.equal(root.querySelector("nav").hidden, true);
  fail = true;
  await submit("test");
  assert.match(root.querySelector(".status").textContent, /Schlüssel/);
});

test("HA state updates do not issue another search", async () => {
  let calls = 0;
  const callWS = async () => { calls++; return page(1); };
  const { card, submit } = await setup(callWS);
  await submit("test");
  card.hass = { callWS, states: { "sensor.unrelated": { state: "1" } } };
  await settle();
  assert.equal(calls, 1);
});

test("reconnecting during a search restores usable controls", async () => {
  const { card, root, window, submit } = await setup(() => new Promise(() => {}));
  await submit("test");
  assert.equal(root.querySelector('button[type="submit"]').disabled, true);
  card.remove();
  window.document.body.append(card);
  assert.equal(root.querySelector('button[type="submit"]').disabled, false);
});

test("invalid search gets actionable guidance without an upstream error body", async () => {
  const { root, submit } = await setup(async () => {
    throw { code: "invalid_search", message: "private upstream data" };
  });
  await submit('telekom "rechnung');
  const status = root.querySelector(".status").textContent;
  assert.match(status, /Anführungszeichen/);
  assert.match(status, /32/);
  assert.doesNotMatch(status, /private upstream/);
});

test("oversized PDF offers streamed PDF and original downloads without a blob", async () => {
  const {card, root, submit, window} = await setup(async message => message.type.endsWith("/download")
    ? {url:`/api/paperless_ngx_insights/entry-1/documents/1/download/${message.kind}?authSig=fixture`}
    : page(1), {open_mode:"preview"});
  const urls = [];
  window.HTMLAnchorElement.prototype.click = function () { urls.push(this.href); };
  card._hass.callApiRaw = async () => ({ok:false,status:413});
  await submit("invoice");
  // Invoke the existing click listener without using the overridden anchor method.
  root.querySelector("li a").dispatchEvent(new window.MouseEvent("click", {bubbles:true,cancelable:true}));
  await settle();
  assert.match(root.querySelector(".preview-status").textContent, /20 MiB/);
  assert.equal(root.querySelector(".preview-download").hidden, false);
  assert.equal(root.querySelector(".original-download").hidden, false);
  root.querySelector(".preview-download").click(); await settle();
  root.querySelector(".original-download").click(); await settle();
  assert.equal(urls.length, 2);
  assert.ok(urls[0].includes("/download/pdf?authSig="));
  assert.ok(urls[1].includes("/download/original?authSig="));
  assert.equal(root.querySelector("iframe").hasAttribute("src"), false);
  card.remove();
});

test("download refuses an external URL and discards a late link after closing", async () => {
  const {card, root, submit, window} = await setup(async message => message.type.endsWith("/download")
    ? {url:"https://evil.test/file?authSig=fixture"} : page(1), {open_mode:"preview"});
  let navigations = 0;
  window.HTMLAnchorElement.prototype.click = function () { navigations++; };
  card._hass.callApiRaw = async () => ({ok:false,status:413});
  await submit("invoice");
  root.querySelector("li a").dispatchEvent(new window.MouseEvent("click", {bubbles:true,cancelable:true}));
  await settle();
  root.querySelector(".original-download").click(); await settle();
  assert.equal(navigations, 0);
  assert.match(root.querySelector(".preview-status").textContent, /nicht gestartet/);
  let resolve;
  card._hass.callWS = () => new Promise(done => {resolve=done;});
  root.querySelector(".original-download").click();
  root.querySelector(".preview-close").click();
  resolve({url:"/api/paperless_ngx_insights/entry-1/documents/1/download/original?authSig=fixture"});
  await settle();
  assert.equal(navigations, 0);
});
