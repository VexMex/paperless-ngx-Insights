# Entwicklungsplan: paperless-ngx-Insights

Stand: 31.10.2026
Repository: https://github.com/VexMex/paperless-ngx-Insights
Ziel: Home-Assistant-Integration für die Suche und Anzeige von Paperless-ngx-Dokumenten.

## Aktueller Entwicklungsstand – 31.10.2026

**0.1.0-dev.2: Backend und erste kompakte Suchkarte auf ha-test eingerichtet.**

- [x] Integrationsdateien und Suchkarten-Modul auf **192.168.178.147** übertragen und vollständig zurückgelesen/per Hash geprüft.
- [x] HA-Konfiguration geprüft, ausschließlich ha-test neu gestartet und Paperless über den regulären Config Flow eingerichtet.
- [x] Integration meldet **loaded**. Der bereitgestellte Schlüssel ist im HA-Konfigurationseintrag hinterlegt, nicht im Repository.
- [x] Dashboard **Paperless** mit Ansicht **Suche** und versionierter JavaScript-Ressource angelegt: [Test-Dashboard](http://192.168.178.147/paperless-test/suche).
- [x] Im Browser geprüft: Karte lädt, fünf Titel pro Seite, Weiterblättern auf Treffer 6–10, neue Titelsuche setzt Seite auf 1 zurück, Auswahl Titel/Inhalt und Links für neue Tabs vorhanden.
- [x] Neue kompakte Karte mit sicherer Textausgabe, getrenntem Suchzustand, Lade-/Fehlerzuständen und Verwerfen veralteter Antworten implementiert.
- [x] Lokale Tests: **52 Client-Tests**, **6 Frontend-Tests**, Ruff, Format- und Kompilierungsprüfung bestanden.
- [x] Dashboard-Ausbaustufe in GitHub Actions vollständig erfolgreich geprüft: [Lauf](https://github.com/VexMex/paperless-ngx-Insights/actions/runs/41198510108).
- [ ] Abschließenden Lauf nach der kleinen Korrektur für Suchmoduswechsel während laufender Anfrage und Wiederverbinden bestätigen.
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
- [ ] Adresse und Schlüssel nachträglich ändern können; erneute Anmeldung bei ungültigem Schlüssel anbieten.
- [ ] Optional getrennte interne API-Adresse und vom Browser erreichbare Paperless-Adresse unterstützen.
- [ ] Mehrere Integrationseinträge architektonisch berücksichtigen; Karten wählen den gewünschten Eintrag.

### Karte A: kompakte Suche

- [x] Eigenständiger Kartentyp mit Suchfeld und Auswahl Titel / Titel und Inhalt.
- [x] Standardmäßig fünf Titel pro Ergebnisseite, Anzahl pro Karte einstellbar.
- [x] Vor-/Zurück-Pfeile, korrekt deaktivierte Randpfeile und verständliche Trefferanzeige.
- [ ] Dokumenttitel anklickbar; Verhalten pro Karte auswählbar: Vorschau in Home Assistant oder Öffnen in Paperless.
- [x] Ladezustand, keine Treffer, noch keine Suche und Fehler jeweils eindeutig darstellen.
- [x] Im Normalbetrieb keine Vorschaubilder laden; die Karte soll kompakt bleiben.

### Karte B: Dokumentübersicht für einen ganzen Dashboard-Tab

- [ ] Separater Kartentyp mit gemeinsamer Suchlogik, Trefferliste und Vorschaubildern.
- [ ] Große Dokumentvorschau nach Auswahl.
- [ ] Desktop: Treffer und Vorschau nebeneinander; Mobil: sinnvoll zwischen Liste und Dokument wechseln.
- [ ] Als einzelne große Karte in einer Panel-Ansicht und in regulären Dashboard-Layouts verwendbar.
- [ ] Buttons für Öffnen in Paperless und Download, soweit für das jeweilige Dokument verfügbar.
- [ ] Seitennavigation und Seitengröße unabhängig von der kompakten Karte konfigurierbar.

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

- [ ] Festlegen, welche HA-Benutzer welchen Integrationseintrag benutzen dürfen; serverseitige Prüfung pro Anfrage.
- [ ] Gemeinsamer Paperless-Schlüssel bedeutet gemeinsame Paperless-Rechte: Auswirkungen dokumentieren.
- [ ] Dashboard-Sichtbarkeit ausdrücklich nicht als Zugriffsprüfung verwenden.
- [ ] Verhalten für HA-Administrator, normalen Benutzer, nicht freigeschalteten Benutzer und abgemeldeten Browser definieren.
- [ ] Nachweisen, dass auch direkte Dokument-ID-Aufrufe, Thumbnails, Vorschau und Download dieselben Rechte prüfen.
- [ ] Paperless-seitige Dokumentrechte mit eingeschränktem Testbenutzer prüfen.
- [x] Entscheidung für die erste Ausbaustufe: nur HA-Administratoren. Benutzerfreigaben werden vor einer späteren Erweiterung gesondert umgesetzt.

### R3: Dokumentanzeige und Authentifizierung

- [ ] Aktuelle HA-Schnittstellen für eigene WebSocket-Befehle und geschützte HTTP-Antworten prüfen.
- [ ] PDF-Anzeige als authentifizierter Abruf mit Blob-URL gegen eingebauten PDF-Viewer / PDF.js abwägen.
- [ ] Prüfen, wie PDF-Viewer und neue Tabs authentifiziert laden: ein iframe oder neuer Tab sendet nicht automatisch den HA-Bearer-Header.
- [ ] Falls kurzlebige signierte Links nötig sind: Ablauf, Rechtebindung, Cache-Verhalten und Widerruf untersuchen.
- [ ] Große PDFs, Byte-Range-Anfragen, Speicherverbrauch und Streaming je gewähltem Anzeigeweg prüfen.
- [ ] PDF-Anzeige in Chrome/Edge, Firefox, Safari und Companion-WebViews praktisch testen.
- [ ] Für nicht darstellbare Formate und fehlende Vorschau einen Download-/Öffnen-Fallback definieren.
- [ ] Unterschied zwischen neuem Tab zur Paperless-Weboberfläche mit deren Anmeldung und geschützter Dokumentvorschau aus HA dokumentieren.

### R4: Installation und Frontend

- [ ] Aktuelle HA-Konventionen für Config Flow, Reauth/Reconfigure, Lifecycle und statische Ressourcen prüfen.
- [ ] Gemeinsames Repository für Integration und zwei Karten auf HACS-Kompatibilität untersuchen; nicht zwei Repository-Kategorien ungeprüft voraussetzen.
- [ ] Entscheiden, ob gebaute Karten mit der Integration ausgeliefert und versioniert als Ressource registriert werden.
- [ ] Ressourcenentfernung, Updates, Browser-Cache und parallele Integrationseinträge berücksichtigen.
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
- [ ] Reauth/Reconfigure und sichere Aktualisierung bestehender Einstellungen ergänzen.
- [ ] Doppelte Einträge erkennen; mehrere verschiedene Paperless-Server eindeutig verwalten.
- [ ] Setup, Unload, Reload und Entfernen sauber implementieren; laufende Aufgaben und Sitzungen aufräumen.
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
- [ ] Dokumentmetadaten und geschützte Endpunkte für Thumbnail, Vorschau und Download implementieren.
- [ ] Zugriff in jeder Anfrage anhand des HA-Benutzers und des Integrationseintrags prüfen.
- [ ] Upstream-URLs aus vertrauenswürdiger Basis und validierter Dokument-ID bilden; keinen beliebigen URL-Proxy anbieten.
- [ ] Weiterleitungen und Pagination-Links prüfen, damit API-Schlüssel nicht an fremde Hosts weitergereicht werden.
- [ ] MIME-Typ, Dateiname und Content-Disposition korrekt behandeln; HTML nicht ungeprüft unter der HA-Origin ausführen.
- [ ] Caches nur begrenzt und getrennt nach Integration/Zugriffskontext verwenden; bei Schlüsselwechsel und Unload leeren.
- [ ] Fehlerbehandlung für 404, 429, 5xx, abgebrochene Downloads und verweigerte Dokumentrechte ergänzen.

Tests: Sonderzeichen, Umlaute, Leerzeichen, lange Suche, ungültige IDs, fremder Eintrag, nicht autorisierter Benutzer, manipulierte URLs, Seitenränder und alle Fehlerpfade.

Abnahme: Suche und Dokumentabruf funktionieren ohne Browserzugriff auf den internen Paperless-Server; keine Geheimnisse verlassen das Backend.

## 7. Gemeinsame Frontend-Bausteine

Abhängigkeit: Backend-Schnittstellen.

- [ ] Gemeinsamen Client und typisierte Antwort-/Fehlermodelle für beide Karten anlegen.
- [ ] Suchzustand je Karteninstanz isolieren; Suchtext und Auswahl nicht global speichern.
- [ ] Suche per Enter/Suchbutton umsetzen; optionale Eingabeverzögerung nur mit klarer Anfragebegrenzung.
- [x] Bei neuer Suche Seite auf 1 zurücksetzen und veraltete Antworten verwerfen.
- [ ] Suchwechsel, schnelles Blättern und Verbindungsabbruch ohne vertauschte Ergebnisse behandeln.
- [ ] Wiederverwendbare Seitennavigation, Statusanzeige und Vorschaukomponente erstellen.
- [ ] HA-Themes, Tastaturbedienung, Fokus, Beschriftungen und Screenreader berücksichtigen.
- [ ] Sichere Textausgabe statt ungeprüftem HTML aus Dokumenttiteln oder Suchtreffern.
- [ ] Blob-URLs, Eventhandler und laufende Anfragen beim Wechsel/Entfernen aufräumen.

Tests: verspätete Antwort überschreibt keine neue Suche; zwei Karten beeinflussen sich nicht; Sonderzeichen werden als Text dargestellt; kein wiederholter Request bei jedem HA-Zustandsupdate.

## 8. Kompakte Suchkarte entwickeln

Abhängigkeit: gemeinsame Frontend-Bausteine.

- [ ] Kartentyp, Kartenauswahl-Eintrag und visuelle Konfiguration bereitstellen.
- [ ] Optionen: Integrationseintrag, Überschrift, Suchmodus, Treffer pro Seite (Standard 5), Klickverhalten.
- [ ] Titelzeilen ohne dauerhaft geladene Thumbnails umsetzen; lange Titel zugänglich darstellen.
- [x] Vor-/Zurück-Pfeile und Trefferbereich korrekt berechnen.
- [ ] Vorschau-Dialog und Öffnen der Paperless-Ansicht per Nutzerklick anbinden.
- [x] Konfigurationsfehler und entfernten Integrationseintrag verständlich anzeigen.

Tests: 0/1/5/6/10/11 Treffer, erste/letzte Seite, neue Suche von späterer Seite, gelöschtes Dokument, Dialog schließen, Pop-up-Verhalten, Touch und Tastatur.

Abnahme: Bei 6 Treffern zeigt die Karte zunächst 5 Titel, dann 1 Titel; Navigation und beide Klickoptionen funktionieren.

## 9. Große Dokumentkarte entwickeln

Abhängigkeit: gemeinsame Komponenten und erprobter Vorschauweg.

- [ ] Eigener Kartentyp mit visuellem Editor und gemeinsamem Konfigurationsmodell.
- [ ] Treffer mit Titel, Datum und bedarfsgeladenen Vorschaubildern anzeigen.
- [ ] Desktop-Aufteilung und mobile Navigation zwischen Liste/Vorschau implementieren.
- [ ] Höhe, Scrollbereiche und Größenangaben für Panel- und Sections-Ansichten sauber umsetzen.
- [ ] PDF-Seitenanzeige/Zoom entsprechend der gewählten Viewer-Lösung bereitstellen.
- [ ] Öffnen in Paperless, Download und Fallback für nicht darstellbare Dokumente anbinden.
- [ ] Auswahl beim Such-/Seitenwechsel eindeutig zurücksetzen; keine alte Vorschau unter neuem Titel anzeigen.
- [ ] Fehler einzelner Thumbnails dürfen die übrige Trefferliste nicht blockieren.

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
- [ ] Frontend-Komponententests für Suchrennen, Pagination, Auswahl und Fehlerzustände schreiben.
- [ ] Browser-End-to-End-Tests für beide Karten mit kontrollierten Testdaten einrichten.
- [ ] Manuelle Browser-/Companion-Tests mit Version, Datum und Ergebnis protokollieren.
- [ ] Leistungsbaseline mit Archivgröße, PDF-Größe, Antwortzeit, Requestanzahl und Speicherverbrauch erfassen; messbare Grenzwerte festlegen.
- [ ] Nicht verfügbare Testgeräte als offene Abdeckung ausweisen; nicht als bestanden markieren.

## 11. CI, Dokumentation und Auslieferung

- [ ] Python-Linting, relevante Typprüfung und Backend-Tests in CI einrichten.
- [ ] Frontend-Linting, Typprüfung, Komponententests und reproduzierbaren Produktionsbuild in CI einrichten.
- [ ] Manifest-/Übersetzungsprüfung sowie aktuelle Hassfest-/HACS-Anforderungen prüfen und passend integrieren.
- [ ] Nur veröffentlichbare Dateien paketieren; keine Zugangsdaten, privaten Dokumente oder Entwicklungsartefakte ausliefern.
- [ ] README um Einrichtung, API-Schlüssel-Erstellung, Berechtigungen und beide Karten erweitern.
- [ ] Beispiele für kompakte Karte und große Karte in eigenem Dashboard-Tab bereitstellen.
- [ ] Interne/externe Adresse, Paperless-Anmeldung im neuen Tab, Zertifikate und Vorschau-Fallback erklären.
- [ ] Unterstützte Versionen, bekannte Einschränkungen und Fehlerdiagnose dokumentieren.
- [ ] Installationsweg und Ressourcenregistrierung aus R4 praktisch auf frischem HA testen.
- [ ] Versionsnummer, Changelog, Upgrade-/Entfernungsanleitung und Release-Artefakte vorbereiten.
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

