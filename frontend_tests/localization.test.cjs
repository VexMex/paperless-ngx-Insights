const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const { test } = require("node:test");
const source = readFileSync("custom_components/paperless_ngx_insights/www/paperless-ngx-insights.js", "utf8");
const settle = () => new Promise(resolve => setImmediate(resolve));

async function setup(type = "search", language = "en", config = {}, api = {}) {
  const { Window } = await import("happy-dom");
  const window = new Window({ url: "http://ha-test.local/" });
  window.document.documentElement.lang = "de";
  window.eval(source);
  window.URL.createObjectURL = () => "blob:http://ha-test.local/preview";
  const revoked = [];
  window.URL.revokeObjectURL = url => revoked.push(url);
  const calls = [];
  const hass = {
    language,
    callWS: async message => {
      calls.push(message);
      return message.type.endsWith("/entries") ? [] : { count: 6, web_url: "http://paperless.test", documents: [{ id: 1, title: "", created: "2026-05-01" }] };
    },
    callApiRaw: async () => ({ ok: true, headers: new Map([["Content-Type", "application/pdf"]]), blob: async () => new window.Blob(["%PDF-"]) }),
    ...api,
  };
  const card = window.document.createElement(`paperless-ngx-insights-${type}`);
  card.setConfig({ entry_id: "fixture", page_size: 5, show_thumbnails: false, open_mode: "preview", ...config });
  card.hass = hass;
  window.document.body.append(card);
  const root = card.shadowRoot;
  const search = async () => {
    root.querySelector("form").dispatchEvent(new window.Event("submit", { cancelable: true }));
    await settle();
  };
  return { window, card, root, hass, calls, revoked, search };
}

test("cards follow HA language, regional German, locale fallback and English fallback", async () => {
  for (const [language, expected] of [["en-US", "Search"], ["de-AT", "Suchen"], ["fr", "Search"]]) {
    for (const type of ["search", "documents"]) {
      const { card, root, hass } = await setup(type, language);
      assert.equal(root.querySelector('[type="submit"]').textContent, expected);
      assert.equal(root.querySelector('option[value="title"]').textContent, expected === "Suchen" ? "Nur Titel" : "Title only");
      assert.equal(root.querySelector("select").getAttribute("aria-label"), expected === "Suchen" ? "Suchbereich" : "Search scope");
      assert.equal(root.querySelector(".next").getAttribute("aria-label"), expected === "Suchen" ? "Nächste Seite" : "Next page");
      assert.equal(root.querySelector(".preview-download").textContent, expected === "Suchen" ? "PDF herunterladen" : "Download PDF");
      assert.equal(root.querySelector("iframe").title, expected === "Suchen" ? "PDF-Dokumentvorschau" : "PDF document preview");
      card.hass = { ...hass, language: undefined, locale: { language: "de-DE" } };
      assert.equal(root.querySelector('[type="submit"]').textContent, "Suchen");
      card.remove();
    }
  }
});

test("language changes preserve query, focus, page, results and open preview without requests", async () => {
  for (const type of ["search", "documents"]) {
    const { card, root, hass, calls, revoked, search } = await setup(type, "de");
    const input = root.querySelector("input");
    input.value = "telekom rechnung";
    await search();
    root.querySelector(".next").click(); await settle();
    const link = root.querySelector("li a");
    link.click(); await settle();
    const url = root.querySelector("iframe").src;
    input.focus();
    const count = calls.length;
    card.hass = { ...hass, language: "en" };
    assert.equal(root.querySelector("input"), input);
    assert.equal(input.value, "telekom rechnung");
    assert.equal(root.activeElement, input);
    assert.equal(root.querySelector("li a"), link);
    assert.equal(link.querySelector(".document-name").textContent, "Untitled document");
    assert.equal(link.getAttribute("aria-label"), "Open preview of Document");
    assert.equal(root.querySelector(".range").textContent, "6–6 of 6");
    assert.equal(root.querySelector("iframe").src, url);
    assert.match(root.querySelector(".preview-status").textContent, /PDF viewer stays blank/);
    assert.equal(calls.length, count);
    assert.equal(revoked.length, 0);
    if (type === "documents") assert.equal(root.querySelector(".preview-close").textContent, "← Back to results");
    else assert.equal(root.querySelector("dialog").open, true);
    card.remove();
  }
});

test("a pending search resolves in the new language and custom text is preserved safely", async () => {
  let resolve;
  const { card, root, hass, search } = await setup("search", "de", { title: "Meine <Dokumente>" }, { callWS: () => new Promise(done => { resolve = done; }) });
  await search();
  card.hass = { ...hass, language: "en" };
  assert.equal(root.querySelector(".status").textContent, "Searching documents …");
  resolve({ count: 1, web_url: "http://paperless.test", documents: [{ id: 1, title: "Rechnung <img src=x>" }] });
  await settle();
  assert.equal(root.querySelector("h2").textContent, "Meine <Dokumente>");
  assert.equal(root.querySelector(".document-name").textContent, "Rechnung <img src=x>");
  assert.equal(root.querySelector("li img"), null);
  assert.equal(root.querySelector(".status").textContent, "Select a document to open its preview.");
  card.remove();
});

test("search errors and oversized PDF messages translate when language changes", async () => {
  const { card, root, hass, search } = await setup("search", "en", {}, { callWS: async () => { throw { code: "invalid_search" }; } });
  await search();
  assert.match(root.querySelector(".status").textContent, /quotation marks/);
  card.hass = { ...hass, language: "de" };
  assert.match(root.querySelector(".status").textContent, /Anführungszeichen/);
  const good = { ...hass, language: "en", callWS: async () => ({ count: 1, web_url: "http://paperless.test", documents: [{ id: 1 }] }), callApiRaw: async () => ({ ok: false, status: 413 }) };
  card.hass = good; await search();
  root.querySelector("li a").click(); await settle();
  assert.match(root.querySelector(".preview-status").textContent, /exceeds 20 MiB/);
  card.hass = { ...good, language: "de" };
  assert.match(root.querySelector(".preview-status").textContent, /größer als 20 MiB/);
  card.remove();
});

test("editor translates labels, validation and entry status without discarding edits", async () => {
  const { window, hass, calls } = await setup();
  for (const type of ["search", "documents"]) {
    const editor = window.customElements.get(`paperless-ngx-insights-${type}`).getConfigElement();
    editor.setConfig({ type: `custom:paperless-ngx-insights-${type}`, entry_id: "missing" });
    editor.hass = hass;
    window.document.body.append(editor); await settle();
    const root = editor.shadowRoot;
    assert.equal(root.querySelector('[data-i18n="heading"]').textContent, "Heading");
    assert.equal(root.querySelector('option[value="text"]').textContent, "Title and content");
    assert.match(root.querySelector(".entries-status").textContent, /No loaded Paperless/);
    const title = root.querySelector('[name="title"]');
    title.value = "Uncommitted custom heading"; title.focus();
    const number = root.querySelector('[name="page_size"]');
    number.value = "99"; number.dispatchEvent(new window.Event("change"));
    assert.match(root.querySelector(".validation").textContent, /whole number between 1 and 50/);
    const count = calls.length;
    editor.hass = { ...hass, language: "de" };
    assert.equal(root.querySelector('[name="title"]'), title);
    assert.equal(title.value, "Uncommitted custom heading");
    assert.equal(root.activeElement, title);
    assert.match(root.querySelector(".validation").textContent, /ganze Zahl zwischen 1 und 50/);
    assert.match(root.querySelector(".entries-status").textContent, /Keine geladene Paperless/);
    assert.equal(root.querySelector('[name="entry_id"]').value, "missing");
    assert.equal(calls.length, count);
    editor.remove();
  }
});

test("picker names follow page language and new cards do not store translated headings", async () => {
  const { window, card } = await setup();
  window.document.documentElement.lang = "en";
  assert.equal(window.customCards[0].name, "Paperless-ngx Insights · Search");
  assert.match(window.customCards[1].description, /thumbnails/);
  window.document.documentElement.lang = "de";
  assert.equal(window.customCards[0].name, "Paperless-ngx Insights · Suche");
  for (const type of ["search", "documents"]) assert.equal(window.customElements.get(`paperless-ngx-insights-${type}`).getStubConfig().title, undefined);
  card.remove();
});
