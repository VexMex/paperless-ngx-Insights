# Entwicklungsplan: paperless-ngx-Insights

Stand: 01.11.2026
Repository: https://github.com/VexMex/paperless-ngx-Insights
Ziel: Home-Assistant-Integration für die Suche und Anzeige von Paperless-ngx-Dokumenten.

## Prioritäten nach Nutzerentscheidung

Benutzerfreigaben und persönliche Paperless-API-Schlüssel werden ausdrücklich ganz
ans Ende der Agenda verschoben und nur bei tatsächlichem Bedarf umgesetzt.
Der Eigentümer nutzt das System normalerweise allein. Die bestehende serverseitige
Beschränkung auf HA-Administratoren sowie die Prüfung der Paperless-Dokumentrechte
bleiben erhalten; diese Sicherheitsprüfungen werden nicht zurückgestellt.

Einrichtung/Schlüsselwechsel, Updates und Downloads sind live abgesichert.
HACS-Auslieferung einschließlich Installations-/Updateprüfung ist abgeschlossen. Erweiterte
Mehrbenutzerfunktionen sind kein Abschluss- oder Release-Kriterium für diese Version.

## Aktueller Entwicklungsstand – HACS und Icon 1.0.1 / 1.0.2

- [x] Freigegebenes eigenes Icon als lokale HA-Marke in 256 und 512 Pixeln eingebunden.
- [x] `hacs.json` ergänzt; Manifest auf 1.0.1 angehoben und Changelog angelegt. Bestehendes Release V1.0 bleibt unverändert.
- [x] README auf HACS-Installation und Updates umgestellt; manuelle Alternative bleibt dokumentiert.
- [x] Lokal 103 Client-Tests, 19 Frontendtests, Ruff und Formatprüfung erfolgreich.
- [x] [GitHub Actions](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41292719992) erfolgreich: HACS-Validierung, 103 Client-Tests je Python-Version, 37 HA-Frameworktests, 19 Frontendtests; [Release v1.0.1](https://github.com/VexMex/paperless-ngx-Insights/releases/tag/v1.0.1) veröffentlicht.
- [x] Benutzerdefiniertes Repository auf ha-test hinzugefügt und v1.0.1 tatsächlich über HACS installiert. Alle 15 Laufzeitdateien zurückgelesen: Textinhalt mit normalisierten Zeilenenden, PNG-Icons bytegenau identisch. Keine manuelle Dateiübertragung für diese Installation.
- [x] Nach Neustart Suche mit mehreren Wörtern, Pagination, geschützte PDF-/Thumbnail-Vorschau und vollständig gestreamte PDF-/Original-Downloads geprüft. Schlüsselwechsel/Reload erfolgreich; genau eine Ressource auf 1.0.1. Dashboard-Konfiguration unverändert (Hash 696d5f569f29e4af). Eigenes Icon und Version in Geräte & Dienste sichtbar.
- [x] Sichtprüfung fand kaputten relativen README-Bildpfad innerhalb von HACS; vollständige Bildadresse für 1.0.2 eingesetzt.
- [x] [CI für 1.0.2](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41293055466) vollständig grün; [v1.0.2 veröffentlicht](https://github.com/VexMex/paperless-ngx-Insights/releases/tag/v1.0.2). HACS erkannte das Update von v1.0.1 und installierte v1.0.2. Nach Neustart zeigt Geräte & Dienste das eigene Icon und Version 1.0.2; Ressource automatisch auf 1.0.2 aktualisiert, Dashboard-Hash unverändert. Suche, Vorschau, Downloads und Schlüssel-/Reload-Prüfungen erneut erfolgreich. File editor gestoppt, Start bleibt manuell.
- [x] Korrigiertes README-Bild innerhalb von HACS abschließend visuell geprüft: eigenes Icon geladen, Version v1.0.2 als heruntergeladen angezeigt, HACS-Installationsanleitung lesbar.
- Hinweis: Geprüft wurde die Übernahme der vorhandenen manuellen Testinstallation in HACS, keine frisch aufgesetzte HA-Instanz. Companion-/Browsermatrix bleibt separat offen.

## Vorheriger Entwicklungsstand – Dateien und Downloads 0.1.0-dev.7

- [x] Öffentliche README vereinfacht: Zweck, Funktionen, manuelle Installation und Karten-Einrichtung; lokale Adressen sowie Entwicklungs- und Testdetails aus der README entfernt.

- [x] Vorschaugrenze bleibt bei 20 MiB; größere PDFs erhalten eine ausdrückliche Größenmeldung mit PDF-Download.
- [x] PDF- und Originaldatei-Download als geschützten Attachment-Stream implementiert: 64-KiB-Blöcke, zwei parallele Downloads je Verbindung, keine vollständigen Datei-Blobs im Browser oder Backend.
- [x] Kurzlebige HA-Downloadsignatur pro Dokument/Downloadart und aktueller Anmeldung; feste Upstream-Pfade, keine Redirects und sichere Dateinamen.
- [x] Laufende Upstream-Antworten bei Unload schließen; Anmeldung und Rechte während Streaming prüfen.
- [x] Lokal 103 Client-Tests und 19 Frontend-Tests bestanden, einschließlich großer synthetischer Dateien, Größenmeldung und Original-Download.
- [x] [CI 0.1.0-dev.7](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41289561585) vollständig bestanden: 103 Client-Tests je Python-Version, 37 HA-Frameworktests und 19 Frontendtests. Dateien auf ha-test übertragen und zurückgelesen geprüft; Konfiguration validiert, nur Test-HA neu gestartet.
- [x] Einrichtung/Updates zuerst live geprüft: ungültiger neuer Schlüssel abgewiesen, alte Verbindung erhalten, leerer Schlüssel beibehalten, gültigen vorhandenen Schlüssel erneut gespeichert, temporäre Browser-Adresse geändert und wiederhergestellt, Reload mit Suche und genau einer automatisch auf dev.7 aktualisierten Ressource erfolgreich.
- [x] Anschließend PDF- und Original-Download über ha-test vollständig gestreamt abgerufen; Attachment/no-store und Ablehnung ohne Anmeldung/Signatur geprüft. Such-/PDF-/Thumbnail-Regressionsprüfungen bestanden.
- [x] Beide Download-Buttons im Browser sichtbar geprüft, PDF-Button angeklickt und Übergabe bestätigt. Browserautomation lieferte kein Download-Abschlussereignis; tatsächliches Speichern über die Browseroberfläche bleibt unbestätigt.
- [x] Große Karte zusätzlich in einer temporären regulären Sections-Ansicht mit Suche, Bildern und Dokumentauswahl visuell geprüft. Testansicht entfernt, ursprüngliche zwei Ansichten exakt erhalten. File editor gestoppt, Start bleibt manuell.
- [ ] Companion-/weitere Browser und native PDF-Seitenwahl/Zoom nur mit vorhandenen Geräten praktisch abnehmen; fehlende Abdeckung bleibt offen.

Details: [Dateien und Downloads](docs/downloads.md), [Einrichtung und Updates](docs/setup-updates.md).

## Vorheriger Entwicklungsschritt – Einrichtung und Updates 0.1.0-dev.6

- [x] Automatische versionierte Registrierung/Aktualisierung der eigenen Karten-Ressource für HA-Storage-Dashboards implementiert; doppelte eigene Einträge bereinigen, fremde Ressourcen erhalten.
- [x] Neuladen erhält die gemeinsame Ressource; Entfernen der letzten Verbindung entfernt nur die eigene Modulressource. YAML-Ressourcen werden nicht verändert.
- [x] Reconfigure: leerer/fehlender Schlüssel behält den bisherigen Schlüssel; neuer Schlüssel wird vor Speicherung geprüft. Einrichtung und Reauth verlangen weiterhin gültige Zugangsdaten.
- [x] Zusätzliche HA-Tests für unveränderte Einstellungen bei ungültiger Anmeldung, Behalten des Schlüssels, Reload/Ressourcenupdate und Entfernen mehrerer Einträge geschrieben.
- [x] Reconfigure mit ungültigem/leeren/gültigem Schlüssel und Reload auf ha-test erfolgreich geprüft; Reauth-Erfolg und Ablehnung mit unveränderten Einstellungen im echten HA-Testframework geprüft. Kein tatsächlicher Paperless-Schlüssel widerrufen. Automatisches Ressourcenupdate live bestätigt.
- [x] Danach Dateien/Darstellung und Downloads gemeinsam umgesetzt; siehe dev.7 mit 20-MiB-Vorschaugrenze und gestreamten Downloads.
- [ ] Browser-/Companion-Abdeckung ehrlich getrennt dokumentieren; optionale persönliche API-Schlüssel bleiben zuletzt.

## Vorheriger Entwicklungsstand – Große Karte und Editor 0.1.0-dev.5

- [x] Große Karte `custom:paperless-ngx-insights-documents` mit gemeinsamer Suche, Pagination, Datum und geschützten Vorschaubildern implementiert.
- [x] Eingebettete Dokumentansicht neben der Trefferliste; schmale Kartenbreiten wechseln zwischen Liste und Dokument, mit Rückweg und Fokusrückgabe.
- [x] Vorschaubilder bedarfsgeladen mit IntersectionObserver, maximal drei Abrufe gleichzeitig; Fehler einzelner Bilder blockieren die Liste nicht. URLs/Abrufe bei Seitenwechsel und Entfernen freigegeben.
- [x] Visueller Editor für beide Karten: Verbindungsauswahl, Überschrift, Suchbereich, Trefferzahl; kompakt zusätzlich Klickverhalten, groß zusätzlich Höhe und Vorschaubilder. Zusätzliche YAML-/Layoutoptionen bleiben erhalten.
- [x] Lokale Frontendtests: 17 erfolgreich, einschließlich Vorschauwechsel, Pagination, Bildfehler, begrenzter Parallelität und Editorereignissen/Validierung.
- [x] [GitHub Actions](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41249145583) vollständig grün: 90 Client-Tests unter Python 3.10/3.14, 23 HA-Frameworktests und 17 Frontend-Tests.
- [x] Auf ha-test installiert, Dateien vollständig zurückgelesen geprüft, Konfiguration validiert und ausschließlich Test-HA neu gestartet. Große Karte als Panel-Ansicht [Dokumente](http://192.168.178.147/paperless-test/dokumente) ergänzt; bisherige Suche bleibt erhalten.
- [x] Live im eingebauten Browser bei 1280×720 und 390×844 geprüft: Suche mit zehn Treffern, geladene Vorschaubilder/Datum, eingebettete Bildvorschau, Umblättern auf 11–20, Auswahl zurücksetzen sowie mobile Rücknavigation mit Fokusrückgabe erfolgreich.
- [x] Beide visuellen Editoren in der tatsächlichen HA-Oberfläche geöffnet. Große Karte: Überschrift im Editor geändert und gespeichert; neue Konfiguration anschließend über MCP zurückgelesen (Titel Dokumentübersicht, übrige Optionen erhalten). Kompakte Karte zeigt Verbindung/Suchmodus/Seitenzahl/Klickverhalten korrekt.
- [x] Bestehende Suche und geschützte PDF-/Thumbnail-Endpunkte nach Installation erneut live erfolgreich geprüft; anonyme Abrufe 401, ungültige ID 400. File editor anschließend gestoppt; Start bleibt manuell.
- [x] Große Karte zusätzlich in regulärer Sections-Ansicht live geprüft (01.11.2026, dev.7); temporäre Testansicht anschließend entfernt.
- [ ] Companion-/weitere Browser, Screenreader und große Dateien/Streaming bleiben offen; PDF-Seitenwahl/Zoom hängt weiterhin vom nativen Browser-Viewer ab.

Details: [Große Karte und Editor](docs/document-card.md).

## Vorheriger Entwicklungsstand – PDF-Vorschau 0.1.0-dev.4

- [x] Nutzerrückmeldung: Vorschau funktioniert im eigenen Browser ohne Probleme. Browsertyp/-version und einzelne Funktionen wie Seitenwahl/Zoom wurden dabei nicht separat benannt; die breitere Browser-/Companion-Prüfung bleibt offen.

- [x] Geschützten PDF-Endpunkt mit HA-Authentifizierung und aktiven Adminrechten implementiert; feste Dokument-IDs, keine Weiterleitungen oder öffentlichen Dokumentlinks.
- [x] PDF-Typ und Signatur prüfen; begrenzter Abruf bis 20 MiB mit Timeouts, kein Servercache.
- [x] Kompakte Karte um `open_mode: preview` mit Dialog, Download und Paperless-Fallback erweitert; bisheriger Standard `paperless` bleibt erhalten.
- [x] Abbruch, Freigabe von Blob-URLs, Fokus nach Schließen und Verwerfen verspäteter Vorschauantworten implementiert.
- [x] Lokal 90 Client-Tests und 11 Frontend-Tests bestanden; Ruff, Format und Kompilierung erfolgreich. Größenlimit auch ohne Content-Length geprüft.
- [x] Geschützte Raster-Bildvorschau der ersten Seite als Fallback ergänzt (PNG/JPEG/WebP, maximal 2 MiB, dieselben Adminrechte); ohne nativen PDF-Viewer automatisch, sonst per Button.
- [x] [GitHub Actions](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41248280037) vollständig erfolgreich: 90 Client-Tests jeweils unter Python 3.10/3.14, 23 HA-Frameworktests und 11 Frontend-Tests.
- [x] Dateien auf ha-test übertragen und zurückgelesen geprüft; Konfiguration validiert und ausschließlich Test-HA neu gestartet. PDF und Thumbnail authentifiziert erfolgreich, ohne Anmeldung jeweils 401; ungültige ID 400; no-store bestätigt. Suchregression live bestanden.
- [x] Test-Dashboard auf open_mode: preview umgestellt; Ressource auf ?v=0.1.0-dev.4-r2 aktualisiert. File editor anschließend gestoppt, Start bleibt manuell.
- [x] Sichtprüfung im eingebauten Browser bei schmaler Ansicht und 1366×900: Dialog, Bildvorschau der ersten Seite, Schließen mit Fokusrückgabe und erneutes Öffnen eines anderen Dokuments erfolgreich. Keine Dokumentinhalte ins Repository übernommen.
- [ ] Vollständige native PDF-Anzeige mit Seitenwahl/Zoom in eigenständigen Browsern und Companion praktisch prüfen. Im eingebauten Browser bleibt der native Viewer leer; der manuelle Button zur ersten Bildseite funktioniert. Automatische Umschaltung bei pdfViewerEnabled=false ist implementiert, meldete sich hier aber nicht.
- [ ] Große Dokumentkarte, Thumbnails, große Dateien/Streaming und weitere Browser bleiben offen.

Entscheidung und Grenzen: [PDF-Vorschau](docs/pdf-preview.md).

## Vorheriger Entwicklungsstand – Mehrwortsuche 0.1.0-dev.3

- [x] Mehrere Suchbegriffe werden sicher mit UND verknüpft; Reihenfolge und Groß-/Kleinschreibung verändern die geprüften Treffer nicht.
- [x] Titelmodus begrenzt jeden Begriff auf den Titel; Inhaltsmodus erlaubt Begriffe über Titel und Dokumenttext verteilt.
- [x] Einwort-/Teilwortsuche erhalten; doppelte Anführungszeichen für Wortfolgen unterstützt.
- [x] Suchwerte gegen das Einschleusen von Feldern/Operatoren maskiert; ungeschlossene Anführungszeichen und mehr als 32 Begriffe werden kontrolliert abgewiesen.
- [x] Kartenhinweis und verständliche Fehlermeldung ergänzt.
- [x] Lokale Regressionstests: **64 Client-Tests**, **7 Frontend-Tests**, Ruff, Formatprüfung und Kompilierung bestanden.
- [x] Direkte Paperless-Live-Prüfung: **telekom rechnung mai liefert vier Treffer**. Umgestellte Reihenfolge, Großbuchstaben, engere Wortfolge, fehlender Begriff, getrennte Suchbereiche und Pagination erfolgreich geprüft.
- [x] Version 0.1.0-dev.3 auf **ha-test / 192.168.178.147** übertragen und zurückgelesen geprüft; Konfiguration validiert und ausschließlich das Testsystem neu gestartet.
- [x] Neue Suche über die tatsächliche HA-WebSocket-Schnittstelle unter dem Testbenutzer geprüft, einschließlich kontrollierter Fehlermeldung bei ungeschlossenen Anführungszeichen.
- [x] Frontend-Ressource auf ?v=0.1.0-dev.3 aktualisiert; Auslieferung des neuen Moduls geprüft. File editor anschließend wieder gestoppt.
- [x] [GitHub-Actions-Lauf](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41201471773) vollständig erfolgreich: jeweils 64 Client-Tests unter Python 3.10/3.14, 13 HA-Frameworktests und 7 Frontend-Tests.
- [x] Browser-Anbindung wieder verfügbar; Mehrwortsuche und Vorschau in 0.1.0-dev.4 erneut visuell geprüft. Der frühere Verbindungsfehler ist behoben.
- [ ] Eingebettete PDF-Vorschau und große Dokumentkarte weiterentwickeln.

Details und Grenzen: [Mehrwortsuche](docs/multiword-search.md).
Keine privaten Dokumentinhalte oder Zugangsdaten wurden in das Repository übernommen.

## Vorheriger Entwicklungsstand – 0.1.0-dev.2

**0.1.0-dev.2: Backend und erste kompakte Suchkarte auf ha-test eingerichtet.**

- [x] Integrationsdateien und Suchkarten-Modul auf **192.168.178.147** übertragen und vollständig zurückgelesen/per Hash geprüft.
- [x] HA-Konfiguration geprüft, ausschließlich ha-test neu gestartet und Paperless über den regulären Config Flow eingerichtet.
- [x] Integration meldet **loaded**. Der bereitgestellte Schlüssel ist im HA-Konfigurationseintrag hinterlegt, nicht im Repository.
- [x] Dashboard **Paperless** mit Ansicht **Suche** und versionierter JavaScript-Ressource angelegt: [Test-Dashboard](http://192.168.178.147/paperless-test/suche).
- [x] Im Browser geprüft: Karte lädt, fünf Titel pro Seite, Weiterblättern auf Treffer 6–10, neue Titelsuche setzt Seite auf 1 zurück, Auswahl Titel/Inhalt und Links für neue Tabs vorhanden.
- [x] Neue kompakte Karte mit sicherer Textausgabe, getrenntem Suchzustand, Lade-/Fehlerzuständen und Verwerfen veralteter Antworten implementiert.
- [x] Lokale Tests: **52 Client-Tests**, **6 Frontend-Tests**, Ruff, Format- und Kompilierungsprüfung bestanden.
- [x] Dashboard-Ausbaustufe in GitHub Actions vollständig erfolgreich geprüft: [Lauf](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41198510108).
- [x] Abschließender [GitHub-Actions-Lauf](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41198644757) vollständig erfolgreich: 52 Client-Tests jeweils unter Python 3.10/3.14, 13 HA-Frameworktests und 6 Frontend-Tests.
- [x] Lesende Paperless-Live-Tests mit API-Schlüssel: Titel-/Inhaltssuche, rein inhaltlicher Treffer, Pagination, keine Treffer, Textvorschau/-download, Vorschaubild und PDF-Vorschau erfolgreich.
- [x] HACS-Installationsversuch untersucht: private Repository-Adresse liefert für den HACS-Zugang HTTP 404. Repository blieb privat.
- [x] Stattdessen offizielle File-editor-App 6.3.0 und regulären angemeldeten Ingress-Zugang für die Übertragung verwendet. Netzwerkbeschränkung unverändert; App anschließend gestoppt und auf manuellen Start gesetzt.
- [ ] Eingebettete Dokumentvorschau, große Dokumentkarte, visueller Karteneditor und HACS-Auslieferung fertigstellen.
- [ ] Reload/Reauth, differenzierte Benutzer-/Dokumentrechte, große Dateien und weitere Browser vollständig live prüfen.

Dokumentlinks öffnen derzeit die Paperless-Oberfläche im neuen Tab; dort kann eine eigene Anmeldung nötig sein.
Es gibt noch keine eingebettete PDF-Vorschau. **M0, M1 und M3 sind insgesamt noch nicht abgeschlossen**:
PDF-Authentifizierung, vollständige Verbindungs-/Reauth-Prüfung und verbleibende Kartenfunktionen fehlen.

Details: [Live-Testbericht](docs/live-tests.md), [Architektur](docs/architecture.md).
Alle Live-HA-Arbeiten fanden ausschließlich auf dem vom Benutzer freigegebenen Testsystem statt.

## Nutzertest und geplante Suchverfeinerung – 31.10.2026

- [x] Benutzer bestätigt: erste Version funktioniert; Seitennavigation und Umblättern verhalten sich wie gewünscht.
- [x] Kombinierte Suchbegriffe verbessern: Beispiel **telekom rechnung mai** liefert im Nutzertest keine Treffer.
- Ausgangslage in 0.1.0-dev.2: Die Filter suchten eine zusammenhängende Teilzeichenfolge. In 0.1.0-dev.3 ist die geprüfte UND-Suche umgesetzt; Details stehen im aktuellen Entwicklungsstand.
- [x] Mehrwortsuche über getrennte Begriffe prototypisch prüfen, insbesondere UND-Verknüpfung unabhängig von Position und Reihenfolge.
- [x] Moderne indexbasierte Paperless-Suche mit der bestehenden Teilstringsuche vergleichen; Verhalten anhand der tatsächlichen Serverversion belegen.
- [x] Festlegen und in der Oberfläche erklären, ob normale Eingaben alle Wörter verlangen und Anführungszeichen eine exakte Wortfolge bedeuten.
- [ ] Groß-/Kleinschreibung, Umlaute, Satzzeichen, Teilwörter, Wortreihenfolge und fehlende Begriffe prüfen.
- [x] Regressionstests: Einwortsuche, **telekom rechnung mai**, umgestellte Wortreihenfolge, exakte Phrase und keine Treffer. Trefferzahl, stabile Sortierung und Pagination auch mit mehreren Wörtern überprüfen.
- [x] Suchmodus Titel gegenüber Titel/Inhalt getrennt prüfen; Begriffe innerhalb desselben Dokumentes über verschiedene Felder hinweg berücksichtigen.
- Diese Verfeinerung wurde mit 0.1.0-dev.3 auf dem Testsystem umgesetzt. Weitere Suchoptionen bleiben gesonderte Erweiterungen.

## 1. Ausgangslage und Arbeitsweise

- [x] Repository und Schreibzugriff identifiziert.
- [x] Stammverzeichnis und README geprüft: bislang README.md und LICENSE, keine Implementierung, Tests oder AGENTS.md vorhanden.
- [x] Anforderungen aus der Abstimmung in diesen Plan übertragen.
- [ ] Lizenztext und Verpflichtungen für Quellcode, eingebundene Bibliotheken und Release-Artefakte prüfen.
- [ ] Bei jedem Arbeitspaket Status, Prüfergebnis und gegebenenfalls Beleg/Commit ergänzen.
- [ ] Nicht durchgeführte Tests ausdrücklich als offen markieren; geplantes Verhalten nicht als bereits implementiert darstellen.

Dieser Plan wird mit jedem abgeschlossenen Entwicklungsschritt und jeder relevanten Prüfung aktualisiert. Erledigte Implementierung, tatsächlich bestandene Tests, offene Prüfungen und Einschränkungen getrennt dokumentieren.

### Verbindliche Entwicklungs- und Testumgebung

- Ausschließlich den MCP-Server **ha-test** für Entwicklung, Installation und Live-Tests dieser Integration verwenden.
- Vom Benutzer zugeordnetes Testsystem: **192.168.178.147**. Der produktive Home Assistant darf für diese Entwicklung und Tests nicht verwendet oder verändert werden.
- Vor jeder Live-Änderung sicherstellen, dass der Aufruf über ha-test erfolgt; niemals auf den produktiven MCP-Server ausweichen, wenn ha-test nicht verfügbar ist.
- Lokale Builds und automatisierte Tests mit Mocks sind ergänzend zulässig; alle Live-HA-Tests erfolgen ausschließlich auf dem genannten Testsystem.
- Zugangsdaten und Tokens weder hier noch in Quellcode, Test-Fixtures oder Commit-Nachrichten speichern.
- [x] 31.10.2026: Verbindung über ha-test erfolgreich geprüft (ha_get_overview, success=true).
- Gemeldeter Stand: Home Assistant **2026.10.4**, Zustand **RUNNING**, ha-mcp **9.0.0**.
- Die vom MCP-Server gemeldete interne Basisadresse ist http://supervisor/core. Die IP-Zuordnung stammt aus der Benutzerangabe und ist dadurch nicht unabhängig bestätigt.
- Integration und Suchkarte inzwischen installiert und im Browser geprüft; siehe aktuellen Entwicklungsstand und Live-Testbericht.

## 2. Vereinbarter Funktionsumfang

### Integration

- [x] Einrichtung über Config Flow mit Paperless-Adresse und API-Schlüssel implementiert und auf ha-test erfolgreich ausgeführt.
- [x] Zugriff auf Dokumentliste vor Abschluss der Einrichtung prüfen; mit bereitgestelltem Schlüssel auf ha-test bestätigt.
- [x] Schlüssel ausschließlich serverseitig verwenden; Karten verwenden die HA-WebSocket-Schnittstelle und enthalten keine Paperless-Zugangsdaten.
- [x] Adresse und Schlüssel nachträglich ändern; bei leerem Feld Schlüssel behalten. Live geprüft; Reauth im HA-Framework einschließlich ungültiger Eingaben geprüft.
- [x] Optional getrennte interne API-Adresse und vom Browser erreichbare Paperless-Adresse unterstützen; Links verwenden Browser-Adresse, Vorschau die interne API.
- [x] Mehrere Integrationseinträge architektonisch berücksichtigen; Karten wählen per entry_id. Paralleler Live-Test mit zwei Servern bleibt offen.

### Karte A: kompakte Suche

- [x] Eigenständiger Kartentyp mit Suchfeld und Auswahl Titel / Titel und Inhalt.
- [x] Standardmäßig fünf Titel pro Ergebnisseite, Anzahl pro Karte einstellbar.
- [x] Vor-/Zurück-Pfeile, korrekt deaktivierte Randpfeile und verständliche Trefferanzeige.
- [x] Dokumenttitel anklickbar; Verhalten pro Karte über open_mode auswählbar: PDF-Vorschau in Home Assistant oder Öffnen in Paperless. Live-Abnahme siehe aktuellen Entwicklungsstand.
- [x] Ladezustand, keine Treffer, noch keine Suche und Fehler jeweils eindeutig darstellen.
- [x] Im Normalbetrieb keine Vorschaubilder laden; die Karte soll kompakt bleiben.

### Karte B: Dokumentübersicht für einen ganzen Dashboard-Tab

- [x] Separater Kartentyp mit gemeinsamer Suchlogik, Trefferliste und geschützten Vorschaubildern.
- [x] Große Dokumentvorschau nach Auswahl; native PDF oder Bildfallback der ersten Seite.
- [x] Desktop: Treffer und Vorschau nebeneinander; Mobil: Wechsel zwischen Liste und Dokument mit Rückweg.
- [x] Panel-Ansicht installiert und geprüft; reguläre Layouts über Kartenbreite/Container Query unterstützt. Zusätzliche Live-Abnahme in Sections bleibt oben offen.
- [x] Öffnen in Paperless und Download der geladenen PDF-Vorschau vorhanden. Originaldatei-Download bleibt gesondert offen.
- [x] Seitennavigation und Seitengröße unabhängig von der kompakten Karte konfigurierbar (Standard groß 10, kompakt 5).

### Abgrenzung und spätere Erweiterungen

- Die erste Version arbeitet lesend. Upload, Bearbeitung, Löschen, KI-Suche und Synchronisation des gesamten Archivs gehören nicht zum vereinbarten Kern.
- Suche nach Titel bezeichnet zunächst den Paperless-Dokumenttitel. Suche nach Originaldateinamen ist gesondert zu prüfen.
- Inhaltsuche verwendet den in Paperless verfügbaren Text. Fehlende oder fehlerhafte OCR wird nicht von der Integration repariert.
- Tags, Korrespondenten, Dokumenttypen und Datumsfilter sind mögliche spätere Erweiterungen.
- Eine zusätzliche Seite in der HA-Seitenleiste ist optional; für die große Karte ist zunächst ein normaler Dashboard-Tab ausreichend.

## 3. Recherche und technische Nachweise vor Implementierung

Für jede Prüfung festhalten: untersuchte Version, Quelle/Schema, Ergebnis, gewählte Lösung und Einschränkungen. Online-Dokumentation kann neuer als die tatsächlich installierte Version sein.

### R1: Versionen und API-Vertrag

- [ ] Unterstützte Mindestversionen von Home Assistant, Python und Paperless-ngx ermitteln und begründen.
- [x] Paperless-API-Schema der vorgesehenen Testinstanz unter /api/schema/?format=json geprüft; Suchfilter und Dokument-Endpunkte vorhanden.
- [ ] Authentifizierungsheader, API-Versionierung und Kompatibilitätserkennung untersuchen.
- [x] Implementierte Teilstringsuche über title__icontains und title_content mit echtem Testzugang erfolgreich geprüft.
- [ ] Optionale erweiterte Volltextsuche und moderne indexbasierte Suchparameter vergleichend prüfen.
- [ ] Unterschiede zwischen Teilwort-, Wort-, Phrasen- und Suchsyntax-Verhalten anhand von Testdokumenten belegen.
- [ ] Pagination, Trefferzahl, maximale Seitengröße, Sortierung und Verhalten bei gleichen Sortierwerten prüfen.
- [x] Titel- und Inhaltssuche mit Sortierung -created,-id live geprüft; auch ausschließlich im Inhalt vorkommender Begriff erfolgreich getestet.
- [ ] Antwortfelder für Titel, Datum, Vorschau, MIME-Typ und Dokument-ID prüfen; unnötige Inhaltsfelder vermeiden.
- [ ] Vorschau-, Thumbnail-, Download- und Metadaten-Endpunkte sowie Links auf die Paperless-Dokumentansicht verifizieren.
- [ ] Originaldatei gegenüber Archiv-PDF, fehlende Archivdatei und gegebenenfalls Dokumentversionen untersuchen.
- [ ] Request-/Response-Beispiele anonymisiert als Test-Fixtures und API-Vertrag dokumentieren.

### R2: Zugriffsmodell

**Zurückgestellt:** Erweiterte Freigaben und unterschiedliche Benutzerzugänge stehen
am Ende der Agenda (Abschnitt 14). Nachweise für den bestehenden Adminzugriff bleiben
Teil der normalen Sicherheitsprüfung. Die folgenden offenen Mehrbenutzerpunkte
blockieren die erste Veröffentlichung nicht.

- [ ] Festlegen, welche HA-Benutzer welchen Integrationseintrag benutzen dürfen; serverseitige Prüfung pro Anfrage.
- [ ] Gemeinsamer Paperless-Schlüssel bedeutet gemeinsame Paperless-Rechte: Auswirkungen dokumentieren.
- [ ] Dashboard-Sichtbarkeit ausdrücklich nicht als Zugriffsprüfung verwenden.
- [ ] Verhalten für HA-Administrator, normalen Benutzer, nicht freigeschalteten Benutzer und abgemeldeten Browser definieren.
- [ ] Nachweisen, dass auch direkte Dokument-ID-Aufrufe, Thumbnails, Vorschau und Download dieselben Rechte prüfen.
- [ ] Paperless-seitige Dokumentrechte mit eingeschränktem Testbenutzer prüfen.
- [x] Entscheidung für die erste Ausbaustufe: nur HA-Administratoren. Benutzerfreigaben werden vor einer späteren Erweiterung gesondert umgesetzt.

### R3: Dokumentanzeige und Authentifizierung

- [ ] Aktuelle HA-Schnittstellen für eigene WebSocket-Befehle und geschützte HTTP-Antworten prüfen.
- [x] PDF-Anzeige als authentifizierter Abruf mit Blob-URL und nativem Viewer gewählt; keine PDF.js-Abhängigkeit. Entscheidung und Grenzen in docs/pdf-preview.md.
- [x] Authentifizierungsweg implementiert: callApiRaw sendet HA-Bearer, Viewer lädt nur lokale Blob-URL. Keine Anmeldeheader von iframe/neuem Tab voraussetzen.
- [x] Für speicherschonende Downloads HA-Pfadsignatur mit 30 Sekunden Gültigkeit, Bindung an aktuelle Anmeldung, Adminprüfung und no-store umgesetzt. Ablauf/manipulierter Pfad/Nicht-Admin automatisiert, tatsächlicher Abruf live geprüft; Details in docs/downloads.md.
- [x] Vorschau bleibt auf 20 MiB begrenzt, Downloads werden in 64-KiB-Blöcken gestreamt. Synthetische Dateien über 25 MiB im Client und HA-HTTP-Pfad geprüft. Byte-Range/Resume ist ausdrücklich nicht implementiert; detaillierte Leistungsbaseline bleibt offen.
- [ ] PDF-Anzeige in Chrome/Edge, Firefox, Safari und Companion-WebViews praktisch testen.
- [x] Für nicht darstellbare Formate und fehlende Vorschau Original-Download, Bildvorschau und Paperless-Link angeboten.
- [x] Unterschied zwischen Paperless-Anmeldung im neuen Tab, HA-Vorschau und kurzlebigem HA-Download dokumentiert.

### R4: Installation und Frontend

- [ ] Aktuelle HA-Konventionen für Config Flow, Reauth/Reconfigure, Lifecycle und statische Ressourcen prüfen.
- [ ] Gemeinsames Repository für Integration und zwei Karten auf HACS-Kompatibilität untersuchen; nicht zwei Repository-Kategorien ungeprüft voraussetzen.
- [ ] Entscheiden, ob gebaute Karten mit der Integration ausgeliefert und versioniert als Ressource registriert werden.
- [x] Gemeinsame Ressource automatisch registrieren/aktualisieren, eigene Duplikate entfernen, bei letztem entfernten Eintrag aufräumen. Zwei Einträge/Reload/Update/Entfernen im HA-Framework und Ressourcenupdate mit Reload live geprüft; laufende Browserseiten müssen neu geladen werden.
- [ ] Geeignete Frontend-Basis, Testwerkzeuge und gegebenenfalls PDF-Bibliothek nach Wartung, Lizenz und Bundlegröße auswählen.
- [ ] Entscheidung zu nativer PDF-Anzeige oder eigener Viewer-Bibliothek durch einen kleinen technischen Prototyp absichern.

Freigabekriterium für die folgenden Schritte: Suchvertrag, Benutzerzugriff und authentifizierte PDF-Anzeige sind praktisch belegt. Unsichere Annahmen werden vor der eigentlichen Kartenentwicklung aufgelöst.

## 4. Projektgrundlage und Testumgebung

Abhängigkeit: R1 und erste Entscheidungen aus R4.

- [ ] Öffentliche Kartennamen festlegen; Integrationsdomain paperless_ngx_insights ist implementiert.
- [ ] Struktur anlegen: custom_components/<domain>/, frontend/, tests/, docs/ und .github/workflows/.
- [ ] Manifest, Config Flow, Übersetzungen (Deutsch/Englisch), Versionsverwaltung und Entwicklungsanleitung vorbereiten.
- [ ] Reproduzierbare Python-/Frontend-Abhängigkeiten und Build-Befehle festlegen.
- [ ] Isolierte HA-/Paperless-Testumgebung und eingeschränkten Paperless-Testbenutzer einrichten.
- [ ] Künstliche Dokumente mit bekannten Titeln und eindeutigen Inhaltsbegriffen erstellen; keine privaten Dokumente in Fixtures.
- [ ] Testarchiv mit 0, 1, 5, 6, 10 und 11 Treffern sowie größerer Datenmenge vorbereiten.
- [ ] Mehrseitiges PDF, großes PDF, Bild, nicht direkt darstellbare Datei und fehlende Vorschau abdecken.

Abnahme: Eine frische Entwicklungsumgebung kann Backend-Tests und Frontend-Build nach dokumentierten Schritten ausführen.

## 5. Backend: Verbindung und Einrichtung

Abhängigkeit: Projektgrundlage, R1 und Zugriffsentscheidung R2.

- [x] Asynchronen Paperless-Client mit verwalteter Sitzung, Timeouts und begrenzter Parallelität implementieren.
- [x] Eingabeadresse normalisieren; HTTP/HTTPS, IPv4, Hostname, Port und Unterpfad korrekt behandeln.
- [x] TLS-Prüfung standardmäßig aktivieren; keine Abschaltoption. Lokale eigene CA-Zertifikate noch gesondert prüfen.
- [ ] Fehlerklassen für ungültige Anmeldung, fehlende Rechte, Nichterreichbarkeit, TLS, inkompatible API und fehlerhafte Antworten vorsehen.
- [x] Config Flow mit sicherem Schlüsselfeld und aussagekräftigen deutschen/englischen Fehlermeldungen implementieren.
- [x] Reauth/Reconfigure und sichere Aktualisierung bestehender Einstellungen implementiert und im HA-Framework getestet. Vollständiger Live-Test bleibt offen.
- [x] Doppelte Einträge erkennen und verschiedene Server getrennt verwalten; automatisierte HA-Tests mit zwei Einträgen. Zwei physisch getrennte Server nicht live vorhanden.
- [x] Setup/Unload/Reload/Entfernen einschließlich gemeinsamer Ressource im HA-Framework geprüft; Reload live erfolgreich. Upstream-Antworten werden bei Unload geschlossen, HA-Sitzung bleibt HA-eigen.
- [x] Diagnosedaten mit redigierten Schlüsseln und ohne Dokumentinhalt bereitstellen.
- [x] Keine Dokumentlisten, Suchbegriffe oder Volltexte als globale Sensorattribute oder Recorder-Daten ablegen.

Tests: gültige/ungültige Adresse, falscher/abgelaufener Schlüssel, 401/403, Timeout, DNS-/TLS-Fehler, fehlerhaftes JSON, inkompatible API, Reload und zwei Einträge.

Abnahme: Einrichtung gelingt mit gültigem Zugriff; Fehler bleiben verständlich und enthalten keine Zugangsdaten.

## 6. Backend: Suche und Dokumentzugriff

Abhängigkeit: Backend-Verbindung, verifizierter Suchvertrag und R3.

- [x] Authentifizierten Suchbefehl mit Integrationseintrag, Suchmodus, Suchtext, Seite und Seitengröße implementieren.
- [x] Eingaben validieren und begrenzen; Seitengröße und parallele Abfragen begrenzen.
- [x] Nur benötigte Antwortfelder übertragen; Dokumentinhalt standardmäßig nicht an Karten senden.
- [ ] Stabile Seitennavigation und definiertes Verhalten für leere Suche und verschwundene Treffer implementieren.
- [x] Metadaten sowie geschützte Thumbnail-/Vorschau-/PDF- und Original-Download-Endpunkte vorhanden.
- [x] Jede Anfrage prüft HA-Anmeldung, Adminrechte und geladenen Eintrag; Streaming prüft Zugriff erneut während des Transfers. Erweiterte Benutzerfreigaben bleiben Abschnitt 14.
- [x] Feste Upstream-Pfade aus konfigurierter Basis und validierter Dokument-ID; kein allgemeiner URL-Proxy.
- [x] Redirects deaktiviert und Upstream-Pagination-URLs nicht verfolgt; automatisiert geprüft.
- [x] PDF/Bild-Typ und Signatur prüfen; Downloads mit bereinigtem Dateinamen als Attachment, Originale als octet-stream mit nosniff/Sandbox. HTML/SVG werden nicht inline ausgeführt.
- [ ] Caches nur begrenzt und getrennt nach Integration/Zugriffskontext verwenden; bei Schlüsselwechsel und Unload leeren.
- [ ] Fehlerbehandlung für 404, 429, 5xx, abgebrochene Downloads und verweigerte Dokumentrechte ergänzen.

Tests: Sonderzeichen, Umlaute, Leerzeichen, lange Suche, ungültige IDs, fremder Eintrag, nicht autorisierter Benutzer, manipulierte URLs, Seitenränder und alle Fehlerpfade.

Abnahme: Suche und Dokumentabruf funktionieren ohne Browserzugriff auf den internen Paperless-Server; keine Geheimnisse verlassen das Backend.

## 7. Gemeinsame Frontend-Bausteine

Abhängigkeit: Backend-Schnittstellen.

- [ ] Gemeinsamen Client und typisierte Antwort-/Fehlermodelle für beide Karten anlegen.
- [ ] Suchzustand je Karteninstanz isolieren; Suchtext und Auswahl nicht global speichern.
- [x] Suche per Enter/Suchbutton umgesetzt; keine Anfragen bei jeder Eingabe oder jedem HA-Zustandsupdate.
- [x] Bei neuer Suche Seite auf 1 zurücksetzen und veraltete Antworten verwerfen.
- [ ] Suchwechsel, schnelles Blättern und Verbindungsabbruch ohne vertauschte Ergebnisse behandeln.
- [ ] Wiederverwendbare Seitennavigation, Statusanzeige und Vorschaukomponente erstellen.
- [ ] HA-Themes, Tastaturbedienung, Fokus, Beschriftungen und Screenreader berücksichtigen.
- [x] Sichere Textausgabe statt ungeprüftem HTML aus Dokumenttiteln oder Suchtreffern; Frontendtests bestanden.
- [x] Vorschau-Blob-URLs und Frontend-Abrufe bei Wechsel/Entfernen aufräumen; bereits laufende Upstream-Abrufe sind zeitlich begrenzt. Weitere gemeinsame Komponenten für die große Karte bleiben offen.

Tests: verspätete Antwort überschreibt keine neue Suche; zwei Karten beeinflussen sich nicht; Sonderzeichen werden als Text dargestellt; kein wiederholter Request bei jedem HA-Zustandsupdate.

## 8. Kompakte Suchkarte entwickeln

Abhängigkeit: gemeinsame Frontend-Bausteine.

- [x] Kartentyp, Kartenauswahl-Eintrag und visuellen Editor bereitgestellt und auf ha-test geöffnet.
- [x] Optionen: Integrationseintrag, Überschrift, Suchmodus, Treffer pro Seite (Standard 5), Klickverhalten.
- [x] Titelzeilen ohne dauerhaft geladene Thumbnails umgesetzt; Titel umbrechen und werden als Text ausgegeben.
- [x] Vor-/Zurück-Pfeile und Trefferbereich korrekt berechnen.
- [x] PDF-Vorschau-Dialog und Öffnen der Paperless-Ansicht per Nutzerklick angebunden; Download der geladenen Vorschau verfügbar. Browserabnahme siehe aktuellen Stand.
- [x] Konfigurationsfehler und entfernten Integrationseintrag verständlich anzeigen.

Tests: 0/1/5/6/10/11 Treffer, erste/letzte Seite, neue Suche von späterer Seite, gelöschtes Dokument, Dialog schließen, Pop-up-Verhalten, Touch und Tastatur.

Abnahme: Bei 6 Treffern zeigt die Karte zunächst 5 Titel, dann 1 Titel; Navigation und beide Klickoptionen funktionieren.

## 9. Große Dokumentkarte entwickeln

Abhängigkeit: gemeinsame Komponenten und erprobter Vorschauweg.

- [x] Eigener Kartentyp mit visuellem Editor und gemeinsamem Konfigurationsmodell.
- [x] Treffer mit Titel, Datum und bedarfsgeladenen Vorschaubildern anzeigen.
- [x] Desktop-Aufteilung und mobile Navigation zwischen Liste/Vorschau implementiert und live geprüft.
- [x] Konfigurierbare Höhe, getrennte Scrollbereiche und Größenangaben implementiert. Panel live geprüft; zusätzliche Sections-Abnahme bleibt offen.
- [ ] PDF-Seitenanzeige/Zoom entsprechend der gewählten Viewer-Lösung bereitstellen.
- [x] Öffnen in Paperless, Download der geladenen Vorschau-PDF und Bild-/Öffnen-Fallback angebunden.
- [x] Auswahl beim Such-/Seitenwechsel eindeutig zurücksetzen; veraltete Vorschauantworten verwerfen. Automatisiert und live geprüft.
- [x] Fehler einzelner Thumbnails blockieren die übrige Trefferliste nicht; automatisiert geprüft.

Tests: mehrere PDF-Seiten, schnelles Dokumentwechseln, fehlerhafte Vorschau, großes Dokument, fehlender Archiv-PDF, Mobil-Rücknavigation, Hoch-/Querformat.

Abnahme: Ein Dashboard-Tab bietet benutzbare Suche, Treffer und Dokumentanzeige auf Desktop und Mobilgerät.

## 10. Durchgängige Test- und Prüfliste

| Bereich | Durchführung | Erwartetes Ergebnis |
| --- | --- | --- |
| Suche | Titelbegriff vs. ausschließlich im Inhalt vorkommender Begriff | Titelmodus und Inhaltsmodus liefern die jeweils richtigen Dokumente |
| OCR | Scan mit und ohne erkannten Text | Verhalten entspricht Paperless; fehlender Text wird verständlich erklärt |
| Pagination | 0, 1, 5, 6, 10, 11 Treffer; letzte Seite | Anzahl, Pfeile und Trefferbereich stimmen |
| Datenänderung | Dokument zwischen Suche und Abruf löschen/rechteentziehen | Kein Absturz; verständlicher Fehler; kein unzulässiger Zugriff |
| Anmeldung | Schlüssel widerrufen, ändern, erneut anmelden | Reauth und Wiederherstellung ohne Geheimnisleck |
| Berechtigung | HA-Nutzer wechseln, direkte IDs/URLs aufrufen | Backend setzt Zugriff auch außerhalb der Karten durch |
| Isolation | Zwei Benutzer, Karten und Integrationseinträge parallel | Keine Vermischung von Suche, Cache und Dokumenten |
| Netzwerk | Internes Paperless, extern erreichbares HA, verschiedene Browser-Adressen | HA-Vorschau funktioniert über Backend; externe Paperless-Links sind korrekt |
| Netzwerkfehler | Timeout, Abbruch, 429, 5xx | Begrenzte Wiederholungen, verständlicher Status, keine Anfragestürme |
| Darstellung | Chrome/Edge, Firefox, Safari; Android/iOS Companion | Anzeige funktioniert oder bietet getesteten Fallback |
| Layout | Schmaler Bildschirm, Tablet, Desktop; Seitenleiste; Panel/Sections | Kein abgeschnittener Inhalt; Liste, Pfeile und Vorschau bedienbar |
| Barrierefreiheit | Tastatur, Fokus nach Dialog, Screenreader, Kontrast | Alle Kernfunktionen ohne Maus nutzbar |
| Sicherheit | Script-Inhalt in Titeln, manipulierte IDs/URLs, Redirects | Keine Script-Ausführung, kein offener Proxy, keine Token-Weitergabe |
| Datenschutz | Browser-Netzwerk, Logs, Diagnose, Recorder, Cache | Kein Paperless-Schlüssel; keine unnötige Speicherung von Dokumentdaten |
| Leistung | Großes Archiv, große PDF, schnelles Blättern | Seitenweise Abfragen und begrenzter Speicher-/Requestverbrauch |
| Lebenszyklus | HA-Neustart, Reload, Entfernen und erneutes Einrichten | Kein verwaister Zugriff, keine doppelten Ressourcen/Handler |
| Updates | Frontend-/Backend-Version wechseln, alter Browser-Cache | Kompatible Schnittstellen oder verständlicher Aktualisierungshinweis |

- [ ] Backend-Unit- und Integrationstests für Authentifizierung, Rechte und HTTP-/WebSocket-Pfade schreiben.
- [x] Frontend-Komponententests für Suchrennen, Pagination, Auswahl, Thumbnailfehler und Editorvalidierung vorhanden (17 erfolgreich).
- [ ] Browser-End-to-End-Tests für beide Karten mit kontrollierten Testdaten einrichten.
- [ ] Manuelle Browser-/Companion-Tests mit Version, Datum und Ergebnis protokollieren.
- [ ] Leistungsbaseline mit Archivgröße, PDF-Größe, Antwortzeit, Requestanzahl und Speicherverbrauch erfassen; messbare Grenzwerte festlegen.
- [ ] Nicht verfügbare Testgeräte als offene Abdeckung ausweisen; nicht als bestanden markieren.

## 11. CI, Dokumentation und Auslieferung

- [ ] Python-Linting, relevante Typprüfung und Backend-Tests in CI einrichten.
- [ ] Frontend-Linting, Typprüfung, Komponententests und reproduzierbaren Produktionsbuild in CI einrichten.
- [x] HACS-Validator in CI integriert und für 1.0.1 sowie 1.0.2 bestanden; lokale Markenbilder nach aktuellen HA-Anforderungen eingebunden.
- [ ] Zusätzliche Hassfest-/Übersetzungsprüfung integrieren.
- [x] HACS liefert ausschließlich den Integrationsordner mit Backend, Karten, Übersetzungen und Icon aus; tatsächliche Installation zurückgelesen. Keine Zugangsdaten, privaten Dokumente oder Entwicklungsartefakte im Paket.
- [ ] README um Einrichtung, API-Schlüssel-Erstellung, Berechtigungen und beide Karten erweitern.
- [ ] Beispiele für kompakte Karte und große Karte in eigenem Dashboard-Tab bereitstellen.
- [ ] Interne/externe Adresse, Paperless-Anmeldung im neuen Tab, Zertifikate und Vorschau-Fallback erklären.
- [ ] Unterstützte Versionen, bekannte Einschränkungen und Fehlerdiagnose dokumentieren.
- [x] Testinstallation über File editor durchgeführt, Config Flow und automatisches Ressourcenupdate live geprüft. Anschließend Übernahme durch HACS sowie Update 1.0.1 → 1.0.2 erfolgreich geprüft. Frisch aufgesetzte HA-Instanz bleibt ungeprüft.
- [x] Einheitliche Manifest-/Release-Version, Changelog und HACS-Upgradeanleitung vorhanden; Releases werden erst nach erfolgreichen CI-Prüfungen veröffentlicht.
- [ ] Entfernungsanleitung ergänzen.
- [ ] Lizenzhinweise für alle mitgelieferten Bibliotheken beifügen.
- [ ] Vor Release vollständigen Kernablauf auf sauberer Installation durchführen und Ergebnis dokumentieren.

## 12. Meilensteine und Abschlusskriterien

1. **M0 – Recherche:** API-Vertrag, Berechtigungsmodell, PDF-Authentifizierung und Paketierung entschieden und belegt.
2. **M1 – Verbindung:** Integration über Oberfläche einrichtbar; Fehler, Reauth und Reload getestet.
3. **M2 – Backend:** Titel-/Inhaltsuche, Pagination und geschützter Dokumentzugriff mit Berechtigungstests.
4. **M3 – Kleine Karte:** Fünf Titel pro Seite, Pfeile und konfigurierbares Öffnen funktionsfähig.
5. **M4 – Große Karte:** Thumbnails, große Vorschau und mobile Ansicht funktionsfähig.
6. **M5 – Auslieferung:** CI grün, Testmatrix mit Ergebnissen, saubere Installation und Dokumentation geprüft.

Ein Meilenstein gilt erst als abgeschlossen, wenn seine Tests bestanden und Einschränkungen dokumentiert sind. Die erste nutzbare Version umfasst beide vereinbarten Karten.

## 13. Quellen und noch einzuholende Informationen

Bereits zur Orientierung herangezogen; konkrete Versionskompatibilität bleibt in R1–R4 nachzuweisen:

- Paperless REST API: https://docs.paperless-ngx.com/api/
- Paperless Bedienung und Suche: https://docs.paperless-ngx.com/usage/
- Paperless Konfiguration: https://docs.paperless-ngx.com/configuration/
- HA Entwicklerdokumentation: https://developers.home-assistant.io/
- HA Config Flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- HA WebSocket API: https://developers.home-assistant.io/docs/api/websocket/
- HA Custom Cards: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
- HA Panel-Ansicht: https://www.home-assistant.io/dashboards/panel/
- HACS Entwicklerdokumentation: https://www.hacs.xyz/docs/publish/

Vor den Live-Integrationstests aus einer autorisierten Testumgebung ermitteln:

- [x] Test-Home-Assistant vom Benutzer bereitgestellt; ha-test erreichbar, HA 2026.10.4 (31.10.2026).
- [x] Bereitgestellter Paperless-Testzugang funktioniert für lesende API-Aufrufe.
- [ ] Paperless-Anwendungsversion separat bestätigen; unterstützte Mindestversionen bleiben offen.
- [x] Paperless-Adresse vom Benutzer erhalten: http://192.168.178.10:8810; Anmeldeseite erreichbar. Externe Adresse/Unterpfad noch nicht benötigt bzw. ungeprüft.
- [ ] Eingeschränkter Testzugang und gewünschter Kreis berechtigter HA-Benutzer.
- [ ] Relevante Browser/Companion-Geräte und typische Dokumentformate/-größen.

Zugangsschlüssel ausschließlich über sichere Konfiguration bereitstellen; niemals in diese Datei, Fixtures oder das Repository schreiben.



## 14. Ganz zuletzt – optionale Mehrbenutzerfunktionen

Auf ausdrücklichen Nutzerwunsch nach allen übrigen Arbeitspaketen, nur falls benötigt:

- [ ] Freigabe einzelner Paperless-Verbindungen für ausgewählte normale HA-Benutzer.
- [ ] Persönlicher Paperless-API-Schlüssel je HA-Benutzer, damit dessen eigene Paperless-Dokumentrechte gelten.
- [ ] Bei Umsetzung: Benutzerzuordnung, sichere Schlüsselverwaltung und -entfernung, Isolation sowie Rechteentzug und Benutzerwechsel testen.

Kein eigener Modus „nur ansehen, nicht herunterladen“ geplant. Die PDF-Vorschau
überträgt die Datei bereits an den Browser; ein versteckter Download-Button würde
das Speichern nicht zuverlässig verhindern.


