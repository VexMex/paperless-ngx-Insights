/* Paperless-ngx Insights: compact search card. No credentials in the browser. */
class PaperlessInsightsSearchCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._sequence = 0;
    this._page = 1;
    this._count = 0;
    this._documents = [];
    this._loading = false;
    this._searched = false;
  }

  setConfig(config) {
    const size = config.page_size ?? 5;
    if (!Number.isInteger(size) || size < 1 || size > 50) {
      throw new Error("Treffer pro Seite müssen zwischen 1 und 50 liegen.");
    }
    if (config.search_mode && !["title", "text"].includes(config.search_mode)) {
      throw new Error("Suchmodus muss title oder text sein.");
    }
    this._config = { ...config, page_size: size };
    this._sequence++;
    this._page = 1;
    this._count = 0;
    this._documents = [];
    this._searched = false;
    this._loading = false;
    this._entry = config.entry_id || null;
    this._connecting = false;
    this._build();
    this._connect();
  }

  set hass(value) {
    this._hass = value;
    this._connect();
  }

  connectedCallback() {
    this._controls();
    this._connect();
  }

  disconnectedCallback() {
    this._sequence++;
    this._loading = false;
    this._connecting = false;
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, rows: "auto", min_columns: 6 };
  }

  _build() {
    // Static markup only. Configured headings and document text use textContent.
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card { overflow:hidden; }
        .body { padding:20px; }
        h2 { margin:0 0 18px; font-size:20px; font-weight:500; }
        form { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; }
        label { display:block; font-size:13px; color:var(--secondary-text-color); }
        input,select,button { font:inherit; box-sizing:border-box; }
        input,select { width:100%; min-height:44px; border:1px solid var(--divider-color);
          border-radius:8px; padding:10px; background:var(--card-background-color);
          color:var(--primary-text-color); }
        input { margin-top:5px; }
        select { margin-top:10px; }
        button { cursor:pointer; border:0; border-radius:8px; min-height:44px; min-width:44px;
          background:var(--primary-color); color:var(--text-primary-color,#fff); padding:8px 14px; }
        button:disabled { opacity:.45; cursor:default; }
        button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible {
          outline:3px solid var(--primary-color); outline-offset:3px; }
        form button { align-self:end; }
        ul { padding:0; margin:16px 0 4px; list-style:none; }
        li+li { border-top:1px solid var(--divider-color); }
        a { display:flex; align-items:center; gap:10px; min-height:48px; padding:8px 0;
          color:var(--primary-text-color); text-decoration:none; overflow-wrap:anywhere; }
        a:hover { color:var(--primary-color); }
        .doc-icon { color:var(--primary-color); flex-shrink:0; }
        .title { flex:1; min-width:0; }
        .external { color:var(--secondary-text-color); font-size:16px; }
        .status { margin:14px 0 0; font-size:14px; color:var(--secondary-text-color); }
        .error { color:var(--error-color,#db4437); }
        .hint { font-size:12px; line-height:1.5; color:var(--secondary-text-color); margin:10px 0; }
        nav { display:flex; align-items:center; justify-content:space-between; gap:10px;
          padding-top:12px; margin-top:12px; border-top:1px solid var(--divider-color); }
        nav button { background:transparent; color:var(--primary-text-color); font-size:22px; }
        .range { font-size:14px; text-align:center; color:var(--secondary-text-color); }
        [hidden] { display:none !important; }
      </style>
      <ha-card><div class="body">
        <h2></h2>
        <form>
          <label>Dokument suchen<input type="search" maxlength="500" placeholder="Suchbegriff …" autocomplete="off"></label>
          <button type="submit">Suchen</button>
        </form>
        <select aria-label="Suchbereich"><option value="title">Nur Titel</option><option value="text">Titel und Inhalt</option></select>
        <p class="hint">Mehrere Wörter: alle Begriffe, beliebige Reihenfolge. Mit "Anführungszeichen" eine Wortfolge suchen.</p>
        <p class="status" role="status" aria-live="polite"></p>
        <ul aria-label="Gefundene Dokumente"></ul>
        <nav aria-label="Ergebnisseiten" hidden>
          <button class="previous" aria-label="Vorherige Seite">‹</button>
          <span class="range"></span>
          <button class="next" aria-label="Nächste Seite">›</button>
        </nav>
      </div></ha-card>`;
    const root = this.shadowRoot;
    root.querySelector("h2").textContent = this._config.title || "Paperless · Dokumente";
    this._input = root.querySelector("input");
    this._mode = root.querySelector("select");
    this._mode.value = this._config.search_mode || "title";
    this._status = root.querySelector(".status");
    this._list = root.querySelector("ul");
    this._nav = root.querySelector("nav");
    this._previous = root.querySelector(".previous");
    this._next = root.querySelector(".next");
    this._submit = root.querySelector('button[type="submit"]');
    root.querySelector("form").addEventListener("submit", event => {
      event.preventDefault();
      this._search(1, true);
    });
    this._mode.addEventListener("change", () => {
      if (this._searched || this._loading) this._search(1, true);
    });
    this._previous.addEventListener("click", () => this._search(this._page - 1));
    this._next.addEventListener("click", () => this._search(this._page + 1));
    this._message("Suchbegriff eingeben und Suchen drücken.");
    this._controls();
  }

  async _connect() {
    if (!this._hass || !this._config || !this.isConnected || this._entry || this._connecting) return;
    this._connecting = true;
    const sequence = this._sequence;
    try {
      const entries = await this._hass.callWS({ type: "paperless_ngx_insights/entries" });
      if (sequence !== this._sequence) return;
      if (entries.length === 1) {
        this._entry = entries[0].entry_id;
        this._message("Suchbegriff eingeben und Suchen drücken.");
      } else {
        this._message(entries.length ? "Bitte entry_id in der Karte festlegen." : "Paperless-Integration ist nicht eingerichtet.", true);
      }
    } catch (_) {
      if (sequence === this._sequence) this._message("Kein Zugriff. Bitte als HA-Administrator anmelden.", true);
    } finally {
      if (sequence === this._sequence) {
        this._connecting = false;
        this._controls();
      }
    }
  }

  async _search(page, fresh = false) {
    if (!this._hass || !this._entry || page < 1 || (!fresh && this._loading)) return;
    if (fresh) this._query = this._input.value.trim();
    const sequence = ++this._sequence;
    this._loading = true;
    this._message("Dokumente werden gesucht …");
    this._controls();
    try {
      const result = await this._hass.callWS({
        type: "paperless_ngx_insights/search", entry_id: this._entry,
        text: this._query || "", mode: this._mode.value,
        page, page_size: this._config.page_size,
      });
      if (sequence !== this._sequence || !this.isConnected) return;
      this._page = page;
      this._count = result.count;
      this._documents = result.documents;
      this._searched = true;
      this._list.replaceChildren();
      const base = new URL(result.web_url);
      if (!["http:", "https:"].includes(base.protocol)) throw new Error("Invalid URL");
      for (const document of result.documents) {
        if (!Number.isSafeInteger(document.id) || document.id < 1) continue;
        const row = window.document.createElement("li");
        const link = window.document.createElement("a");
        link.href = `${base.href.replace(/\/$/, "")}/documents/${document.id}/details`;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        const icon = window.document.createElement("span");
        icon.className = "doc-icon";
        icon.textContent = "▤";
        icon.setAttribute("aria-hidden", "true");
        const title = window.document.createElement("span");
        title.className = "title";
        title.textContent = document.title || "Dokument ohne Titel";
        const arrow = window.document.createElement("span");
        arrow.className = "external";
        arrow.textContent = "↗";
        arrow.setAttribute("aria-hidden", "true");
        link.setAttribute("aria-label", `${document.title || "Dokument"} in Paperless öffnen (neuer Tab)`);
        link.append(icon, title, arrow);
        row.append(link);
        this._list.append(row);
      }
      this._message(result.count ? "Dokument antippen, um es in Paperless zu öffnen." : "Keine Dokumente gefunden.");
    } catch (error) {
      if (sequence !== this._sequence) return;
      this._documents = [];
      this._count = 0;
      this._list.replaceChildren();
      const message = error.code === "invalid_auth"
        ? "Paperless-Schlüssel bitte in der Integration erneuern."
        : error.code === "invalid_search"
          ? "Anführungszeichen bitte schließen und höchstens 32 Suchbegriffe verwenden."
          : "Suche fehlgeschlagen. Verbindung und Berechtigung prüfen.";
      this._message(message, true);
    } finally {
      if (sequence === this._sequence) {
        this._loading = false;
        this._controls();
      }
    }
  }

  _message(text, error = false) {
    if (!this._status) return;
    this._status.textContent = text;
    this._status.classList.toggle("error", error);
  }

  _controls() {
    if (!this._submit) return;
    this._submit.disabled = !this._entry || this._loading;
    this._previous.disabled = this._loading || this._page <= 1;
    this._next.disabled = this._loading || this._page * this._config.page_size >= this._count;
    this._nav.hidden = !this._searched || !this._count;
    const start = this._count ? (this._page - 1) * this._config.page_size + 1 : 0;
    const end = Math.min(this._page * this._config.page_size, this._count);
    this.shadowRoot.querySelector(".range").textContent = `${start}–${end} von ${this._count}`;
    this._list.setAttribute("aria-busy", String(this._loading));
  }
}

if (!customElements.get("paperless-ngx-insights-search")) {
  customElements.define("paperless-ngx-insights-search", PaperlessInsightsSearchCard);
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "paperless-ngx-insights-search",
  name: "Paperless-ngx Insights · Suche",
  description: "Dokumente suchen, seitenweise anzeigen und in Paperless öffnen.",
  preview: false,
});
