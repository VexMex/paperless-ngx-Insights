# Live-Prüfung am 31.10.2026

## Umgebung und Umfang

- Paperless-Adresse: http://192.168.178.10:8810
- HA-Testverbindung: ausschließlich MCP-Server `ha-test`; HA 2026.10.4 / RUNNING.
- Der bereitgestellte API-Schlüssel wurde lokal aus einer Datei gelesen, nicht
  ausgegeben, nicht in das Repository kopiert und nicht in Test-Fixtures eingebaut.
- Alle Paperless-Aufrufe waren lesende GET-Anfragen. Keine Dokumente wurden
  angelegt, geändert oder gelöscht. Private Titel, Inhalte und Dateinamen wurden
  nur im Arbeitsspeicher verarbeitet; dieser Bericht enthält keine solchen Daten.
- Verwendet wurde der echte Integrationsclient außerhalb von HA. Dies ist kein
  Nachweis einer Installation oder eines erfolgreichen Karten-/Browser-Tests.

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
- Integration auf ha-test installieren und konfigurieren; HA-WebSocket-Suche,
  Reload/Reauth, geschützte Dokumentauslieferung und Browseranzeige dort prüfen.
- Keine Tests am produktiven Home Assistant durchgeführt.

## Wiederholung

Mit einer aktivierten Entwicklungsumgebung:

```sh
python tools/probe_paperless.py --url http://192.168.178.10:8810 --key-file /path/to/local-token.txt
```

Die Schlüsseldatei muss ausschließlich den API-Schlüssel enthalten. Das Werkzeug
gibt nur Prüfergebnisse und Formatinformationen aus, keine Dokumentdaten.
