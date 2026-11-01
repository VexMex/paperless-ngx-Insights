const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const { test } = require("node:test");
const source = readFileSync("custom_components/paperless_ngx_insights/www/paperless-ngx-insights.js", "utf8");
const settle = () => new Promise(resolve => setImmediate(resolve));

async function setup(config = {}, api = {}) {
  const { Window } = await import("happy-dom");
  const window = new Window({ url: "http://ha-test.local" });
  // Drive lazy visibility deterministically in these DOM tests.
  window.IntersectionObserver = undefined;
  window.document.documentElement.lang = "de";
  window.eval(source);
  let nextUrl = 0;
  const revoked = [];
  window.URL.createObjectURL = () => `blob:http://ha-test.local/${++nextUrl}`;
  window.URL.revokeObjectURL = url => revoked.push(url);
  const card = window.document.createElement("paperless-ngx-insights-documents");
  const queries = [];
  const page = message => ({ count: 11, web_url: "http://paperless.test", documents: Array.from({length: message.page === 1 ? 10 : 1}, (_, i) => ({id: (message.page - 1) * 10 + i + 1, title: `<b>Dokument ${i}</b>`, created: "2026-05-01"})) });
  card.setConfig({ entry_id: "fixture", ...config });
  card.hass = {
    callWS: async message => { queries.push(message); return page(message); },
    callApiRaw: async (_, path) => ({ ok: true, headers: new Map([["Content-Type", path.endsWith("thumbnail") ? "image/webp" : "application/pdf"]]), blob: async () => new window.Blob(["synthetic"]) }),
    ...api,
  };
  window.document.body.append(card);
  const root = card.shadowRoot;
  const search = async text => {
    root.querySelector("input").value = text;
    root.querySelector("form").dispatchEvent(new window.Event("submit", {cancelable:true}));
    for (let i = 0; i < 5; i++) await settle();
  };
  return {window, card, root, queries, revoked, search};
}

test("large card shares search, shows dates/thumbnails and embeds selection without modal", async () => {
  const {card, root, queries, search} = await setup();
  await search("invoice");
  assert.equal(queries[0].page_size, 10);
  assert.equal(root.querySelectorAll("li").length, 10);
  assert.equal(root.querySelectorAll("time").length, 10);
  assert.equal(root.querySelectorAll("li b").length, 0);
  assert.equal(root.querySelectorAll("li img[src]").length, 10);
  assert.equal(root.querySelector("dialog"), null);
  root.querySelector("li a").click(); await settle();
  assert.equal(root.querySelector(".inline-preview").hidden, false);
  assert.ok(root.querySelector("iframe").getAttribute("src").startsWith("blob:"));
  assert.equal(root.querySelector('a[aria-current="true"]'), root.querySelector("li a"));
  root.querySelector(".preview-close").click();
  assert.equal(root.querySelector(".inline-preview").hidden, true);
  assert.equal(root.activeElement, root.querySelector("li a"));
  assert.equal(card.getGridOptions().columns, "full");
});

test("page change clears selected preview and releases thumbnails", async () => {
  const {root, revoked, search} = await setup();
  await search("invoice");
  root.querySelector("li a").click(); await settle();
  root.querySelector(".next").click();
  for (let i = 0; i < 5; i++) await settle();
  assert.equal(root.querySelector(".inline-preview").hidden, true);
  assert.equal(root.querySelector("iframe").hasAttribute("src"), false);
  assert.equal(root.querySelectorAll("li").length, 1);
  assert.equal(root.querySelector(".range").textContent, "11–11 von 11");
  assert.ok(revoked.length >= 11);
});

test("thumbnails can be disabled, failures do not break results", async () => {
  let requests = 0;
  const a = await setup({show_thumbnails:false}, {callApiRaw: async () => { requests++; throw {}; }});
  await a.search("invoice");
  assert.equal(requests, 0);
  assert.equal(a.root.querySelectorAll("li img").length, 0);
  const b = await setup({}, {callApiRaw: async () => { throw {}; }});
  await b.search("invoice");
  assert.equal(b.root.querySelectorAll("li").length, 10);
  assert.equal(b.root.querySelectorAll("li img[hidden]").length, 10);
});

test("thumbnail concurrency is bounded and removed cards abort pending requests", async () => {
  let active = 0, max = 0;
  const signals = [];
  const {card, search} = await setup({}, {callApiRaw: async (_, path, a, b, signal) => {
    signals.push(signal); active++; max = Math.max(max, active);
    return new Promise((resolve, reject) => signal.addEventListener("abort", () => {active--; reject({});}, {once:true}));
  }});
  await search("invoice");
  assert.equal(max, 3);
  card.remove(); await settle();
  assert.ok(signals.every(signal => signal.aborted));
});

test("late document response cannot replace a newer selection", async () => {
  let resolve;
  const {root, search, window} = await setup({show_thumbnails:false}, {callApiRaw: (_, path) => path.includes("/1/") ? new Promise(done => {resolve=done;}) : Promise.resolve({ok:true, headers:new Map([["Content-Type","application/pdf"]]), blob:async () => new window.Blob(["new"])}) });
  await search("invoice");
  root.querySelectorAll("li a")[0].click();
  root.querySelectorAll("li a")[1].click(); await settle();
  const url = root.querySelector("iframe").getAttribute("src");
  resolve({ok:true, headers:new Map([["Content-Type","application/pdf"]]), blob:async () => new window.Blob(["old"])}); await settle();
  assert.equal(root.querySelector("iframe").getAttribute("src"), url);
  assert.match(root.querySelector(".preview-title").textContent, /Dokument 1/);
});

test("editor preserves extra configuration, validates and selects connections safely", async () => {
  const {window} = await setup();
  for (const type of ["search", "documents"]) {
    const Card = window.customElements.get(`paperless-ngx-insights-${type}`);
    const editor = Card.getConfigElement();
    const config = {type:`custom:paperless-ngx-insights-${type}`, title:"<img src=x>", entry_id:"missing", grid_options:{columns:12}, visibility:[{condition:"user",users:["fixture"]}]};
    editor.setConfig(config);
    let calls = 0;
    editor.hass = {callWS: async () => { calls++; return [{entry_id:"fixture",title:"<script>unsafe</script>"}];}};
    window.document.body.append(editor); await settle();
    const root = editor.shadowRoot;
    assert.equal(root.querySelector("script,img"), null);
    assert.equal(root.querySelector('[name="entry_id"]').value, "missing");
    const changes = [];
    editor.addEventListener("config-changed", event => {assert.ok(event.bubbles && event.composed); changes.push(event.detail.config);});
    const input = root.querySelector('[name="page_size"]');
    input.value = "0"; input.dispatchEvent(new window.Event("change"));
    assert.equal(changes.length, 0);
    assert.match(root.querySelector(".validation").textContent, /zwischen/);
    input.value = "7"; input.dispatchEvent(new window.Event("change"));
    assert.equal(changes[0].page_size, 7);
    assert.deepEqual(changes[0].grid_options, config.grid_options);
    assert.deepEqual(changes[0].visibility, config.visibility);
    const select = root.querySelector('[name="entry_id"]');
    select.value = "fixture"; select.dispatchEvent(new window.Event("change"));
    assert.equal(changes[1].entry_id, "fixture");
    editor.hass = {callWS:async () => {throw new Error("must not refetch on state update");}};
    assert.equal(calls, 1);
    editor.remove();
  }
});
