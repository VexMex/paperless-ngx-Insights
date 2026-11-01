# Einrichtung und Updates – 0.1.0-dev.6

Die Integration richtet ihre gemeinsame Karten-Ressource in HA-Storage-Dashboards
automatisch ein und aktualisiert den Versionsparameter anhand der Manifestversion.
Die existierende Ressourcen-ID wird erhalten. Nur relative URLs mit exakt dem
eigenen Modulpfad gehören zur Integration; andere Module bleiben unverändert.
Mehrere Verbindungen teilen sich eine Ressource. Neuladen entfernt sie nicht,
Entfernen der letzten Verbindung entfernt sie über die HA-Ressourcensammlung.
Keine Bearbeitung interner `.storage`-Dateien. YAML-Ressourcen bleiben manuell.

Ein Update besteht weiterhin aus dem Austausch der Integrationsdateien und einem
HA-Neustart (HACS-Paketierung folgt später). Anschließend Dashboard neu laden.
Eine laufende Browserseite behält ihr bereits geladenes Modul bis zum Neuladen;
die neue URL sorgt dann für die richtige Version. Ein Rollback auf eine ältere
Manifestversion aktualisiert dieselbe Ressourcen-ID entsprechend zurück.

„Verbindung ändern“ erlaubt das Anpassen der API-/Browser-Adresse. Ein leerer oder
weggelassener Schlüssel behält den vorhandenen Wert. Ein neuer Schlüssel wird wie
bei der Einrichtung geprüft; ungültige Eingaben verändern die funktionierende
Verbindung nicht. Bestehende Schlüssel werden nie in Formulare vorgefüllt.
Bei abgelehntem Schlüssel startet die Integration den HA-Reauth-Flow. Dort ist
ein gültiger Schlüssel erforderlich. Verschiedene normalisierte API-Adressen
werden als getrennte Verbindungen verwaltet; Duplikate werden abgewiesen.

Die Erweiterungen werden mit HA 2026.10.4 geprüft. Ressourcenverwaltung nutzt die
[HA-Lovelace-Ressourcensammlung](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/lovelace/resources.py).
Neue automatisierte Prüfungen ergänzen die vorhandenen Flow-/Lifecycle-Tests.
Tatsächlich bestandene CI- und Live-Prüfungen werden in todo.md ergänzt.
