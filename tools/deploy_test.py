"""Install this component on the explicitly authorized test HA only.

Uses the normal authenticated HA and File editor ingress APIs. Never edits HA
internal storage. Password is read from HA_TEST_PASSWORD, not a source file.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import aiohttp

BASE = "http://192.168.178.147"
DOMAIN = "paperless_ngx_insights"
PROJECT = Path(__file__).resolve().parents[1]
LAST_STAGE = {"value": "login"}


async def run(action: str, key_file: Path | None) -> None:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:

        async def post_json(path, data, headers=None):
            LAST_STAGE["value"] = "authenticated_request" if headers else "login"
            async with session.post(BASE + path, json=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

        flow = await post_json(
            "/auth/login_flow",
            {
                "client_id": BASE + "/",
                "handler": ["homeassistant", None],
                "redirect_uri": BASE + "/?auth_callback=1",
            },
        )
        result = await post_json(
            "/auth/login_flow/" + flow["flow_id"],
            {
                "client_id": BASE + "/",
                "username": "shakran-test",
                "password": os.environ["HA_TEST_PASSWORD"],
            },
        )
        if result.get("type") != "create_entry":
            raise RuntimeError("Test HA login failed")
        async with session.post(
            BASE + "/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": result["result"],
                "client_id": BASE + "/",
            },
        ) as response:
            auth = await response.json()
        try:
            headers = {"Authorization": "Bearer " + auth["access_token"]}
            if action == "configure":
                if key_file is None:
                    raise ValueError("Key file required")
                token = await asyncio.to_thread(key_file.read_text, encoding="utf-8-sig")
                flow = await post_json(
                    "/api/config/config_entries/flow", {"handler": DOMAIN}, headers
                )
                if flow.get("type") != "form":
                    raise RuntimeError("Integration configuration form unavailable")
                result = await post_json(
                    "/api/config/config_entries/flow/" + flow["flow_id"],
                    {
                        "url": "http://192.168.178.10:8810",
                        "token": token.strip(),
                        "web_url": "http://192.168.178.10:8810",
                    },
                    headers,
                )
                print(
                    json.dumps(
                        {
                            "flow_type": result.get("type"),
                            "errors": result.get("errors"),
                            "entry_id": result.get("result", {}).get("entry_id"),
                        }
                    )
                )
                if result.get("type") != "create_entry":
                    raise RuntimeError("Integration configuration did not complete")
                return

            async with session.ws_connect(BASE + "/api/websocket") as ws:
                await ws.receive_json()
                await ws.send_json({"type": "auth", "access_token": auth["access_token"]})
                if (await ws.receive_json())["type"] != "auth_ok":
                    raise RuntimeError("Test HA websocket login failed")
                seq = 0

                async def command(command_type, allow_error=False, **data):
                    nonlocal seq
                    seq += 1
                    LAST_STAGE["value"] = command_type
                    await ws.send_json({"id": seq, "type": command_type, **data})
                    answer = await ws.receive_json()
                    if not answer.get("success"):
                        if allow_error:
                            return {"error": answer.get("error", {})}
                        raise RuntimeError(
                            "Test HA command failed: "
                            + str(answer.get("error", {}).get("code", "unknown"))
                        )
                    return answer["result"]

                user = await command("auth/current_user")
                if not user.get("is_admin"):
                    raise RuntimeError("Test user must be an administrator")
                if action == "verify_lifecycle":
                    entries = await command(DOMAIN + "/entries")
                    if len(entries) != 1 or key_file is None:
                        raise RuntimeError("One test entry and key file required")
                    entry_id = entries[0]["entry_id"]
                    token = (
                        await asyncio.to_thread(key_file.read_text, encoding="utf-8-sig")
                    ).strip()
                    base_url = "http://192.168.178.10:8810"

                    async def search():
                        for _ in range(40):
                            result = await command(
                                DOMAIN + "/search",
                                entry_id=entry_id,
                                text="",
                                page_size=1,
                                allow_error=True,
                            )
                            if "error" not in result:
                                return result
                            if result["error"].get("code") != "not_loaded":
                                raise RuntimeError("Lifecycle search failed")
                            await asyncio.sleep(0.25)
                        raise RuntimeError("Reload did not finish")

                    async def reconfigure(values):
                        flow = await post_json(
                            "/api/config/config_entries/flow",
                            {"handler": DOMAIN, "entry_id": entry_id},
                            headers,
                        )
                        if token in json.dumps(flow):
                            raise RuntimeError("Secret exposed in configuration form")
                        return await post_json(
                            "/api/config/config_entries/flow/" + flow["flow_id"], values, headers
                        )

                    initial = await search()
                    original_web = initial["web_url"]
                    checks = {}
                    try:
                        invalid = await reconfigure(
                            {
                                "url": base_url,
                                "web_url": original_web,
                                "token": "invalid-test-fixture",
                            }
                        )
                        checks["invalid_token_rejected"] = (
                            invalid.get("errors", {}).get("base") == "invalid_auth"
                        )
                        if invalid.get("flow_id"):
                            async with session.delete(
                                BASE + "/api/config/config_entries/flow/" + invalid["flow_id"],
                                headers=headers,
                            ) as response:
                                response.raise_for_status()
                        checks["old_connection_preserved"] = (await search())[
                            "web_url"
                        ] == original_web
                        changed = await reconfigure(
                            {
                                "url": base_url,
                                "web_url": base_url + "/temporary-link-check",
                                "token": "",
                            }
                        )
                        checks["blank_token_kept"] = changed.get("type") == "abort" and (
                            await search()
                        )["web_url"].endswith("/temporary-link-check")
                    finally:
                        restored = await reconfigure(
                            {"url": base_url, "web_url": original_web, "token": token}
                        )
                        if restored.get("type") != "abort":
                            raise RuntimeError("Test connection restoration failed")
                    checks["valid_token_renewal"] = (await search())["web_url"] == original_web
                    await post_json(
                        f"/api/config/config_entries/entry/{entry_id}/reload", {}, headers
                    )
                    checks["reload_search"] = (await search())["count"] == initial["count"]
                    resources = await command("lovelace/resources")
                    owned = [
                        r
                        for r in resources
                        if r["url"].split("?")[0] == f"/{DOMAIN}/frontend/paperless-ngx-insights.js"
                    ]
                    version = json.loads(
                        (PROJECT / "custom_components" / DOMAIN / "manifest.json").read_text()
                    )["version"]
                    checks["one_current_resource"] = len(owned) == 1 and owned[0]["url"].endswith(
                        "?v=" + version
                    )
                    print(json.dumps({"test_ha": BASE, "checks": checks}))
                    if not all(checks.values()):
                        raise RuntimeError("Lifecycle checks failed")
                    return
                if action == "verify_download":
                    entries = await command(DOMAIN + "/entries")
                    entry_id = entries[0]["entry_id"]
                    found = await command(
                        DOMAIN + "/search", entry_id=entry_id, text="", page_size=1
                    )
                    document_id = found["documents"][0]["id"]
                    checks = {}
                    for kind in ("pdf", "original"):
                        result = await command(
                            DOMAIN + "/download",
                            entry_id=entry_id,
                            document_id=document_id,
                            kind=kind,
                        )
                        # Signed links and file names are deliberately never printed.
                        size = 0
                        async with session.get(BASE + result["url"]) as response:
                            checks[kind + "_attachment"] = (
                                response.status == 200
                                and response.headers.get("Content-Disposition", "").startswith(
                                    "attachment;"
                                )
                            )
                            checks[kind + "_no_store"] = (
                                response.headers.get("Cache-Control") == "no-store, private"
                            )
                            async for chunk in response.content.iter_chunked(65536):
                                size += len(chunk)
                        checks[kind + "_nonempty"] = size > 0
                        async with session.get(BASE + result["url"].split("?")[0]) as response:
                            checks[kind + "_unsigned_rejected"] = response.status == 401
                    print(json.dumps({"test_ha": BASE, "checks": checks}))
                    if not all(checks.values()):
                        raise RuntimeError("Download checks failed")
                    return
                if action == "verify_preview":
                    entries = await command(DOMAIN + "/entries")
                    if len(entries) != 1:
                        raise RuntimeError("Expected one test entry")
                    entry_id = entries[0]["entry_id"]
                    found = await command(
                        DOMAIN + "/search",
                        entry_id=entry_id,
                        text="",
                        mode="title",
                        page=1,
                        page_size=50,
                    )
                    checks = {}
                    for document in found["documents"]:
                        path = f"/api/{DOMAIN}/{entry_id}/documents/{document['id']}/preview"
                        async with session.get(BASE + path, headers=headers) as response:
                            if response.status == 415:
                                continue
                            data = await response.read()
                            checks["authenticated_pdf"] = (
                                response.status == 200 and data.startswith(b"%PDF-")
                            )
                            checks["no_store"] = (
                                response.headers.get("Cache-Control") == "no-store, private"
                            )
                            checks["pdf_only"] = response.content_type == "application/pdf"
                        async with session.get(BASE + path) as response:
                            checks["anonymous_rejected"] = response.status == 401
                        async with session.get(
                            BASE + path.replace("/preview", "/thumbnail"), headers=headers
                        ) as response:
                            checks["protected_thumbnail"] = (
                                response.status == 200
                                and response.content_type
                                in {"image/webp", "image/png", "image/jpeg"}
                            )
                        async with session.get(
                            BASE + path.replace("/preview", "/thumbnail")
                        ) as response:
                            checks["anonymous_thumbnail_rejected"] = response.status == 401
                        break
                    async with session.get(
                        BASE + f"/api/{DOMAIN}/{entry_id}/documents/0/preview", headers=headers
                    ) as response:
                        checks["invalid_id_rejected"] = response.status == 400
                    print(json.dumps({"test_ha": BASE, "checks": checks}))
                    if len(checks) != 7 or not all(checks.values()):
                        raise RuntimeError("Preview verification failed")
                    return
                if action == "verify_search":
                    entries = await command(DOMAIN + "/entries")
                    if len(entries) != 1:
                        raise RuntimeError("Expected one loaded Paperless test entry")

                    async def search(text, mode="text", page=1):
                        return await command(
                            DOMAIN + "/search",
                            entry_id=entries[0]["entry_id"],
                            text=text,
                            mode=mode,
                            page=page,
                            page_size=5,
                        )

                    found = await search("telekom rechnung mai")
                    reverse = await search("mai rechnung telekom")
                    phrase = await search('"telekom rechnung mai"')
                    titles = await search("telekom rechnung mai", mode="title")
                    first = await search("telekom rechnung")
                    second = await search("telekom rechnung", page=2)
                    async with session.get(
                        BASE + f"/{DOMAIN}/frontend/paperless-ngx-insights.js?v=0.1.0-dev.3"
                    ) as response:
                        asset = await response.text()
                        asset_ok = response.status == 200 and "Mehrere Wörter" in asset
                    invalid = await command(
                        DOMAIN + "/search",
                        allow_error=True,
                        entry_id=entries[0]["entry_id"],
                        text='"telekom',
                        mode="text",
                        page=1,
                        page_size=5,
                    )
                    checks = {
                        "example_nonempty": found["count"] > 0,
                        "order_independent": found == reverse,
                        "phrase_is_narrower": phrase["count"] < found["count"],
                        "title_scope_nonempty": titles["count"] > 0,
                        "pagination": len(first["documents"]) == len(second["documents"]) == 5
                        and not (
                            {d["id"] for d in first["documents"]}
                            & {d["id"] for d in second["documents"]}
                        ),
                        "updated_frontend_served": asset_ok,
                        "invalid_search_reported": invalid.get("error", {}).get("code")
                        == "invalid_search",
                    }
                    print(json.dumps({"test_ha": BASE, "checks": checks}))
                    if not all(checks.values()):
                        raise RuntimeError("Test HA search verification failed")
                    return
                info = await command(
                    "supervisor/api", endpoint="/addons/core_configurator/info", method="get"
                )
                ingress = await command(
                    "supervisor/api", endpoint="/ingress/session", method="post"
                )
                editor = BASE + info["ingress_url"].rstrip("/") + "/"
                cookies = {"ingress_session": ingress["session"]}

                async def listing(path):
                    async with session.get(
                        editor + "api/listdir", params={"path": path}, cookies=cookies
                    ) as r:
                        r.raise_for_status()
                        text = await r.text()
                        return json.loads(text) if text else None

                async def form(path, data):
                    async with session.post(editor + path, data=data, cookies=cookies) as r:
                        r.raise_for_status()
                        result = await r.json(content_type=None)
                        if not isinstance(result, dict) or result.get("error"):
                            raise RuntimeError("File editor operation failed")
                        return result

                root = "/homeassistant"
                base_listing = await listing(root)
                if (
                    not base_listing
                    or base_listing.get("error")
                    or base_listing.get("abspath") != root
                ):
                    raise RuntimeError("Unexpected File editor configuration directory")
                if action == "probe":
                    print(
                        json.dumps({"test_ha": BASE, "file_editor": "ready", "config_root": root})
                    )
                    return

                if action == "verify_install":
                    source = PROJECT / "custom_components" / DOMAIN
                    paths = sorted(
                        p
                        for p in source.rglob("*")
                        if p.is_file()
                        and "__pycache__" not in p.parts
                        and p.suffix in {".py", ".json", ".js", ".png"}
                    )
                    for path in paths:
                        relative = path.relative_to(source).as_posix()
                        destination = root + "/custom_components/" + DOMAIN + "/" + relative
                        async with session.get(
                            editor + "api/file", params={"filename": destination}, cookies=cookies
                        ) as response:
                            response.raise_for_status()
                            actual = await response.read()
                        expected = await asyncio.to_thread(path.read_bytes)
                        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
                            raise RuntimeError("Installed file verification failed: " + relative)
                    print(
                        json.dumps(
                            {"test_ha": BASE, "hacs_files_verified": len(paths), "verified": True}
                        )
                    )
                    return

                async def mkdir(path):
                    existing = await listing(path)
                    if existing and not existing.get("error"):
                        return
                    target = PurePosixPath(path)
                    await mkdir(str(target.parent))
                    await form("api/newfolder", {"path": str(target.parent), "name": target.name})

                source = PROJECT / "custom_components" / DOMAIN
                paths = await asyncio.to_thread(
                    lambda: sorted(
                        p
                        for p in source.rglob("*")
                        if p.is_file()
                        and "__pycache__" not in p.parts
                        and p.suffix in {".py", ".json", ".js"}
                    )
                )
                for path in paths:
                    relative = path.relative_to(source).as_posix()
                    destination = root + "/custom_components/" + DOMAIN + "/" + relative
                    if not destination.startswith(root + "/custom_components/" + DOMAIN + "/"):
                        raise RuntimeError("Unexpected deployment path")
                    await mkdir(str(PurePosixPath(destination).parent))
                    text = await asyncio.to_thread(path.read_text, encoding="utf-8")
                    await form("api/save", {"filename": destination, "text": text})
                    async with session.get(
                        editor + "api/file", params={"filename": destination}, cookies=cookies
                    ) as r:
                        actual = await r.text()
                    if (
                        hashlib.sha256(actual.encode()).digest()
                        != hashlib.sha256(text.encode()).digest()
                    ):
                        raise RuntimeError("Deployed file verification failed")
                print(json.dumps({"test_ha": BASE, "deployment": "verified", "files": len(paths)}))
        finally:
            await session.post(
                BASE + "/auth/token", data={"action": "revoke", "token": auth["refresh_token"]}
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=[
            "probe",
            "deploy",
            "configure",
            "verify_search",
            "verify_preview",
            "verify_lifecycle",
            "verify_download",
            "verify_install",
        ],
    )
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.action, args.key_file))
    except Exception as error:
        # No traceback or upstream bodies: they may contain authentication data.
        print(
            json.dumps(
                {
                    "result": "failed",
                    "error_type": type(error).__name__,
                    "stage": LAST_STAGE["value"],
                    "check": str(error) if type(error) is RuntimeError else None,
                }
            )
        )
        raise SystemExit(1) from None
