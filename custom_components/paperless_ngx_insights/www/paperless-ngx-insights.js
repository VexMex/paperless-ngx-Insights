/* Paperless-ngx Insights: compact search card. No credentials in the browser. */
class PaperlessInsightsSearchCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("paperless-ngx-insights-editor");
  }

  static getStubConfig() {
    return { title: "Dokumente suchen", page_size: 5, search_mode: "title", open_mode: "preview" };
  }
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
    if (config.open_mode && !["preview", "paperless"].includes(config.open_mode)) {
      throw new Error("open_mode muss preview oder paperless sein.");
    }
    this._closePreview(false);
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
    this._closePreview(false);
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
        dialog { box-sizing:border-box; width:min(1100px,96vw); max-width:96vw;
          height:90dvh; max-height:90dvh; border:1px solid var(--divider-color); border-radius:12px;
          padding:16px; color:var(--primary-text-color); background:var(--card-background-color,#fff); }
        dialog::backdrop { background:rgba(0,0,0,.55); }
        .preview-layout { height:100%; display:flex; flex-direction:column; gap:10px; }
        .preview-header { display:flex; gap:12px; align-items:center; }
        .preview-title { flex:1; font-size:18px; overflow-wrap:anywhere; margin:0; }
        .preview-actions { display:flex; gap:16px; flex-wrap:wrap; }
        .preview-actions a { min-height:32px; padding:0; color:var(--primary-color); }
        iframe { flex:1; min-height:120px; width:100%; border:0; background:#eee; }
        .thumbnail-wrap { flex:1; min-height:0; overflow:auto; text-align:center; }
        .thumbnail-wrap img { max-width:100%; height:auto; background:white; }
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
    this.shadowRoot.innerHTML += `
      <dialog aria-labelledby="preview-title"><div class="preview-layout">
        <div class="preview-header"><h3 id="preview-title" class="preview-title"></h3>
          <button class="preview-close" aria-label="Dokumentvorschau schließen">Schließen</button></div>
        <p class="preview-status" role="status" aria-live="polite"></p>
        <div class="preview-actions"><a class="paperless-link" target="_blank" rel="noopener noreferrer">In Paperless öffnen ↗</a>
          <button class="preview-download" hidden>PDF herunterladen</button>
          <button class="original-download" hidden>Original herunterladen</button></div>
        <button class="show-thumbnail">Erste Seite als Bild anzeigen</button>
        <div class="thumbnail-wrap" hidden><img alt="Vorschaubild der ersten Dokumentseite"></div>
        <iframe title="PDF-Dokumentvorschau" referrerpolicy="no-referrer" hidden></iframe>
      </div></dialog>`;
    const root = this.shadowRoot;
    this._dialog = root.querySelector("dialog");
    root.querySelector(".preview-close").addEventListener("click", () => this._closePreview());
    root.querySelector(".preview-download").addEventListener("click", () => this._download("pdf"));
    root.querySelector(".original-download").addEventListener("click", () => this._download("original"));
    root.querySelector(".show-thumbnail").addEventListener("click", () => this._showThumbnail());
    this._dialog.addEventListener("cancel", event => { event.preventDefault(); this._closePreview(); });
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
    this._closePreview();
    this._beforeSearch?.();
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
        if (this._config.open_mode === "preview") {
          arrow.textContent = "▣";
          link.setAttribute("aria-label", `${document.title || "Dokument"} als Vorschau öffnen`);
          link.addEventListener("click", event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            this._openPreview(document, link);
          });
        }
        link.append(icon, title, arrow);
        row.append(link);
        this._list.append(row);
        this._decorateResult?.(document, row, link);
      }
      this._afterResults?.();
      this._message(result.count ? (this._config.open_mode === "preview"
        ? "Dokument antippen, um die Vorschau zu öffnen."
        : "Dokument antippen, um es in Paperless zu öffnen.") : "Keine Dokumente gefunden.");
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

  _closePreview(restoreFocus = true) {
    this._previewSequence = (this._previewSequence || 0) + 1;
    this._previewAbort?.abort();
    this._thumbnailAbort?.abort();
    this._previewAbort = null;
    clearTimeout(this._previewTimeout);
    const frame = this._dialog?.querySelector("iframe");
    if (frame) { frame.removeAttribute("src"); frame.hidden = true; }
    const download = this._dialog?.querySelector(".preview-download");
    if (download) { download.removeAttribute("href"); download.hidden = true; }
    const original = this._dialog?.querySelector(".original-download");
    if (original) original.hidden = true;
    if (this._previewUrl) URL.revokeObjectURL(this._previewUrl);
    if (this._thumbnailUrl) URL.revokeObjectURL(this._thumbnailUrl);
    this._thumbnailUrl = null;
    const image = this._dialog?.querySelector("img");
    if (image) { image.removeAttribute("src"); image.parentElement.hidden = true; }
    this._previewUrl = null;
    if (this._dialog?.open) this._dialog.close();
    if (restoreFocus && this._previewOpener?.isConnected) this._previewOpener.focus();
    this._previewOpener = null;
  }

  async _openPreview(document, opener) {
    this._closePreview(false);
    this._previewOpener = opener;
    const sequence = this._previewSequence;
    this._previewDocument = document.id;
    const root = this._dialog;
    root.querySelector(".preview-title").textContent = document.title || "Dokument";
    root.querySelector(".paperless-link").href = opener.href;
    const status = root.querySelector(".preview-status");
    status.textContent = "PDF-Vorschau wird geladen …";
    root.querySelector(".preview-download").hidden = false;
    root.querySelector(".original-download").hidden = false;
    root.querySelectorAll(".preview-download,.original-download").forEach(button => { button.disabled = false; });
    this._presentPreview();
    const controller = new AbortController();
    this._previewAbort = controller;
    this._previewTimeout = setTimeout(() => controller.abort(), 65000);
    try {
      const response = await this._hass.callApiRaw("GET",
        `paperless_ngx_insights/${encodeURIComponent(this._entry)}/documents/${document.id}/preview`,
        undefined, undefined, controller.signal);
      if (!response.ok) throw { status: response.status };
      if (response.headers.get("Content-Type")?.split(";")[0] !== "application/pdf") throw {};
      const blob = await response.blob();
      if (sequence !== this._previewSequence || !this.isConnected) return;
      if (blob.size > 20 * 1024 * 1024) throw { status: 413 };
      this._previewUrl = URL.createObjectURL(blob);
      const frame = root.querySelector("iframe");
      frame.src = this._previewUrl;
      frame.hidden = false;
      const download = root.querySelector(".preview-download");
      download.hidden = false;
      status.textContent = "Falls die PDF-Anzeige hier leer bleibt: PDF herunterladen oder in Paperless öffnen.";
      if (navigator.pdfViewerEnabled === false) await this._showThumbnail();
    } catch (error) {
      if (sequence !== this._previewSequence) return;
      if (error.status === 415) root.querySelector(".preview-download").hidden = true;
      status.textContent = error.status === 413 ? "Diese PDF ist größer als 20 MiB und wird zum Schutz von Home Assistant nicht angezeigt. Bitte PDF herunterladen."
        : error.status === 415 ? "Für dieses Format ist keine PDF-Vorschau verfügbar. Bitte das Original herunterladen oder die erste Seite als Bild anzeigen."
          : error.status === 403 ? "Keine Berechtigung für diese Dokumentvorschau."
            : "Vorschau konnte nicht geladen werden. Verbindung und Anmeldung prüfen oder in Paperless öffnen.";
    } finally {
      if (sequence === this._previewSequence) {
        clearTimeout(this._previewTimeout);
        this._previewAbort = null;
      }
    }
  }

  async _showThumbnail() {
    const sequence = this._previewSequence;
    const root = this._dialog;
    const button = root.querySelector(".show-thumbnail");
    if (button.disabled) return;
    button.disabled = true;
    const controller = new AbortController();
    this._thumbnailAbort = controller;
    const timeout = setTimeout(() => controller.abort(), 30000);
    const status = root.querySelector(".preview-status");
    try {
      if (!this._thumbnailUrl) {
        const response = await this._hass.callApiRaw("GET",
          `paperless_ngx_insights/${encodeURIComponent(this._entry)}/documents/${this._previewDocument}/thumbnail`,
          undefined, undefined, controller.signal);
        if (!response.ok || !["image/png", "image/jpeg", "image/webp"].includes(response.headers.get("Content-Type")?.split(";")[0])) throw {};
        const blob = await response.blob();
        if (sequence !== this._previewSequence || !this.isConnected) return;
        if (blob.size > 2 * 1024 * 1024) throw {};
        this._thumbnailUrl = URL.createObjectURL(blob);
      }
      root.querySelector("iframe").hidden = true;
      const image = root.querySelector("img");
      image.src = this._thumbnailUrl;
      image.parentElement.hidden = false;
      status.textContent = "Vorschaubild der ersten Seite. Die vollständige PDF kann heruntergeladen oder in Paperless geöffnet werden.";
    } catch (_) {
      if (sequence === this._previewSequence) status.textContent = "Seitenvorschau nicht verfügbar. Bitte PDF herunterladen oder in Paperless öffnen.";
    } finally {
      clearTimeout(timeout);
      if (this._thumbnailAbort === controller) this._thumbnailAbort = null;
      button.disabled = false;
    }
  }

  _presentPreview() {
    this._dialog.showModal();
  }

  async _download(kind) {
    const sequence = this._previewSequence;
    const root = this._dialog;
    const button = root.querySelector(kind === "pdf" ? ".preview-download" : ".original-download");
    if (button.disabled || button.hidden) return;
    button.disabled = true;
    try {
      const result = await this._hass.callWS({ type:"paperless_ngx_insights/download", entry_id:this._entry, document_id:this._previewDocument, kind });
      if (sequence !== this._previewSequence || !this.isConnected) return;
      const url = new URL(result.url, window.location.origin);
      const path = `/api/paperless_ngx_insights/${encodeURIComponent(this._entry)}/documents/${this._previewDocument}/download/${kind}`;
      if (url.origin !== window.location.origin || url.pathname !== path || !url.searchParams.has("authSig")) throw {};
      const anchor = document.createElement("a");
      anchor.href = url.href;
      anchor.download = "";
      anchor.rel = "noreferrer";
      anchor.hidden = true;
      root.append(anchor);
      anchor.click();
      anchor.remove();
      root.querySelector(".preview-status").textContent = "Download an den Browser übergeben. Die Datei wird direkt übertragen und nicht als Vorschau geladen.";
    } catch (_) {
      if (sequence === this._previewSequence) root.querySelector(".preview-status").textContent = "Download konnte nicht gestartet werden. Anmeldung und Verbindung prüfen.";
    } finally {
      if (sequence === this._previewSequence) button.disabled = false;
    }
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

class PaperlessInsightsDocumentsCard extends PaperlessInsightsSearchCard {
  static getStubConfig() {
    return { title: "Paperless · Dokumentübersicht", page_size: 10, search_mode: "text", height: 800, show_thumbnails: true };
  }

  setConfig(config) {
    const height = config.height ?? 800;
    if (!Number.isInteger(height) || height < 400 || height > 1400) throw new Error("Höhe muss zwischen 400 und 1400 Pixel liegen.");
    if (config.show_thumbnails !== undefined && typeof config.show_thumbnails !== "boolean") throw new Error("show_thumbnails muss true oder false sein.");
    this._releaseThumbnails();
    super.setConfig({ ...config, height, page_size: config.page_size ?? 10, search_mode: config.search_mode ?? "text", open_mode: "preview" });
  }

  getCardSize() { return 12; }
  getGridOptions() { return { columns: "full", rows: "auto", min_columns: 12 }; }

  _build() {
    super._build();
    const root = this.shadowRoot;
    const body = root.querySelector(".body");
    body.classList.add("browser");
    body.style.setProperty("--paperless-height", `${this._config.height}px`);
    const workspace = document.createElement("div");
    workspace.className = "workspace";
    const results = document.createElement("section");
    results.className = "results";
    results.setAttribute("aria-label", "Dokumentensuche und Treffer");
    for (const node of [...body.children].filter(node => node.tagName !== "H2")) results.append(node);
    const pane = document.createElement("section");
    pane.className = "document-pane";
    pane.setAttribute("aria-label", "Ausgewähltes Dokument");
    const empty = document.createElement("p");
    empty.className = "preview-empty";
    empty.textContent = "Dokument aus der Trefferliste auswählen, um die Vorschau zu öffnen.";
    const oldDialog = this._dialog;
    const inline = document.createElement("div");
    inline.className = "inline-preview";
    inline.hidden = true;
    inline.append(oldDialog.querySelector(".preview-layout"));
    oldDialog.remove();
    this._dialog = inline;
    this._emptyPreview = empty;
    const close = inline.querySelector(".preview-close");
    close.textContent = "← Zur Trefferliste";
    close.setAttribute("aria-label", "Zur Trefferliste zurückkehren");
    pane.append(empty, inline);
    workspace.append(results, pane);
    body.append(workspace);
    const style = document.createElement("style");
    style.textContent = `
      :host { container-type:inline-size; }
      .workspace { display:grid; grid-template-columns:minmax(270px,.8fr) minmax(0,1.6fr);
        height:min(var(--paperless-height),calc(100dvh - 180px)); min-height:400px; gap:20px; }
      .results { overflow:auto; padding:3px 10px 3px 3px; min-width:0; }
      .document-pane { border-left:1px solid var(--divider-color); padding:4px 0 4px 20px; min-width:0; min-height:0; }
      .preview-empty { color:var(--secondary-text-color); padding:24px; text-align:center; }
      .inline-preview { height:100%; }
      .preview-status { font-size:13px; margin:0; }
      .preview-close { background:transparent; color:var(--primary-color); }
      .preview-header { flex-wrap:wrap; }
      .preview-title { min-width:180px; }
      .show-thumbnail { background:transparent; color:var(--primary-color); border:1px solid var(--divider-color); }
      .result-image { width:56px; height:76px; object-fit:contain; flex-shrink:0; background:var(--secondary-background-color); }
      li a { border-radius:8px; padding:10px 6px; }
      li a[aria-current="true"] { background:var(--secondary-background-color); outline:2px solid var(--primary-color); outline-offset:-2px; }
      time { display:block; font-size:12px; color:var(--secondary-text-color); margin-top:6px; }
      @container (max-width:760px) {
        .workspace { grid-template-columns:minmax(0,1fr); }
        .browser:not(.selected) .document-pane { display:none; }
        .browser.selected .results { display:none; }
        .document-pane { border-left:0; padding:0; }
      }
    `;
    root.append(style);
    this._pendingThumbs = [];
  }

  _presentPreview() {
    this._dialog.hidden = false;
    this._emptyPreview.hidden = true;
    this.shadowRoot.querySelector(".browser").classList.add("selected");
    this._dialog.querySelector(".preview-close").focus();
  }

  _closePreview(restoreFocus = true) {
    const opener = this._previewOpener;
    super._closePreview(false);
    if (this._dialog && this._emptyPreview) {
      this._dialog.hidden = true;
      this._emptyPreview.hidden = false;
      this.shadowRoot.querySelector(".browser")?.classList.remove("selected");
      this._list?.querySelectorAll("a[aria-current]").forEach(link => link.removeAttribute("aria-current"));
    }
    if (restoreFocus && opener?.isConnected) opener.focus();
  }

  async _openPreview(item, opener) {
    const promise = super._openPreview(item, opener);
    opener.setAttribute("aria-current", "true");
    await promise;
  }

  _beforeSearch() { this._releaseThumbnails(); this._list.replaceChildren(); }

  _decorateResult(item, row, link) {
    const date = new Date(item.created);
    if (item.created && !Number.isNaN(date.getTime())) {
      const time = document.createElement("time");
      time.dateTime = item.created;
      time.textContent = date.toLocaleDateString(this._hass?.locale?.language || "de");
      link.querySelector(".title").append(time);
    }
    if (this._config.show_thumbnails === false) return;
    const image = document.createElement("img");
    image.className = "result-image";
    image.alt = "";
    image.width = 56;
    image.height = 76;
    image.addEventListener("error", () => { image.hidden = true; });
    link.querySelector(".doc-icon").replaceWith(image);
    this._pendingThumbs.push({ item, image });
  }

  _releaseThumbnails() {
    this._thumbGeneration = (this._thumbGeneration || 0) + 1;
    this._thumbObserver?.disconnect();
    this._thumbRequests?.forEach(controller => controller.abort());
    this._thumbRequests = new Set();
    this._thumbUrls?.forEach(url => URL.revokeObjectURL(url));
    this._thumbUrls = new Set();
    this._pendingThumbs = [];
  }

  _afterResults() {
    const generation = this._thumbGeneration;
    const queue = [];
    let active = 0;
    const run = () => {
      if (generation !== this._thumbGeneration) return;
      while (active < 3 && queue.length) {
        const job = queue.shift();
        active++;
        this._loadResultThumbnail(job, generation).finally(() => { active--; run(); });
      }
    };
    const jobs = this._pendingThumbs;
    if (typeof IntersectionObserver === "function") {
      const byImage = new Map(jobs.map(job => [job.image, job]));
      this._thumbObserver = new IntersectionObserver(entries => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          this._thumbObserver?.unobserve(entry.target);
          const job = byImage.get(entry.target);
          if (job) { queue.push(job); byImage.delete(entry.target); }
        }
        run();
      }, { root: this.shadowRoot.querySelector(".results"), rootMargin: "120px" });
      jobs.forEach(job => this._thumbObserver.observe(job.image));
    } else {
      queue.push(...jobs);
      run();
    }
  }

  async _loadResultThumbnail({ item, image }, generation) {
    const controller = new AbortController();
    this._thumbRequests.add(controller);
    const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await this._hass.callApiRaw("GET",
        `paperless_ngx_insights/${encodeURIComponent(this._entry)}/documents/${item.id}/thumbnail`,
        undefined, undefined, controller.signal);
      if (!response.ok || !["image/png", "image/jpeg", "image/webp"].includes(response.headers.get("Content-Type")?.split(";")[0])) throw {};
      const blob = await response.blob();
      if (generation !== this._thumbGeneration || !this.isConnected) return;
      if (blob.size > 2 * 1024 * 1024) throw {};
      const url = URL.createObjectURL(blob);
      this._thumbUrls.add(url);
      image.src = url;
    } catch (_) {
      if (generation === this._thumbGeneration) { image.hidden = true; image.parentElement?.setAttribute("data-thumbnail-unavailable", "true"); }
    } finally {
      clearTimeout(timeout);
      this._thumbRequests.delete(controller);
    }
  }

  connectedCallback() {
    super.connectedCallback();
    if (this._documents.length) {
      this._releaseThumbnails();
      this._list.querySelectorAll("li").forEach((row, index) => {
        const image = row.querySelector(".result-image");
        if (image) { image.hidden = false; this._pendingThumbs.push({ item: this._documents[index], image }); }
      });
      this._afterResults();
    }
  }

  disconnectedCallback() { this._releaseThumbnails(); super.disconnectedCallback(); }
}

class PaperlessInsightsEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }

  setConfig(config) {
    this._config = { ...config };
    this._large = config.type === "custom:paperless-ngx-insights-documents";
    this._build();
    this._fillEntries();
    this._loadEntries();
  }

  set hass(value) { this._hass = value; this._loadEntries(); }
  connectedCallback() { this._loadEntries(); }
  disconnectedCallback() { this._entriesRequest = null; }

  _build() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; } .fields { display:grid; gap:16px; padding:8px 0; }
        label { display:grid; gap:6px; color:var(--primary-text-color); font-size:14px; }
        input,select { font:inherit; width:100%; box-sizing:border-box; padding:12px; min-height:44px;
          border:1px solid var(--divider-color); border-radius:8px; color:var(--primary-text-color);
          background:var(--card-background-color); }
        input[type=checkbox] { width:24px; min-height:24px; margin:0; }
        .check { display:flex; align-items:center; gap:12px; }
        p { color:var(--secondary-text-color); font-size:13px; margin:0; line-height:1.5; }
        .error { color:var(--error-color,#db4437); }
        [hidden] { display:none !important; }
      </style>
      <div class="fields">
        <label>Überschrift<input name="title" type="text" maxlength="200"></label>
        <label>Paperless-Verbindung<select name="entry_id"></select></label>
        <p class="entries-status" role="status"></p>
        <label>Suchbereich<select name="search_mode"><option value="title">Nur Titel</option><option value="text">Titel und Inhalt</option></select></label>
        <label>Treffer pro Seite<input name="page_size" type="number" min="1" max="50" step="1"></label>
        <label class="compact-option">Dokument öffnen<select name="open_mode"><option value="paperless">Paperless im neuen Tab</option><option value="preview">Vorschau in Home Assistant</option></select></label>
        <label class="large-option">Höhe des Dokumentbereichs (Pixel)<input name="height" type="number" min="400" max="1400" step="1"></label>
        <label class="large-option check"><input name="show_thumbnails" type="checkbox">Vorschaubilder in der Trefferliste</label>
        <p class="validation error" role="alert"></p>
        <p>Der API-Schlüssel wird ausschließlich in der Integration verwaltet. PDF-Vorschauen bis 20 MiB; Anzeige abhängig vom Browser.</p>
      </div>`;
    const defaults = this._large ? PaperlessInsightsDocumentsCard.getStubConfig() : PaperlessInsightsSearchCard.getStubConfig();
    for (const control of this.shadowRoot.querySelectorAll("input,select")) {
      const value = this._config[control.name] ?? defaults[control.name];
      if (control.type === "checkbox") control.checked = value !== false;
      else control.value = value ?? "";
      control.addEventListener("change", () => this._changed(control));
    }
    this.shadowRoot.querySelectorAll(".large-option").forEach(node => { node.hidden = !this._large; });
    this.shadowRoot.querySelector(".compact-option").hidden = this._large;
  }

  _changed(control) {
    const config = { ...this._config };
    let value = control.type === "checkbox" ? control.checked : control.value;
    const error = this.shadowRoot.querySelector(".validation");
    if (control.type === "number") {
      value = Number(value);
      if (!Number.isInteger(value) || value < Number(control.min) || value > Number(control.max)) {
        error.textContent = `Bitte eine ganze Zahl zwischen ${control.min} und ${control.max} eingeben.`;
        return;
      }
    }
    error.textContent = "";
    if (value === "") delete config[control.name];
    else config[control.name] = value;
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: { ...config } }, bubbles: true, composed: true }));
  }

  _fillEntries() {
    const select = this.shadowRoot.querySelector('[name="entry_id"]');
    if (!select) return;
    select.replaceChildren();
    const option = (value, title) => { const node = document.createElement("option"); node.value = value; node.textContent = title; select.append(node); };
    option("", "Automatisch (bei genau einer Verbindung)");
    for (const entry of this._entries || []) option(entry.entry_id, entry.title);
    if (this._config.entry_id && !this._entries?.some(entry => entry.entry_id === this._config.entry_id)) option(this._config.entry_id, `${this._config.entry_id} (derzeit nicht geladen)`);
    select.value = this._config.entry_id || "";
  }

  async _loadEntries() {
    if (!this._hass || !this._config || this._entries || this._entriesRequest) return;
    const request = {};
    this._entriesRequest = request;
    try {
      const entries = await this._hass.callWS({ type: "paperless_ngx_insights/entries" });
      if (this._entriesRequest !== request) return;
      this._entries = entries;
      this._fillEntries();
      this.shadowRoot.querySelector(".entries-status").textContent = entries.length ? "" : "Keine geladene Paperless-Verbindung gefunden. Bitte zuerst die Integration einrichten.";
    } catch (_) {
      if (this._entriesRequest === request) this.shadowRoot.querySelector(".entries-status").textContent = "Verbindungen konnten nicht geladen werden. HA-Administratorrechte und Integration prüfen.";
    } finally {
      if (this._entriesRequest === request) this._entriesRequest = null;
    }
  }
}

if (!customElements.get("paperless-ngx-insights-editor")) customElements.define("paperless-ngx-insights-editor", PaperlessInsightsEditor);
if (!customElements.get("paperless-ngx-insights-documents")) customElements.define("paperless-ngx-insights-documents", PaperlessInsightsDocumentsCard);
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
window.customCards.push({
  type: "paperless-ngx-insights-documents",
  name: "Paperless-ngx Insights · Dokumentübersicht",
  description: "Dokumente mit Vorschaubildern suchen und direkt im Dashboard ansehen.",
  preview: false,
});
