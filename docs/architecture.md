# Erste Architekturentscheidungen und offene Nachweise

Stand: 31.10.2026. Dieses Dokument beschreibt die erste Backend-Ausbaustufe.

## Implementierte Entscheidungen

1. Domain: `paperless_ngx_insights`. Ein HA-Konfigurationseintrag je normalisierter
   Paperless-Basisadresse, mehrere verschiedene Server möglich.
2. HTTP-Sitzung aus HA injizieren. Der Client schließt die gemeinsame Sitzung
   nicht. Entladen entfernt den Zugriff und sperrt neue Clientanfragen.
3. UI-Einrichtung und erneute Anmeldung mit einem geheimen Schlüsselfeld.
   Die Integration verwendet die auf HA 2026.10.4 geprüften API-Quellreferenzen
   einschließlich `probatio`. Ältere HA-Versionen sind kein bestätigtes Testziel.
4. Zunächst nur Administratorzugriff. Die Prüfung findet an jedem
   WebSocket-Einstiegspunkt statt, unabhängig von Dashboard-Sichtbarkeit.
   Noch keine Freigaben für normale Benutzer. Die Paperless-Rechte des
   gemeinsamen Schlüssels werden dadurch nicht pro HA-Benutzer unterschieden.
5. Suche auf Anforderung, keine periodische Archiv-Synchronisation. Antworten
   werden auf Metadaten reduziert und nicht als Entitätszustände gespeichert.
6. Titelsuche über `title__icontains`, Titel/Inhalt über `title_content`.
   Das ist eine bewusste Kompatibilitätsentscheidung für wörtliche Teilstrings.
   Paperless 3.x behält `title_content` im aktuellen Quellcode als veralteten
   Parameter bei. Vor einer zugesicherten Versionsunterstützung muss das
   Schema des tatsächlich betriebenen Servers geprüft werden. Unbekannte
   Parameter werden nicht durch einen ungeprüften automatischen Fallback ersetzt.
7. Sortierung `-created,-id`; stabile Reihenfolge bei gleichen Datumswerten.
   Änderungen am Archiv zwischen zwei Seitenabfragen können trotzdem Treffer
   verschieben. Die erste Version bietet keine Snapshot-Suche.
8. HTTP-Weiterleitungen und Upstream-Pagination-URLs werden nie verfolgt.
   Pro Anfrage 15 Sekunden Gesamt- und 5 Sekunden Verbindungszeitlimit,
   maximal vier parallele Anfragen je Eintrag, maximal 1 MiB JSON-Antwort.
   Fehlermeldungen enthalten keine fremden Antworttexte oder Header.
9. Keine API-Versionsnummer ohne Prüfung des Zielservers fest vorgeben.
   Die initiale Verbindung prüft bisher das Dokumentlisten-Schema; eine echte
   Kompatibilitäts-/Versionsprüfung bleibt offen.

## Offen vor Dokumentanzeige und Karten

- Tatsächliche Paperless-Version, API-Version und Rechte eines Testtokens.
- Server mit mehreren HA-Benutzern und späterem Freigabemodell praktisch prüfen.
- Authentifizierte PDF-Auslieferung prototypisch auf ha-test belegen: eingebettete
  Viewer und neue Tabs übernehmen keinen beliebigen Bearer-Header automatisch.
- Dateiformate, Archiv-PDF/Original, Range-Requests und Streaming untersuchen.
- HACS-Paketierung und versionierte Bereitstellung beider Karten entscheiden.
- Frontend-Framework und mögliche PDF-Bibliothek einschließlich Lizenzen wählen.

## Beobachtung am vorgesehenen Paperless-Server

Am 31.10.2026 war das OpenAPI-Schema unter
`http://192.168.178.10:8810/api/schema/?format=json` lesbar (HTTP 200).
Es meldet `info.version: 6.0.0 (10)`. Das ist zunächst die vom Schema gemeldete
Versionsangabe; eine separate Bestätigung der installierten Anwendung bleibt offen.

Das Dokumentlisten-Schema führt `title__icontains`, `title_content`, `text`,
`title_search`, `query`, `ordering`, `fields`, `page` und `page_size` auf.
Auch die Pfade für `preview`, `thumb` und `download` sind vorhanden.
Der Dokumentlisten-Aufruf ohne Token antwortet mit HTTP 401.
Die Filterparameter sind damit im Ziel-Schema nachgewiesen, ihr Verhalten mit
echten Dokumenten und Rechten jedoch noch nicht getestet. Es wurden keine
Dokumente abgerufen und keine Anmeldung vorgenommen.

Das PDF-Authentifizierungs-Gate aus todo.md bleibt vor der eingebetteten
Dokumentvorschau bestehen. Die kompakte Karte in 0.1.0-dev.2 verwendet zunächst
normale Paperless-Links für neue Tabs. Das Modul liegt im Integrationsordner
unter www/ und wird über einen eigenen statischen HA-Pfad ausgeliefert. Die
Karte ruft ausschließlich HA-WebSocket-Befehle auf und erhält keinen API-Schlüssel.
M0 und M1 sind durch die erste Testinstallation noch nicht insgesamt abgeschlossen.

## Quellen zur API-Prüfung

- [Paperless REST API](https://docs.paperless-ngx.com/api/)
- [Paperless Filterimplementierung](https://github.com/paperless-ngx/paperless-ngx/blob/main/src/documents/filters.py)
- [HA Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [HA 2026.10.4 Config Entries](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/config_entries.py)
- [HA 2026.10.4 WebSocket-Dekoratoren](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/websocket_api/decorators.py)
- [HA 2026.10.4 Konfigurationsmuster](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/mealie/config_flow.py)

Die Referenzimplementierung wurde nur zur Prüfung der HA-Schnittstellen gelesen;
es wurden keine Bibliotheks-/Viewer-Quelltexte in dieses Projekt übernommen.
