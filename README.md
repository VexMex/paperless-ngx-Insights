# Paperless-ngx Insights

Home-Assistant-Integration zum Suchen und Anzeigen von Paperless-ngx-Dokumenten.

**Entwicklungsstand 0.1.0-dev.3:** Backend und kompakte Suchkarte mit Mehrwortsuche sind implementiert:
Einrichtung über die Oberfläche, Verbindungstest, erneute Anmeldung,
Ändern der Verbindung, getrennte Browser-Adresse und eine administrativ
geschützte Suchschnittstelle mit serverseitiger Pagination.

Die kompakte Karte zeigt fünf Titel pro Seite, Pfeile zum Blättern und öffnet
Dokumente in einem neuen Paperless-Tab. Die große Dokumentkarte, Vorschaubilder
und eingebettete PDF-Anzeige sind noch in Entwicklung. Diese Version ist kein fertiges Release. Der aktuelle
Arbeits- und Teststand steht in [todo.md](todo.md).

## Entwicklung und Tests

- Ausschließlich **ha-test**, vom Eigentümer dem System **192.168.178.147**
  zugeordnet, für alle Live-HA-Tests verwenden. Keine Tests am produktiven HA.
- Aktuelles HA-Testziel: **2026.10.4**, Python **ab 3.14.2**. Andere HA-Versionen
  sind noch nicht bestätigt. Die portable HTTP-Client-Testsuite läuft auch auf
  Python 3.10; das bedeutet keine HA-Unterstützung auf Python 3.10.
- Paperless-Testadresse: **http://192.168.178.10:8810**. Die Anmeldeseite wurde
  erreicht. Erste authentifizierte Such-/Dateiprüfungen sind bestanden; siehe
  [Live-Testbericht](docs/live-tests.md). Die Integration und Suchkarte sind auf
  ha-test installiert und im Browser geprüft. Die separate Bestätigung der
  Paperless-Anwendungsversion bleibt offen.
- Zugriff auf die Suchschnittstelle haben zunächst nur HA-Administratoren.
  Der Paperless-Schlüssel bestimmt zusätzlich die Paperless-Dokumentrechte.
- API-Schlüssel werden ausschließlich im HA-Konfigurationseintrag gehalten.
  Keine Zugangsdaten in YAML-Karten, Repository oder Testdaten eintragen.

### Lokale Tests mit künstlichen Dokumentdaten

```sh
python -m venv .venv
# Die virtuelle Umgebung passend zum Betriebssystem aktivieren.
python -m pip install -r requirements-test.txt
ruff check .
ruff format --check .
python -m compileall -q custom_components
python -m pytest -q
npm ci --ignore-scripts --no-audit --no-fund
npm test
```

Die HTTP-Tests starten ausschließlich einen lokalen synthetischen Server; sie
greifen nicht auf einen Home Assistant oder ein reales Dokumentarchiv zu.

Die HA-Frameworktests benötigen Linux und Python ab 3.14.2:

```sh
python -m pip install -r requirements-ha-test.txt
python -m pytest -q ha_tests
```

Beide Testarten werden in GitHub Actions ausgeführt. CI ersetzt die noch offenen
Live-Tests auf ha-test nicht.

## Einrichtung der Entwicklungsversion auf ha-test

Nur für die Testinstanz: Den Ordner
`custom_components/paperless_ngx_insights` in das gleichnamige Unterverzeichnis
des HA-Konfigurationsverzeichnisses kopieren. Nach dem erforderlichen Neustart
unter **Einstellungen > Geräte & Dienste > Integration hinzufügen** nach
**Paperless-ngx Insights** suchen. Ein HACS-Installationsweg ist noch nicht
fertiggestellt.

Folgende Angaben werden abgefragt:

- **Paperless-Adresse:** vollständige Basisadresse inklusive optionalem Port
  oder Reverse-Proxy-Unterpfad. Ein reiner Hostname/IP wird als HTTP interpretiert.
- **API-Schlüssel:** Token eines Paperless-Benutzers mit Dokument-Leserechten.
- **Browser-Adresse:** optional vom Browser erreichbare Paperless-Basisadresse;
  für spätere Dokumentlinks vorgesehen und noch nicht von Karten verwendet.

TLS-Zertifikate werden geprüft. Eine Abschaltoption ist bewusst nicht vorhanden.
Bei einer falschen Adresse oder unzureichenden Rechten bleibt der Dialog offen.
Ein Server kann einmal pro normalisierter Basisadresse eingerichtet werden.

Auf ha-test wurde dieser Entwicklungsstand am 31.10.2026 über den regulären
Dateieditor-Zugang installiert, HA neu gestartet und die Integration über ihren
Config Flow eingerichtet. HACS auf ha-test konnte das private Repository nicht
lesen; der Testinstallationsweg ändert keine Repository-Sichtbarkeit und keine
Netzbeschränkungen des Dateieditors.

## Kompakte Karte

Dashboard-Ressource als **JavaScript-Modul** registrieren:

```text
/paperless_ngx_insights/frontend/paperless-ngx-insights.js?v=0.1.0-dev.3
```

Danach die Karte hinzufügen:

```yaml
type: custom:paperless-ngx-insights-search
title: Dokumente suchen
page_size: 5
search_mode: title
```

Bei genau einem geladenen Integrationseintrag wird dieser automatisch gewählt.
Bei mehreren Servern zusätzlich dessen `entry_id` setzen. `search_mode` ist
`title` oder `text`; der Suchbereich kann auch direkt in der Karte gewählt werden.
Dokumentlinks öffnen die normale Paperless-Oberfläche in einem neuen Tab. Dafür
kann zusätzlich eine Paperless-Anmeldung erforderlich sein. Eine eingebettete
Vorschau oder ein visueller Karteneditor ist in diesem Stand noch nicht vorhanden.

Das eingerichtete Test-Dashboard ist unter
[Paperless auf ha-test](http://192.168.178.147/paperless-test/suche) erreichbar und
auf HA-Administratoren beschränkt.

## Suchschnittstelle für die folgenden Karten

Authentifizierte HA-WebSocket-Befehle, jeweils nur für Administratoren:

```json
{"id":1,"type":"paperless_ngx_insights/entries"}
```

```json
{"id":2,"type":"paperless_ngx_insights/search","entry_id":"ENTRY_ID","text":"Rechnung","mode":"title","page":1,"page_size":5}
```

`mode` ist `title` (Titel) oder `text` (Titel und Inhalt). Die Antwort enthält
`count`, `page`, `page_size` und `documents` mit `id`, `title`, `created`.
Pro Seite sind 1–50 Dokumente erlaubt. Mehrere Begriffe werden mit UND
verknüpft: `telekom rechnung mai` findet Dokumente mit allen drei
Begriffen unabhängig von der Reihenfolge. Im Titelmodus müssen alle Begriffe im
Titel stehen; im Inhaltsmodus dürfen sie über Titel und Dokumenttext verteilt
sein. Eine Wortfolge in doppelten Anführungszeichen bleibt zusammen. Einzelne
Begriffe finden weiterhin auch Wortteile. Keine benutzerdefinierte erweiterte
Suchsyntax. Leere Suche listet erreichbare Dokumente nach Erstellungsdatum und ID
absteigend. Details und Nachweise: [Mehrwortsuche](docs/multiword-search.md).

Keine vollständigen Dokumenttexte oder Geheimnisse werden zurückgegeben.
Es gibt keinen Dokumentcache und keine Entitäten mit Dokumentdaten im Recorder.
Ein entladener Eintrag kann nicht weiter abgefragt werden.

## Entfernung

Den Integrationseintrag über die HA-Oberfläche entfernen. Für vollständige
Deinstallation anschließend ausschließlich auf dem Testsystem den zugehörigen
Custom-Component-Ordner entfernen. Noch vorhandene Browser-Verbindungen erhalten
keinen weiteren Zugriff über den entfernten Eintrag.

## Lizenz

Das Repository enthält die GNU GPL Version 3; siehe [LICENSE](LICENSE).
Es wird keine Viewer-Bibliothek mitgeliefert. Lizenzprüfungen für zukünftige
Frontend-Abhängigkeiten bleiben Teil des Entwicklungsplans.
