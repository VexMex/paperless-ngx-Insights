# Große Dokumentkarte und visueller Editor – 0.1.0-dev.5

Die Ressource `paperless-ngx-insights.js?v=0.1.0-dev.5` registriert beide Karten
und den gemeinsamen visuellen Editor. Kein zusätzliches Kartenpaket erforderlich.

```yaml
type: custom:paperless-ngx-insights-documents
title: Paperless · Dokumentübersicht
search_mode: text
page_size: 10
height: 800
show_thumbnails: true
```

Bei mehreren Verbindungen `entry_id` wählen. Die große Karte verwendet stets die
eingebettete Vorschau; `open_mode` gehört zur kompakten Karte.

Für einen ganzen Tab eine HA-Panel-Ansicht mit genau dieser Karte verwenden:

```yaml
title: Dokumente
path: dokumente
type: panel
cards:
  - type: custom:paperless-ngx-insights-documents
    title: Paperless · Dokumentübersicht
    page_size: 10
    search_mode: text
    height: 800
    show_thumbnails: true
```

Alternativ in Sections mit `grid_options: {columns: full, rows: auto}`. Die
Kartenbreite, nicht die gesamte Fensterbreite, bestimmt die Aufteilung: bis 760px
wechselt die Karte zwischen Liste und Vorschau. Der Zurück-Button stellt den Fokus
auf den gewählten Treffer wieder her. Höhe 400–1400px (Standard 800), zusätzlich
durch verfügbare Bildschirmhöhe begrenzt. Separate Scrollbereiche für Treffer und
Dokument, ohne automatische Dokumentauswahl oder Suche beim Tippen.

Die gemeinsame Such-/Vorschaulogik entspricht der kompakten Karte. Jeder Such- und
Seitenwechsel entfernt die alte Auswahl. Bilder erscheinen nur für die aktuelle
Ergebnisseite und erst bei Sichtbarkeit (mit 120px Vorlauf), maximal drei parallel.
Ohne IntersectionObserver werden die aktuellen Ergebnisse begrenzt parallel geladen.
Ein fehlendes Bild lässt den Titel bedienbar. `show_thumbnails: false` deaktiviert
Bildanfragen vollständig. Keine globalen Dokumentzustände oder zusätzlichen Caches.

Alle Bilder/PDFs laden über die administrativ geschützten HA-Endpunkte; Tokens
stehen nicht im Frontend. Grenzen aus [PDF-Vorschau](pdf-preview.md) gelten weiter:
20 MiB pro PDF, 2 MiB pro Bild; native PDF-Anzeige abhängig vom Browser, Bild der
ersten Seite per Button. Download bezieht sich auf die geladene PDF-Vorschau,
nicht einen zusätzlichen Originaldatei-Endpunkt.

## Editor

In der HA-Kartenauswahl heißen die Karten „Paperless-ngx Insights · Suche“ und
„Paperless-ngx Insights · Dokumentübersicht“. Nach Auswahl erscheint der visuelle
Editor. Er lädt geladene Verbindungen über den bestehenden Admin-WebSocket-Befehl.
Eine derzeit nicht geladene Verbindung bleibt als Auswahl erhalten. Automatische
Auswahl funktioniert bei genau einer geladenen Verbindung.

Der Editor nutzt `getConfigElement`, `getStubConfig` und das vollständige,
aufsteigende `config-changed`-Ereignis nach dem offiziellen
[HA-Vertrag](https://contributors.home-assistant.io/frontend/custom-ui/card-editor/).
Zahlen werden vor Übernahme validiert. Layout-, Sichtbarkeits- und andere zusätzliche
Konfigurationsschlüssel bleiben erhalten. Kein API-Schlüsselfeld in Karten.

## Prüfungen und offene Abdeckung

17 lokale Frontendtests bestehen; davon sechs neue Szenarien für große Karte und
Editor: gemeinsame Suche/Datum/Bilder/Inline-Vorschau, Seitenwechsel und Freigabe,
deaktivierte/fehlerhafte Thumbnails, maximal drei Bildabrufe und Abbruch beim
Entfernen, verspätete Dokumentantwort sowie Editorvalidierung/Verbindungsauswahl/
Erhalt zusätzlicher Einstellungen. CI und Live-Sichtprüfung werden in todo.md
mit tatsächlich ausgeführten Ergebnissen ergänzt.

Weiter offen: Companion-/Safari-/Firefox-Matrix, Screenreader-Abnahme, große PDFs
mit Streaming und Originaldatei-Download. Diese Version ist kein fertiges Release.
