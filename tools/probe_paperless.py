"""Read-only live probe. Report only test outcomes, never tokens or document data.

Usage: python tools/probe_paperless.py --url URL --key-file PATH
The key file must contain only the API token. No documents are modified.
"""

import argparse
import asyncio
import importlib
import json
import re
import sys
import types
from pathlib import Path

import aiohttp

package = types.ModuleType("_insights_probe")
package.__path__ = [
    str(Path(__file__).resolve().parents[1] / "custom_components" / "paperless_ngx_insights")
]
sys.modules[package.__name__] = package
api = importlib.import_module("_insights_probe.client")


async def probe(url: str, key_file: Path) -> dict:
    token = api.validate_token(await asyncio.to_thread(key_file.read_text, encoding="utf-8-sig"))
    report = {}
    async with aiohttp.ClientSession() as session:
        client = api.PaperlessClient(session, url, token)
        await client.validate_connection()
        report["connection"] = "passed"
        first = await client.search("", page_size=5)
        report["metadata_page"] = "passed"
        report["first_page_at_most_five"] = len(first.documents) <= 5
        if first.count > 5:
            second = await client.search("", page=2, page_size=5)
            report["pagination"] = (
                first.count == second.count
                and bool(second.documents)
                and not ({d.id for d in first.documents} & {d.id for d in second.documents})
            )
        else:
            report["pagination"] = "not_tested_insufficient_documents"
        absent = await client.search("insights-probe-no-match-5f789c77c6", page_size=5)
        report["no_match"] = absent.count == 0 and not absent.documents
        if first.documents:
            document = first.documents[0]
            if document.title.strip():
                for mode in ("title", "text"):
                    found = await client.search(document.title, mode=mode, page_size=5)
                    report[f"{mode}_search"] = document.id in {d.id for d in found.documents}
            detail = await client._get_json(f"documents/{document.id}/", {"fields": "id,content"})
            content = detail.get("content", "")
            word = next(
                (
                    w
                    for w in re.findall(r"[^\W\d_]{9,}", content)
                    if w.casefold() not in document.title.casefold()
                ),
                None,
            )
            if word:
                text = await client.search(word, mode="text", page_size=5)
                title = await client.search(word, mode="title", page_size=5)
                report["content_only_search"] = document.id in {
                    d.id for d in text.documents
                } and document.id not in {d.id for d in title.documents}
            else:
                report["content_only_search"] = "not_tested_no_suitable_word"
            for kind in ("preview", "thumb", "download"):
                async with session.get(
                    f"{client.base_url}/api/documents/{document.id}/{kind}/",
                    headers={"Authorization": f"Token {token}", "Range": "bytes=0-31"},
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    prefix = await response.content.read(32)
                    report[kind] = {
                        "status": response.status,
                        "content_type": response.content_type,
                        "nonempty": bool(prefix),
                        "pdf_signature": prefix.startswith(b"%PDF-"),
                        "range_supported": response.status == 206,
                    }
            candidates = await client._get_json(
                "documents/",
                {"page_size": "50", "fields": "id,original_file_name", "ordering": "-created,-id"},
            )
            pdf = next(
                (
                    d
                    for d in candidates.get("results", [])
                    if str(d.get("original_file_name", "")).lower().endswith(".pdf")
                ),
                None,
            )
            if pdf:
                async with session.get(
                    f"{client.base_url}/api/documents/{int(pdf['id'])}/preview/",
                    headers={"Authorization": f"Token {token}", "Range": "bytes=0-31"},
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    prefix = await response.content.read(32)
                    report["pdf_preview"] = {
                        "status": response.status,
                        "content_type": response.content_type,
                        "pdf_signature": prefix.startswith(b"%PDF-"),
                        "range_supported": response.status == 206,
                    }
            else:
                report["pdf_preview"] = "not_tested_no_pdf_in_latest_fifty"
        else:
            report["document_tests"] = "not_tested_empty_archive"
        client.close()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--key-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = asyncio.run(probe(args.url, args.key_file))
    except Exception as error:
        # Do not print exception chains: upstream errors may contain private URLs.
        print(json.dumps({"probe": "failed", "error_type": type(error).__name__}))
        sys.exit(1)
    print(json.dumps(result, indent=2))
    if any(value is False for value in result.values()):
        sys.exit(1)
