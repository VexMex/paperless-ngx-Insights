# Paperless-ngx Insights

<img src="https://raw.githubusercontent.com/VexMex/paperless-ngx-Insights/main/custom_components/paperless_ngx_insights/brand/icon.png" width="96" alt="Paperless-ngx Insights icon">

Search your Paperless-ngx document archive and view documents directly in Home Assistant. Find invoices, letters and other documents without opening the Paperless interface first.

## Features

- **Document search:** Search titles, or titles and content. Multiple search terms are matched together.
- **Compact search card:** A simple list with five results per page and arrows for browsing.
- **Document overview card:** Thumbnails, document dates and an integrated preview, suitable for a dedicated dashboard tab.
- **Previews and downloads:** View PDFs in Home Assistant, download the PDF or original file, or open the document in Paperless.
- **Visual card editor:** Configure both cards through the interface.
- **English and German:** Cards and their editor follow your Home Assistant interface language automatically. Other languages use English. Setup dialogs are also available in English and German. Custom headings and document titles keep their original text.

The integration reads documents from Paperless. It does not modify or delete them.

## Installation

You need **Home Assistant 2026.10.4 or newer**, a reachable Paperless-ngx server and a Paperless API token with permission to read the documents you want to access.

### Install from the Marketplace catalog

On **Home Assistant 2026.11 or newer**, the built-in Marketplace replaces HACS.

1. Open **Settings → Marketplace** and search for **Paperless-ngx Insights**.
2. Open the listing, select **Install**, review the version and confirm.
3. Follow the setup prompt. If Home Assistant asks you to restart, restart first and then complete setup as described below.

Paperless-ngx Insights is listed in the catalog. Catalog installs do not require a GitHub account or a repository URL. Existing HACS installations are migrated automatically when you upgrade to Home Assistant 2026.11 or newer. On Home Assistant 2026.10.4, you can still install the integration through HACS 2.0.5 or newer.

### Add the repository by link

If you need to add the repository manually, use **Settings → Marketplace → Add from link**.

1. If prompted, connect your GitHub account.
2. Enter `https://github.com/VexMex/paperless-ngx-Insights` in **GitHub link** and select **Add**.
3. If the Marketplace asks for a **Type**, choose **Integration** and select **Add** again.
4. Open the repository listing and select **Install**. If the Marketplace says it is already listed, open the catalog listing to install it.

See the [Home Assistant Marketplace documentation](https://www.home-assistant.io/integrations/marketplace/#custom-repositories) for details.

### Set up Paperless-ngx Insights

If the setup dialog did not open after installation, go to **Settings → Devices & services → Add integration** and search for **Paperless-ngx Insights**. Enter your Paperless server address and API token. Set the optional **Browser address** if your browser uses a different address to open Paperless.

Both dashboard cards and the icon are included. You do not need a separate card repository.

### Install from a ZIP

Download the source ZIP for the [latest release](https://github.com/VexMex/paperless-ngx-Insights/releases/latest), extract it and copy `custom_components/paperless_ngx_insights` to `/config/custom_components/paperless_ngx_insights/`. Restart Home Assistant, then add the integration as described above.

## Adding cards to your dashboard

After setup, reload your dashboard and select **Edit dashboard → Add card**. Choose:

- **Paperless-ngx Insights · Search** for the compact results list.
- **Paperless-ngx Insights · Document overview** for the larger view with thumbnails.

If searching for `paperless` does not show the cards immediately after setup, close the card picker and fully reload the Home Assistant browser page with **Ctrl+F5** (or **Cmd+Shift+R** on macOS). Then open the card picker again. In the Companion app, use **Reset frontend cache** if reloading does not help.

For a dedicated dashboard tab, use a **Panel** view with the document overview as its only card. The visual editor lets you adjust the heading, search scope, results per page and other options. The card resource is registered automatically for dashboards managed through the Home Assistant interface.

## Notes

- By default, only **Home Assistant administrators** can access documents. To share a connection, open **Settings → Devices & services → Paperless-ngx Insights → Configure → Document access** and select additional users. An empty list limits access to administrators.
- Shared users can search, preview and download every document the configured Paperless account can read. Change that account's permissions in Paperless to restrict the available documents. Changing the Paperless address or API token clears the sharing list.
- PDF previews are limited to **20 MiB**. Larger PDFs can be downloaded.
- If your browser cannot display a PDF directly, you can show the first page as an image.
- The API token stays in the integration configuration. Do not put it in the card configuration.
- Change the interface language in your **Home Assistant profile**. No language setting is needed in the cards.

## Updates

Marketplace updates appear under **Settings → Updates**. Install the update, restart Home Assistant to apply it and reload your dashboard. On older installations managed by HACS, update through HACS. For installations from a ZIP, replace the integration folder with the new version.

## License

[GNU General Public License v3](LICENSE).

