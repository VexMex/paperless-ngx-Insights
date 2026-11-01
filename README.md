# Paperless-ngx Insights

Mit Paperless-ngx Insights kannst du dein Dokumentenarchiv direkt in Home Assistant durchsuchen und Dokumente ansehen. So findest du zum Beispiel Rechnungen oder Briefe, ohne zuerst die Paperless-Oberfläche öffnen zu müssen.

## Funktionen

- **Dokumentensuche:** Suche im Titel oder in Titel und Inhalt. Mehrere Suchwörter werden gemeinsam berücksichtigt.
- **Kompakte Suchkarte:** Eine einfache Trefferliste mit fünf Dokumenten pro Seite und Pfeilen zum Blättern.
- **Große Dokumentübersicht:** Treffer mit Vorschaubildern und Datum sowie eine Dokumentansicht für einen ganzen Dashboard-Tab.
- **Vorschau und Downloads:** PDFs in Home Assistant ansehen, PDF oder Originaldatei herunterladen oder das Dokument in Paperless öffnen.
- **Visueller Editor:** Beide Karten lassen sich über die Oberfläche einstellen.

Die Integration liest Dokumente aus Paperless. Sie verändert oder löscht keine Dokumente.

## Installation

Du benötigst Home Assistant, eine erreichbare Paperless-ngx-Instanz und einen Paperless-API-Schlüssel mit Leserechten für die gewünschten Dokumente.

Die Installation erfolgt momentan manuell:

1. [Repository als ZIP herunterladen](https://github.com/VexMex/paperless-ngx-Insights/archive/refs/heads/main.zip) und entpacken.
2. Den enthaltenen Ordner `custom_components/paperless_ngx_insights` in das Verzeichnis `custom_components` deiner Home-Assistant-Konfiguration kopieren. Das Ziel ist normalerweise `/config/custom_components/paperless_ngx_insights/`.
3. Home Assistant neu starten.
4. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Paperless-ngx Insights** suchen.
5. Deine Paperless-Adresse und den API-Schlüssel eintragen. Die optionale **Browser-Adresse** benötigst du nur, wenn du Paperless im Browser über eine andere Adresse öffnest.

## Karten zum Dashboard hinzufügen

Nach der Einrichtung das Dashboard neu laden und über **Dashboard bearbeiten → Karte hinzufügen** eine der beiden Karten auswählen:

- **Paperless-ngx Insights · Suche** für die kompakte Trefferliste.
- **Paperless-ngx Insights · Dokumentübersicht** für die große Ansicht mit Vorschaubildern.

Für einen ganzen Tab eine Ansicht vom Typ **Panel** mit der Dokumentübersicht als einziger Karte verwenden. In den Karteneinstellungen kannst du unter anderem Überschrift, Suchbereich und Trefferzahl anpassen. Die Karten-Ressource wird bei über die Oberfläche verwalteten Dashboards automatisch eingerichtet.

## Hinweise

- Aktuell können nur **Home-Assistant-Administratoren** auf die Dokumente zugreifen.
- Die PDF-Vorschau ist auf **20 MiB** begrenzt. Größere PDFs können heruntergeladen werden.
- Falls dein Browser PDFs nicht direkt anzeigt, steht eine Bildvorschau der ersten Seite zur Verfügung.
- Der API-Schlüssel bleibt in der Integration und gehört nicht in die Kartenkonfiguration.

## Updates

Den Integrationsordner durch die neue Version ersetzen, Home Assistant neu starten und das Dashboard neu laden.

## Lizenz

[GNU General Public License v3](LICENSE).
