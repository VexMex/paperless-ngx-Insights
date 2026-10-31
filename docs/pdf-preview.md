# PDF-Vorschau – 0.1.0-dev.4

Die kompakte Karte unterstützt `open_mode: preview`. Die bisherige Voreinstellung
`paperless` bleibt erhalten. Ein Titel öffnet einen modalen Dialog mit PDF-Anzeige,
Download der geladenen PDF und einem Link zur Paperless-Oberfläche.

## Abruf und Rechte

- Die Karte nutzt HA `callApiRaw` mit dem regulären Bearer-Header.
- `GET /api/paperless_ngx_insights/{entry_id}/documents/{id}/preview` verlangt
  HA-Authentifizierung sowie einen aktiven Administrator. Dashboard-Sichtbarkeit
  ist keine Berechtigung. Auch direkte IDs werden geprüft.
- Das Backend ruft ausschließlich `/api/documents/{id}/preview/` unter der
  konfigurierten Paperless-Basis ab. Keine beliebigen URLs, keine Weiterleitungen,
  keine öffentlichen/signierten Dokumentlinks, keine Tokens in URLs.
- Ein gemeinsamer Paperless-Schlüssel bedeutet gemeinsame Paperless-Rechte.
  Paperless prüft seine Dokumentrechte bei jedem Abruf; 403 wird weitergegeben.
- Nach Abruf werden Benutzerrechte und geladene Integration erneut geprüft.
- Nur `application/pdf` mit `%PDF-`-Signatur wird ausgeliefert; HTML/andere Formate
  werden abgewiesen. Upstream-Dateiname und Antworttext werden nicht übernommen.
- Antworten verwenden `no-store, private`, `nosniff`, einen festen PDF-Dateinamen
  und `no-referrer`. Es gibt keinen Dokumentcache auf dem Server.

## Ressourcen und Grenzen

Der begrenzte vollständige Abruf wurde für den ersten Prototyp gegenüber Streaming
gewählt: maximal 20 MiB pro PDF, vier gleichzeitige Upstream-Anfragen je Eintrag,
60 Sekunden Upstream-Timeout, 65 Sekunden im Frontend. Die Größenbegrenzung gilt
auch beim Lesen ohne Content-Length. Gleichzeitige Abrufe und temporäre Kopien
benötigen entsprechend mehr Arbeitsspeicher. Byte-Range/Streaming und größere
Dateien bleiben offen; keine unbegrenzten großen PDFs laden.

Die Karte erzeugt eine lokale Blob-URL für den nativen Browser-PDF-Viewer.
Schließen, Suchwechsel, neue Konfiguration und Entfernen der Karte brechen den
Frontend-Abruf ab und geben die Blob-URL frei. Ein bereits laufender HA-Upstream-
Abruf kann noch bis zum Timeout weiterlaufen. Verspätete Antworten werden verworfen.
Ein bereits ausgeliefertes Dokument lässt sich durch späteren Rechteentzug nicht
aus dem Browser zurückrufen. Native PDF-Viewer können eine temporäre Kopie halten.

Kein PDF.js wird mitgeliefert. Seitenwahl und Zoom hängen vom nativen Viewer ab.
Meldet der Browser `navigator.pdfViewerEnabled === false`, wird automatisch eine
Bildvorschau der ersten Seite geladen. Der Button „Erste Seite als Bild anzeigen“
ermöglicht dies auch manuell. Der Thumbnail-Endpunkt verlangt dieselben HA-Rechte,
akzeptiert nur PNG/JPEG/WebP mit passender Signatur und begrenzt Dateien auf 2 MiB.
SVG und HTML werden abgewiesen; die Bilder laden ebenfalls über HA und Blob-URLs.
Paperless akzeptiert beim binären Abruf `Accept: */*`; ein alleiniger PDF-Accept-
Header wurde im Live-Test abgewiesen. Die Antwort wird unabhängig davon strikt geprüft.
Die Bildvorschau ist keine mehrseitige PDF-Anzeige und kann niedrig aufgelöst sein.
Ein leeres Viewer-Fenster ist nicht zuverlässig erkennbar; Download und externer
Link bleiben daher immer angeboten. Firefox, Safari und Companion-WebViews sind
noch nicht praktisch freigegeben. Nicht-PDF, fehlende Vorschau und Größenlimit
zeigen eine verständliche Meldung mit Paperless-Fallback.

## Nachweise

Grundlagen: [HA HTTP-View 2026.10.4](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/helpers/http.py),
[HA Frontend API](https://github.com/home-assistant/frontend/blob/dev/src/types.ts),
[authentifizierter Raw-Abruf](https://github.com/home-assistant/frontend/blob/dev/src/util/hass-call-api.ts).

Lokale synthetische HTTP-Tests prüfen IDs, festen Pfad und Auth-Header, PDF-Typ und
Signatur, Größenlimit, Fehlerstatus und Unload. Frontendtests prüfen Dialog, Abruf,
Download, Fokus, Abbruch, verspätete Antworten und Fallback. HA-Frameworktests
prüfen den registrierten HTTP-Pfad mit echter Auth-Middleware und Adminrechten.
Aktuelle CI-/Live-Ergebnisse und noch offene Browserprüfung stehen in todo.md.

Am 31.10.2026: GitHub Actions vollständig grün (90 Client-Tests pro Python-Version,
23 HA-Frameworktests, 11 Frontendtests). Auf ha-test wurden PDF/Thumbnail mit
Anmeldung, Ablehnung ohne Anmeldung, ungültige IDs und no-store geprüft. Die
vorherige Suche bleibt live funktionsfähig. Die Bildvorschau wurde bei schmaler
Ansicht und 1366×900 sichtbar geprüft; Schließen stellt den Fokus wieder her.
Der native Viewer bleibt im eingebauten Browser leer, obwohl dieser keinen
fehlenden PDF-Viewer meldet: der manuelle Bild-Button ist hier erforderlich.
Eine erfolgreiche vollständige mehrseitige PDF-Anzeige wird daher noch nicht als
browserübergreifend geprüft ausgewiesen. Download-Link und PDF-Abruf funktionieren;
der tatsächliche Download-Klick wurde nicht separat live ausgeführt.
