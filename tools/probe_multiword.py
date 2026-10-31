"""Read-only live regression probe. Never output document titles or OCR text."""

import argparse
import asyncio
import importlib
import json
import re
import sys
import types
from pathlib import Path

import aiohttp

package = types.ModuleType("_multiword_probe")
package.__path__ = [
    str(Path(__file__).resolve().parents[1] / "custom_components" / "paperless_ngx_insights")
]
sys.modules[package.__name__] = package
api = importlib.import_module("_multiword_probe.client")


async def probe(key_file: Path) -> dict:
    token = await asyncio.to_thread(key_file.read_text, encoding="utf-8-sig")
    async with aiohttp.ClientSession() as session:
        client = api.PaperlessClient(session, "http://192.168.178.10:8810", token)
        results = await client.search("telekom rechnung mai", mode="text")
        reverse = await client.search("mai rechnung telekom", mode="text")
        upper = await client.search("TELEKOM RECHNUNG MAI", mode="text")
        phrase = await client.search('"telekom rechnung mai"', mode="text")
        report = {
            "example_matches": results.count,
            "example_nonempty": results.count > 0,
            "order_independent": results == reverse,
            "case_independent": results == upper,
            "phrase_is_narrower": phrase.count < results.count,
        }
        all_terms = True
        candidate = None
        for doc in results.documents:
            detail = await client._get_json(f"documents/{doc.id}/", {"fields": "id,title,content"})
            title = str(detail.get("title", "")).casefold()
            content = str(detail.get("content", "")).casefold()
            terms = ("telekom", "rechnung", "mai")
            all_terms &= all(term in title or term in content for term in terms)
            if candidate is None:
                words = sorted(set(re.findall(r"[^\W\d_]{12,}", content)), key=len, reverse=True)
                candidate = (doc.id, [word for word in words if word not in title][:3])
        report["all_terms_in_each_returned_document"] = all_terms
        report["content_extends_title_search"] = "not_tested_no_suitable_content_term"
        if candidate:
            target, words = candidate
            for word in words:
                both = await client.search("telekom " + word, mode="text", page_size=50)
                only_title = await client.search("telekom " + word, mode="title", page_size=50)
                if target in {d.id for d in both.documents}:
                    report["content_extends_title_search"] = target not in {
                        d.id for d in only_title.documents
                    }
                    break
        titles = await client.search("telekom rechnung", mode="title")
        report["title_scope"] = bool(titles.documents) and all(
            all(term in doc.title.casefold() for term in ("telekom", "rechnung"))
            for doc in titles.documents
        )
        first = await client.search("telekom rechnung", mode="text", page_size=5)
        second = await client.search("telekom rechnung", mode="text", page=2, page_size=5)
        report["pagination"] = (
            first.count == second.count
            and len(first.documents) == len(second.documents) == 5
            and not ({d.id for d in first.documents} & {d.id for d in second.documents})
        )
        absent = await client.search("telekom insightsnomatch5f789c77c6", mode="text")
        report["missing_word_excludes_document"] = absent.count == 0 and not absent.documents
        for mode in ("title", "text"):
            literal = await client.search("telekom", mode=mode)
            report[f"single_word_{mode}"] = literal.count > 0
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = asyncio.run(probe(args.key_file))
    except Exception as error:
        print(json.dumps({"probe": "failed", "error_type": type(error).__name__}))
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))
    if any(value is False for value in result.values()):
        raise SystemExit(1)
