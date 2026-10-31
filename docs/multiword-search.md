# Mehrwortsuche – Entwicklungsstand 0.1.0-dev.3

## Verhalten

- `telekom rechnung mai`: Alle Begriffe müssen im selben Dokument vorkommen;
  ihre Reihenfolge ist beliebig. Groß-/Kleinschreibung spielt keine Rolle.
- **Nur Titel:** Jeder Begriff wird ausschließlich im Dokumenttitel gesucht.
- **Titel und Inhalt:** Jeder Begriff darf im Titel oder Dokumenttext vorkommen.
- `"telekom rechnung mai"`: Zusammenhängende Wortfolge wie in der bisherigen
  Teilstringsuche suchen.
- `telekom "rechnung mai"`: Ein Begriff und eine zusammenhängende Wortfolge.
- Einzelne Begriffe behalten die Teilwortsuche. Mehrere Begriffe nutzen den
  Paperless-Wortindex; Wortformen können entsprechend dessen Spracheinstellungen
  verarbeitet werden. Eine Mehrwortsuche ist keine beliebige Teilwortsuche.
- Anführungszeichen müssen geschlossen sein. Maximal 32 Begriffe, insgesamt
  weiterhin höchstens 500 Zeichen. Leere Suche listet Dokumente wie bisher.

Die Karte erklärt die Mehrwortsuche direkt unter der Suchbereich-Auswahl.

## Umsetzung

Einzelne Begriffe/Wortfolgen werden weiterhin über `title__icontains` bzw.
`title_content` gesucht. Bei mehreren Begriffen erzeugt der Client eine
explizite UND-Abfrage, je nach Suchbereich beispielsweise:

```text
title:"telekom" AND title:"rechnung" AND title:"mai"

(title:"telekom" OR content:"telekom") AND
(title:"rechnung" OR content:"rechnung") AND
(title:"mai" OR content:"mai")
```

Eingaben werden als Werte maskiert; Benutzer können keine eigenen Felder oder
booleschen Operatoren einschleusen. Einzelne Satzzeichen wie `&` zwischen
Begriffen werden ausgelassen. Apostrophe und Umlaute bleiben erhalten.
Trefferzahl, Sortierung und Pagination stammen vollständig von Paperless;
es gibt keine nachträgliche Filterung einer bereits geladenen Ergebnisseite.

Siehe [Paperless-Suchdokumentation](https://docs.paperless-ngx.com/usage/#document-searches).
Die gewählte Syntax wurde zusätzlich direkt auf der vorgesehenen Instanz geprüft.

## Live-Nachweise am 31.10.2026

- Mit bereitgestelltem Schlüssel gegen Paperless geprüft: Das Beispiel
  `telekom rechnung mai` liefert **vier Treffer**.
- Umgekehrte Wortreihenfolge und Großbuchstaben liefern dieselben Ergebnisse.
- Die angezeigten Dokumente enthalten alle drei Begriffe. Exakte Wortfolge
  grenzt stärker ein; ein zusätzlicher fehlender Begriff schließt Treffer aus.
- Separat einen Titelbegriff mit einem nur im Dokumenttext vorhandenen Begriff
  kombiniert und die Trennung der Suchbereiche geprüft.
- Titelsuche, Einzelwortsuche und Pagination mit fünf Treffern geprüft.
- Bestehenden allgemeinen API-Probelauf inklusive Text-, Bild- und PDF-Endpunkten
  erneut erfolgreich ausgeführt.
- Dateien auf **ha-test / 192.168.178.147** übertragen und zurückgelesen geprüft;
  Konfiguration validiert und ausschließlich das Testsystem neu gestartet.
- Über die echte HA-WebSocket-Schnittstelle unter dem autorisierten Testbenutzer
  Mehrwortsuche, Wortreihenfolge, Wortfolge, beide Suchbereiche und Blättern
  erfolgreich geprüft. Aktualisiertes Frontend wird vom Testsystem ausgeliefert.
- Browser-Neuprüfung automatisiert nicht verfügbar: Die vorhandene Verbindung
  meldet `browser.user is unavailable`. Es wird daher keine erneute visuelle
  Prüfung dieser Änderung behauptet; Interaktionstests laufen mit synthetischen
  Daten in der DOM-Testumgebung.
- Keine privaten Dokumenttitel, Inhalte, Dateinamen oder IDs in diesem Bericht.

## Wiederholung

```sh
python tools/probe_multiword.py --key-file /path/to/local-token.txt
```

Das Werkzeug liest ausschließlich Dokumentdaten, verarbeitet sie im Arbeitsspeicher
und gibt nur Prüfergebnisse aus. Es verändert keine Dokumente.
