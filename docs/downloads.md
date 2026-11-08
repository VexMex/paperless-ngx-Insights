# Dateien, Darstellung und Downloads – 0.1.0-dev.7

Die PDF-Vorschau bleibt auf **20 MiB** begrenzt. Größere Dateien werden nicht im
Viewer gepuffert; die Karte erklärt die Grenze und bietet „PDF herunterladen“ an.
Ohne PDF-Vorschau bleibt „Original herunterladen“ verfügbar. Bildvorschauen der
ersten Seite sind weiterhin auf 2 MiB begrenzt.

## Übertragung und Anmeldung

PDF und Original werden als authentifizierte HA-Attachments gestreamt. Feste
Paperless-Pfade: PDF über `preview/`, Original über `download/?original=true`.
Keine beliebigen URLs oder Weiterleitungen. Höchstens 64-KiB-Blöcke, kein
vollständiges Dateiarray, keine temporäre Datei und kein großer Browser-Blob.
Zwei Downloads je Verbindung gleichzeitig; Timeout zehn Minuten, Lesepause
höchstens 30 Sekunden. Netzwerk und Verbindungen bleiben währenddessen belegt.

Originale werden als `application/octet-stream` und `attachment` mit `nosniff`,
`no-store` und CSP-Sandbox ausgeliefert. Auch HTML/SVG werden heruntergeladen und
nicht unter der HA-Origin angezeigt. Dateinamen werden von Pfaden, Steuerzeichen
und Header-Syntax bereinigt. PDF-Downloads prüfen MIME-Typ und PDF-Signatur.

Reload/Unload schließt laufende Upstream-Antworten. Während eines Transfers werden
die geladene Verbindung, die aktuelle Benutzerfreigabe und die vorhandene
HA-Anmeldung erneut geprüft.
Abbruch/Übertragungsfehler beendet die Verbindung. Kein automatisches Wiederholen
und keine Byte-Range-/Resume-Unterstützung in dieser Ausbaustufe.

Normale Download-Links senden keinen HA-Bearer-Header. Der Button fordert deshalb
per WebSocket einen **30 Sekunden gültigen** HA-Link für genau Dokument und
Downloadart an. Er ist an die aktuelle HA-Anmeldung gebunden und nutzt die
[HA-Pfadsignatur](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/http/auth.py).
Der Link ist ein kurzlebiger Zugriffsbeleg: Wer ihn während seiner Gültigkeit kennt,
kann denselben Transfer starten. Kein dauerhafter öffentlicher Freigabelink und
niemals der Paperless-Schlüssel. Ablauf, manipulierte Pfade/Parameter, entfernte
Anmeldung und fehlende Berechtigung für die Verbindung verhindern neue Abrufe. Bereits begonnene
Transfers dürfen nach Ablauf weiterlaufen, maximal bis zum Download-Timeout.
Signierte URLs werden von der Integration weder gespeichert noch protokolliert.

Browser-/Companion-Downloads verwenden die jeweilige normale Speicheroberfläche.
Android/iOS-Geräte stehen für eine praktische Abnahme noch nicht zur Verfügung.
Diese Abdeckung bleibt offen. Im eingebauten Browser bleibt die bekannte native
PDF-Einschränkung; die erste Bildseite ist weiterhin per Button verfügbar.

## Prüfungen

Clienttests streamen synthetische Dateien über 25 MiB, prüfen feste Pfade,
Original-Parameter, begrenzte Blöcke, Fehler und Validierung. HA-Tests prüfen
einen über 25 MiB großen Attachment-Stream, Authentifizierung, Signaturablauf,
manipulierten Pfad, Nicht-Adminzugriff und Dateinamen. Frontendtests prüfen die
Größenmeldung mit beiden Downloads, erlaubte HA-URLs und veraltete Antworten.
Tatsächliche CI-/Live-Ergebnisse stehen in todo.md.

Am 01.11.2026 vollständig grüne CI: 103 Client-Tests pro Python-Version,
37 HA-Frameworktests und 19 Frontendtests. auf der isolierten Testinstanz beide Downloadarten vollständig
gestreamt abgerufen, Attachment/no-store geprüft; ohne gültige Anmeldung/Signatur
jeweils abgewiesen. Vorschau, Thumbnail und Suche weiterhin erfolgreich.
Im Browser beide Buttons sichtbar und PDF-Klick mit Übergabestatus geprüft.
Die Browserautomation lieferte kein Download-Abschlussereignis; das tatsächliche
Speichern über diesen Browser wird nicht als bestanden behauptet. Sections-Layout
mit Suche, Vorschaubildern und ausgewähltem Dokument zusätzlich visuell geprüft.
Temporäre Testansicht entfernt; vorhandenes Dashboard vollständig erhalten.
