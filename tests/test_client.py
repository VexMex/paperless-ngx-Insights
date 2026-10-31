"""Exercise the real HTTP client against a local synthetic Paperless server.

Load the client under an isolated package name so these portable tests don't
import Home Assistant's platform-specific integration entry point.
"""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path

import aiohttp
import pytest
import pytest_asyncio
from aiohttp import web

package = types.ModuleType("_insights_client")
package.__path__ = [
    str(Path(__file__).resolve().parents[1] / "custom_components" / "paperless_ngx_insights")
]
sys.modules[package.__name__] = package
api = importlib.import_module("_insights_client.client")


@pytest_asyncio.fixture
async def server(unused_tcp_port):
    """Use real request parsing, encoding, response limits, and context cleanup."""
    state = {"status": 200, "body": {"count": 0, "results": []}, "requests": [], "delay": 0}

    async def handler(request):
        state["requests"].append(request)
        await asyncio.sleep(state["delay"])
        if "raw" in state:
            return web.Response(
                status=state["status"],
                body=state["raw"],
                content_type=state.get("type", "text/html"),
            )
        return web.json_response(state["body"], status=state["status"])

    app = web.Application()
    app.router.add_get("/{tail:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", unused_tcp_port).start()
    async with aiohttp.ClientSession() as session:
        state["client"] = api.PaperlessClient(
            session, f"http://127.0.0.1:{unused_tcp_port}/paperless", "fixture-token"
        )
        state["session"] = session
        yield state
    await runner.cleanup()


async def test_pdf_preview_fixed_path_and_auth(server):
    server.update(raw=b"%PDF-1.7\nsynthetic fixture", type="application/pdf")
    assert (await server["client"].preview(42)).startswith(b"%PDF-")
    request = server["requests"][-1]
    assert request.path == "/paperless/api/documents/42/preview/"
    assert request.headers["Authorization"] == "Token fixture-token"
    assert not request.query


@pytest.mark.parametrize("number", [True, 0, -1, 2147483648, "../1", "1", None])
async def test_preview_invalid_ids_never_request(server, number):
    with pytest.raises(ValueError):
        await server["client"].preview(number)
    assert not server["requests"]


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, api.InvalidAuth),
        (403, api.Forbidden),
        (404, api.PreviewUnavailable),
        (302, api.PreviewUnavailable),
        (429, api.RateLimited),
        (500, api.CannotConnect),
    ],
)
async def test_preview_safe_status_errors(server, status, error):
    server.update(status=status, raw=b"private upstream details", type="text/html")
    with pytest.raises(error) as caught:
        await server["client"].preview(1)
    assert "private" not in str(caught.value)
    assert len(server["requests"]) == 1


@pytest.mark.parametrize(
    ("body", "mime"),
    [
        (b"<script>alert(1)</script>", "application/pdf"),
        (b"%PDF-1.7", "text/html"),
        (b"", "application/pdf"),
    ],
)
async def test_preview_rejects_non_pdf(server, body, mime):
    server.update(raw=body, type=mime)
    with pytest.raises(api.PreviewUnavailable):
        await server["client"].preview(1)


async def test_preview_size_limit_and_unload(server, monkeypatch):
    monkeypatch.setattr(api, "MAX_PREVIEW_BYTES", 10)
    server.update(raw=b"%PDF-1.7" + b"x" * 100, type="application/pdf")
    with pytest.raises(api.PreviewTooLarge):
        await server["client"].preview(1)
    server["client"].close()
    with pytest.raises(api.CannotConnect):
        await server["client"].preview(1)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("192.168.178.10:8810", "http://192.168.178.10:8810"),
        (" HTTPS://EXAMPLE.COM/paperless/ ", "https://example.com/paperless"),
        ("http://[::1]:8810/", "http://[::1]:8810"),
    ],
)
def test_normalize_url(value, expected):
    assert api.normalize_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "ftp://host",
        "http://",
        "http://user:secret@host",
        "http://host?token=secret",
        "http://host/#fragment",
        "http://host:70000",
        "http://host:0",
        "http://bad host",
        "http://host\n/path",
        "http://host\\path",
    ],
)
def test_invalid_addresses(value):
    with pytest.raises(api.InvalidAddress):
        api.normalize_url(value)


@pytest.mark.parametrize("token", ["", " ", "abc\r\nInjected: value", "a b", "ümlaut", "a\x7fb"])
def test_invalid_tokens(token):
    with pytest.raises(api.InvalidAuth):
        api.validate_token(token)


async def test_search_params_and_metadata_only(server):
    server["body"] = {
        "count": 6,
        "results": [
            {
                "id": 12,
                "title": "Rechnung <script>",
                "created": "2026-10-31",
                "content": "private OCR",
                "token": "never-forward",
            }
        ],
        "next": "http://attacker.invalid/steal-token",
    }
    result = await server["client"].search(' "Öl & Gas" ', mode="text", page=2)
    request = server["requests"][0]
    assert request.path == "/paperless/api/documents/"
    assert dict(request.query) == {
        "page": "2",
        "page_size": "5",
        "ordering": "-created,-id",
        "fields": "id,title,created",
        "title_content": "Öl & Gas",
    }
    assert request.headers["Authorization"] == "Token fixture-token"
    assert result.count == 6
    assert result.page == 2
    assert result.documents[0].title == "Rechnung <script>"
    assert "private OCR" not in json.dumps(result.as_dict())
    assert "never-forward" not in json.dumps(result.as_dict())
    assert len(server["requests"]) == 1  # Never follow upstream pagination links.


async def test_title_search_is_literal(server):
    await server["client"].search("invoice:A*", mode="title")
    assert server["requests"][0].query["title__icontains"] == "invoice:A*"
    assert "query" not in server["requests"][0].query


@pytest.mark.parametrize("mode", ["title", "text"])
async def test_multiword_uses_scoped_and_query(server, mode):
    await server["client"].search("telekom rechnung mai", mode=mode, page=2)
    query = server["requests"][0].query
    if mode == "title":
        assert query["query"] == 'title:"telekom" AND title:"rechnung" AND title:"mai"'
    else:
        assert query["query"] == (
            '(title:"telekom" OR content:"telekom") AND '
            '(title:"rechnung" OR content:"rechnung") AND '
            '(title:"mai" OR content:"mai")'
        )
    assert query["page"] == "2"
    assert query["page_size"] == "5"
    assert query["ordering"] == "-created,-id"
    assert "title_content" not in query


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('telekom "rechnung mai"', 'title:"telekom" AND title:"rechnung mai"'),
        ("Öl & Gas", 'title:"Öl" AND title:"Gas"'),
        ("Telekom\tRechnung\nMai", 'title:"Telekom" AND title:"Rechnung" AND title:"Mai"'),
        ("Telekom Telekom Rechnung", 'title:"Telekom" AND title:"Rechnung"'),
        ("O'Reilly Rechnung", 'title:"O\'Reilly" AND title:"Rechnung"'),
        ("a OR content:b", 'title:"a" AND title:"OR" AND title:"content:b"'),
        (r"file\name invoice", r'title:"file\\name" AND title:"invoice"'),
    ],
)
def test_multiword_quotes_punctuation_and_scope(text, expected):
    assert api.search_parameters(text, "title") == {"query": expected}


@pytest.mark.parametrize("text", ['telekom "rechnung', " ".join(f"term{i}" for i in range(33))])
async def test_invalid_multiword_never_requests(server, text):
    with pytest.raises(ValueError):
        await server["client"].search(text)
    assert not server["requests"]


async def test_phrase_keeps_literal_substring_behavior(server):
    await server["client"].search('"telekom rechnung mai"', mode="text")
    assert server["requests"][0].query["title_content"] == "telekom rechnung mai"


async def test_validate_requests_only_one_document(server):
    await server["client"].validate_connection()
    assert server["requests"][0].query["page_size"] == "1"
    assert "title__icontains" not in server["requests"][0].query


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, api.InvalidAuth),
        (403, api.Forbidden),
        (429, api.RateLimited),
        (500, api.CannotConnect),
        (503, api.CannotConnect),
        (302, api.InvalidResponse),
        (404, api.InvalidResponse),
        (406, api.InvalidResponse),
    ],
)
async def test_safe_status_errors(server, status, error):
    server.update(status=status, body={"error": "private upstream response fixture-token"})
    with pytest.raises(error) as exc:
        await server["client"].validate_connection()
    assert "fixture-token" not in str(exc.value)
    assert "private" not in str(exc.value)


@pytest.mark.parametrize(
    "body",
    [
        [],
        {},
        {"count": -1, "results": []},
        {"count": True, "results": []},
        {"count": 0, "results": None},
        {"count": 0, "results": [{"id": 1, "title": "A"}]},
        {"count": 1, "results": [{"id": True, "title": "A"}]},
        {"count": 1, "results": [{"id": 1, "title": None}]},
        {"count": 1, "results": [{"id": 1, "title": "A", "created": []}]},
    ],
)
async def test_invalid_document_lists(server, body):
    server["body"] = body
    with pytest.raises(api.InvalidResponse):
        await server["client"].search("")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"page": 0},
        {"page": True},
        {"page_size": 51},
        {"page_size": False},
        {"page_size": 0},
        {"mode": "advanced"},
    ],
)
async def test_invalid_input_never_makes_request(server, kwargs):
    with pytest.raises(ValueError):
        await server["client"].search("x", **kwargs)
    assert not server["requests"]


async def test_long_search_rejected(server):
    with pytest.raises(ValueError):
        await server["client"].search("x" * 501)
    assert not server["requests"]


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        (b"<html>login</html>", "text/html"),
        (b"not-json", "application/json"),
        (b"x" * (api.MAX_RESPONSE_BYTES + 1), "application/json"),
    ],
)
async def test_invalid_and_oversized_response(server, body, content_type):
    server.update(raw=body, type=content_type)
    with pytest.raises(api.InvalidResponse):
        await server["client"].validate_connection()


async def test_close_prevents_new_requests_but_keeps_shared_session(server):
    server["client"].close()
    assert not server["session"].closed
    with pytest.raises(api.CannotConnect):
        await server["client"].search("x")
    assert not server["requests"]


async def test_unreachable_server(unused_tcp_port):
    async with aiohttp.ClientSession() as session:
        client = api.PaperlessClient(session, f"http://127.0.0.1:{unused_tcp_port}", "token")
        with pytest.raises(api.CannotConnect):
            await client.validate_connection()
