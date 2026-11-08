# Änderungen

## 1.1.4

- Share a Paperless connection with selected Home Assistant users under **Settings → Devices & services → Paperless-ngx Insights → Configure → Document access**. The list is empty by default, so existing connections remain accessible to administrators only.
- Selected users can search, preview and download documents that the connection's Paperless account can read. Permissions apply separately to each connection and are checked on the server, including for direct document requests.
- Removing a user's access takes effect immediately, including for previously issued download links. Changing the Paperless server address or API token clears the sharing list.

## 1.1.3

- Run the full HACS validation, including the repository topics check.
- Require a successful Hassfest run before publishing a release.

## 1.1.2

- Give the Paperless link the same compact 44-pixel toolbar size as the download buttons.
- Use a PDF-specific icon to distinguish the PDF download from the original-file download.

## 1.1.1

- Compact document preview on phones: full-screen dialog, two-line heading and a single row of accessible icon actions.
- Hide routine preview explanations on narrow screens while keeping loading, download feedback and errors visible.
- Move the first-page image action into the toolbar and hide it once the image is displayed; restore it for the next document.
- Apply the compact toolbar to narrow embedded previews in the document overview card as well.

## 1.1.0

- Cards and the visual editor automatically follow the Home Assistant interface language: English and German, with English fallback for other languages.
- Search, pagination, preview/download messages, accessibility labels and default headings are translated. Custom headings and document titles are preserved.
- Language changes update existing controls without restarting searches or discarding an open preview.
- README and new release descriptions are now in English, including the documentation displayed in HACS.

## 1.0.2

- README-Icon mit vollständiger Bildadresse verlinkt, damit es auch innerhalb von HACS angezeigt wird.
- Installation von 1.0.1 über HACS erfolgreich geprüft; 1.0.2 dient zusätzlich der Prüfung des HACS-Updatewegs.

## 1.0.1

- Installation und Updates über HACS als benutzerdefiniertes Integrations-Repository vorbereitet.
- Eigenes Dokument-/Lupen-Icon für Home Assistant ergänzt.
- Manifestversion und neues Release einheitlich auf 1.0.1 gesetzt.
- README um HACS-Installation ergänzt; beide Karten sind weiterhin im selben Paket enthalten.

Die vorhandenen Funktionen bleiben erhalten: Titel-/Inhaltssuche, kompakte und große
Dashboard-Karte, visueller Editor, geschützte Vorschau bis 20 MiB und gestreamte
PDF-/Original-Downloads. Der vorhandene Release-Tag V1.0 bleibt unverändert.
