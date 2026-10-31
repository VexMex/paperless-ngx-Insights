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
  assert.equal(root.querySelectorAll("img,script").length, 0);
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
