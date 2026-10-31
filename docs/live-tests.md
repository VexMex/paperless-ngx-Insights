# Live-Prüfung am 31.10.2026

## Umgebung und Umfang

- Paperless-Adresse: http://192.168.178.10:8810
- HA-Testverbindung: ausschließlich MCP-Server `ha-test`; HA 2026.10.4 / RUNNING.
- Der bereitgestellte API-Schlüssel wurde lokal aus einer Datei gelesen, nicht
  ausgegeben, nicht in das Repository kopiert und nicht in Test-Fixtures eingebaut.
- Alle Paperless-Aufrufe waren lesende GET-Anfragen. Keine Dokumente wurden
  angelegt, geändert oder gelöscht. Private Titel, Inhalte und Dateinamen wurden
  nur im Arbeitsspeicher verarbeitet; dieser Bericht enthält keine solchen Daten.
- Dieser Abschnitt beschreibt die erste API-Prüfung mit dem Integrationsclient
  außerhalb von HA. Der nachfolgende Installations-/Browsertest ist unten separat
  dokumentiert.

## Bestandene Prüfungen

| Prüfung | Ergebnis |
| --- | --- |
| Verbindung mit bereitgestelltem Schlüssel | Dokumentlisten-Endpunkt erreichbar |
| Metadaten laden | Integrationsclient verarbeitet die Antwort |
| Fünf Treffer pro Seite | Seitengröße eingehalten |
| Zweite Seite | Treffer vorhanden, disjunkte IDs, gleiche Gesamttrefferzahl |
| Titelsuche | Ausgewähltes Dokument über seinen Titel gefunden |
| Suche in Titel und Inhalt | Ausgewähltes Dokument gefunden |
| Reine Inhaltsübereinstimmung | Begriff aus OCR-/Dokumenttext findet das Dokument im Inhaltsmodus, nicht im Titelmodus |
| Suche ohne Treffer | Leere Ergebnisse und Trefferzahl null |
| Textdatei: Vorschau und Download | HTTP 200, text/plain, nicht leer |
| Vorschaubild | HTTP 200, image/webp, nicht leer |
| PDF-Vorschau eines weiteren Dokuments | HTTP 200, application/pdf, PDF-Signatur bestätigt |

Die Dateiprüfungen lasen jeweils nur einen kurzen Datenanfang und speicherten
keine Dokumentdateien. Der PDF-Kandidat wurde aus höchstens 50 aktuellen
Dokument-Metadatensätzen gewählt.

## Beobachtungen und offene Prüfungen

- Auf `Range: bytes=0-31` antworteten die geprüften Datei-Endpunkte mit HTTP 200
  statt 206. Teilbereichsübertragung darf für diesen Server nicht vorausgesetzt
  werden; das ist für die spätere Anzeige großer PDFs zu berücksichtigen.
- Ein Dokument ist nicht zwangsläufig ein PDF. Die Karten benötigen eine
  Formatprüfung und eine Darstellung bzw. einen Öffnen-/Download-Fallback.
- Benutzer-/Dokumentrechte mit eingeschränktem Schlüssel, widerrufene Schlüssel,
  Fehlersimulationen sowie gezielte 0/1/5/6/10/11-Treffer-Testarchive bleiben offen.
- Reload/Reauth, geschützte Dokumentauslieferung und weitere Browser dort prüfen.
- Keine Tests am produktiven Home Assistant durchgeführt.

## Wiederholung

Mit einer aktivierten Entwicklungsumgebung:

```sh
python tools/probe_paperless.py --url http://192.168.178.10:8810 --key-file /path/to/local-token.txt
```

Die Schlüsseldatei muss ausschließlich den API-Schlüssel enthalten. Das Werkzeug
gibt nur Prüfergebnisse und Formatinformationen aus, keine Dokumentdaten.

## Installation und Dashboard auf ha-test

- Version 0.1.0-dev.2 samt kompakter Karte direkt auf **192.168.178.147** installiert.
- HACS konnte das private Repository nicht lesen (GitHub 404). Stattdessen wurde
  die offizielle App **File editor 6.3.0** installiert und der reguläre,
  angemeldete Ingress-Zugang verwendet. Die Netzwerkbeschränkung blieb unverändert.
- Integrationsdateien nach Übertragung vollständig zurückgelesen und per Hash
  mit den lokalen Quellen verglichen. HA-Konfigurationsprüfung erfolgreich.
- Ausschließlich ha-test neu gestartet; Config Flow mit dem bereitgestellten
  Paperless-Schlüssel erfolgreich abgeschlossen. Integration meldet **loaded**.
- JavaScript-Modul registriert und eigenes Admin-Dashboard **Paperless** mit
  Ansicht **Suche** über die offiziellen Dashboard-APIs angelegt.
- Im Browser geprüft: Karte lädt, Suche liefert fünf Titel, Vor-/Zurück-Pfeile
  funktionieren, nächste Seite zeigt Treffer 6–10, neue Titelsuche startet auf
  Seite eins. Auswahl des Inhaltsmodus und Linkziel neuer Tab geprüft.
- Die Prüfergebnisse enthalten keine privaten Dokumenttitel, Inhalte oder IDs.
- Lokale Regressionstests: **52 Client-Tests** und **5 Frontend-Tests bestanden**.
- Der normale Paperless-Tab kann eine separate Anmeldung verlangen. PDF-Vorschau
  innerhalb von HA, große Dokumentkarte und visueller Editor bleiben offen.
