import argparse
import http.cookiejar
import json
import re
import time
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


DEFAULT_HOST = "192.168.20.3"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
USER_AGENT = "LeisurePoolTestProbe/1.0"
DEFAULT_MIN_PERIOD = 1000
GROUP_SUBSCRIPTION_CHUNK_SIZE = 4

ASSET_PATTERN = re.compile(
    r"""(?:src|href)=["'](?P<url>[^"'#?]+(?:\?[^"'#]*)?)["']""",
    re.IGNORECASE,
)
CGI_PATTERN = re.compile(r"""/cgi/[^"'\\\s<>()]+""", re.IGNORECASE)


def make_output_dir(base_dir: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir = base_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def sanitize_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", value)


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def unique_urls(urls: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


class LeisurePoolProbe:
    def __init__(self, host: str, username: str, password: str) -> None:
        self.host = host
        self.base_url = f"http://{host}"
        self.username = username
        self.password = password
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookie_jar))

    def _open(self, url: str, data: bytes | None = None, timeout: int = 15, headers: dict | None = None):
        request_headers = {"User-Agent": USER_AGENT}
        if headers:
            request_headers.update(headers)
        request = Request(url, data=data, headers=request_headers)
        return self.opener.open(request, timeout=timeout)

    def login(self, force: bool = False) -> dict:
        login_url = f"{self.base_url}/cgi/login"
        if force:
            login_url += "?forceLogin=true"
        payload = urlencode({"username": self.username, "password": self.password}).encode()
        with self._open(login_url, data=payload, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
            result = parse_login_response(body)
            result["status_code"] = response.status
            result["body"] = body
            result["force"] = force
            return result

    def fetch_page(self, path: str = "/"):
        return self._open(urljoin(self.base_url, path), timeout=15)

    def download_url(self, url: str):
        return self._open(url, timeout=20)

    def logout(self) -> str:
        with self._open(f"{self.base_url}/cgi/logout", timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")

    def get_property(self, name: str) -> dict:
        url = f"{self.base_url}/cgi/getProperties?n=1&it1={name}"
        with self._open(url, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
        parts = body.split("\t")
        return {
            "name": parts[0].strip("# \r\n") if parts else name,
            "code": parts[1].strip() if len(parts) > 1 else "E_FAIL",
            "value": parts[2].strip() if len(parts) > 2 else "",
            "raw": body,
        }

    def fetch_json(self, url: str) -> object:
        with self._open(url, timeout=20) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))

    def sse_command(self, client_id: str, query: str) -> str:
        url = f"{self.base_url}/cgi/sse?id={client_id}&{query}"
        with self._open(url, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace").strip()

    def stream_sse(self, sse_url: str, duration: int, output_dir: Path, setup_commands: list[str] | None = None) -> dict:
        event_log = []
        raw_path = output_dir / "sse_raw.txt"
        parsed_path = output_dir / "sse_events.json"
        started_at = time.time()
        current_event = {"event": "message", "data": []}
        content_type = ""
        setup_results = []

        with self._open(
            sse_url,
            timeout=duration + 15,
            headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
        ) as response:
            content_type = response.headers.get("Content-Type", "")
            client_id = parse_qs_value(sse_url, "id")

            if client_id and setup_commands:
                for query in setup_commands:
                    try:
                        setup_results.append({"query": query, "result": self.sse_command(client_id, query)})
                    except Exception as exc:  # noqa: BLE001
                        setup_results.append({"query": query, "error": str(exc)})

            with raw_path.open("w", encoding="utf-8") as raw_file:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                    raw_file.write(f"{line}\n")
                    raw_file.flush()

                    if line == "":
                        if current_event["data"]:
                            event_log.append(
                                {
                                    "event": current_event.get("event", "message"),
                                    "id": current_event.get("id"),
                                    "retry": current_event.get("retry"),
                                    "data": "\n".join(current_event["data"]),
                                }
                            )
                        current_event = {"event": "message", "data": []}
                    elif line.startswith(":"):
                        continue
                    else:
                        field, _, value = line.partition(":")
                        value = value.lstrip(" ")
                        if field == "data":
                            current_event["data"].append(value)
                        elif field in {"event", "id", "retry"}:
                            current_event[field] = value

                    if time.time() - started_at >= duration:
                        break

        save_json(
            parsed_path,
            {
                "sse_url": sse_url,
                "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "events": event_log,
                "headers": {"content_type": content_type},
                "setup_commands": setup_results,
            },
        )
        return {"content_type": content_type, "event_count": len(event_log), "setup_commands": setup_results}


def build_sse_url(base_url: str, sse_path: str, sse_id: str | None, min_period: int) -> str:
    if sse_id is None:
        sse_id = str(int(time.time() * 1000000))
    base = urljoin(base_url, sse_path)
    return f"{base}?id={sse_id}&minPeriod={min_period}"


def parse_qs_value(url: str, key: str) -> str | None:
    query = urlparse(url).query
    for part in query.split("&"):
        name, _, value = part.partition("=")
        if name == key:
            return value
    return None


def parse_login_response(body: str) -> dict:
    normalized = body.lower().splitlines()
    token = None
    info = {}
    for line in body.splitlines():
        if line.startswith("IDALToken="):
            token = line.split("=", 1)[1].strip()
        elif line.startswith("INFO="):
            try:
                info = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                info = {}

    status_text = next((line for line in normalized if line.startswith("#")), "")
    error_code = next((line for line in normalized if line.startswith("-")), "")
    return {
        "ok": "#s_ok" in normalized and token is not None,
        "token": token,
        "info": info,
        "status_text": status_text,
        "error_code": error_code,
    }


def normalize_project_path(project_path: str) -> str:
    normalized = project_path.strip().strip("/")
    if normalized.startswith("workspace/"):
        normalized = normalized.split("/", 1)[1]
    return normalized


def discover_web_project(probe: LeisurePoolProbe) -> dict:
    prop = probe.get_property("projectRelativePath")
    if prop["code"] != "S_OK" or not prop["value"]:
        raise RuntimeError(f"projectRelativePath ophalen mislukt: {prop['raw'].strip()}")

    project_path = normalize_project_path(prop["value"])
    web_path = f"/{project_path}/web/web"
    return {
        "project_relative_path": prop["value"],
        "normalized_project_path": project_path,
        "web_path": web_path,
        "main_page": f"{web_path}/_webmain.html",
        "index_page": f"{web_path}/index.html",
    }


def fetch_project_config(probe: LeisurePoolProbe, web_path: str, output_dir: Path) -> dict:
    conf_url = urljoin(probe.base_url, f"{web_path}/config/conf.json")
    conf = probe.fetch_json(conf_url)
    save_json(output_dir / "conf.json", conf)

    tags = conf.get("tags.json", {})
    groups = conf.get("groups.json", {})
    alarms = conf.get("alarms.json", {})
    save_json(output_dir / "tags.json", tags)
    save_json(output_dir / "groups.json", groups)
    save_json(output_dir / "alarms.json", alarms)

    return {
        "url": conf_url,
        "tag_count": len(tags),
        "group_count": len(groups),
        "alarm_count": len(alarms.get("alarms", {})) if isinstance(alarms, dict) else 0,
        "groups": list(groups.keys()),
        "tags": list(tags.keys()),
    }


def build_group_subscription_queries(groups: list[str]) -> list[str]:
    queries = ["na=*"]
    for index in range(0, len(groups), GROUP_SUBSCRIPTION_CHUNK_SIZE):
        chunk = groups[index : index + GROUP_SUBSCRIPTION_CHUNK_SIZE]
        parts = [f"ng={len(chunk)}"]
        for chunk_index, group_name in enumerate(chunk):
            parts.append(f"g{chunk_index}={quote_value(group_name)}")
        queries.append("&".join(parts))
    return queries


def quote_value(value: str) -> str:
    return quote(value, safe="")


def extract_asset_urls(page_url: str, html: str) -> list[str]:
    urls = []
    for match in ASSET_PATTERN.finditer(html):
        raw_url = unescape(match.group("url"))
        absolute_url = urljoin(page_url, raw_url)
        parsed = urlparse(absolute_url)
        if parsed.scheme in {"http", "https"}:
            urls.append(absolute_url)
    return unique_urls(urls)


def extract_cgi_references(content: str) -> list[str]:
    return unique_urls(CGI_PATTERN.findall(content))


def dump_webpage(probe: LeisurePoolProbe, page_path: str, output_dir: Path, max_assets: int) -> dict:
    with probe.fetch_page(page_path) as response:
        html = response.read().decode("utf-8", errors="replace")
        page_url = response.geturl()
        status_code = response.status
    save_text(output_dir / "page.html", html)

    asset_urls = extract_asset_urls(page_url, html)
    downloaded_assets = []
    discovered_cgi = set(extract_cgi_references(html))

    for index, asset_url in enumerate(asset_urls[:max_assets], start=1):
        try:
            with probe.download_url(asset_url) as asset_response:
                asset_text = asset_response.read().decode("utf-8", errors="replace")
                parsed = urlparse(asset_url)
                suffix = Path(parsed.path).suffix or ".txt"
                stem = sanitize_name(Path(parsed.path).stem or "asset")
                filename = f"{index:03d}_{stem}{suffix}"
                save_text(output_dir / "assets" / filename, asset_text)
                downloaded_assets.append({"url": asset_url, "status_code": asset_response.status, "file": filename})
                discovered_cgi.update(extract_cgi_references(asset_text))
        except Exception as exc:  # noqa: BLE001
            downloaded_assets.append({"url": asset_url, "error": str(exc)})

    summary = {
        "page_url": page_url,
        "status_code": status_code,
        "asset_count": len(asset_urls),
        "downloaded_asset_count": len(downloaded_assets),
        "assets": downloaded_assets,
        "discovered_cgi_paths": sorted(discovered_cgi),
    }
    save_json(output_dir / "webpage_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Log in to a Leisure Pool controller, dump the webpage, and capture the SSE stream."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Controller IP or hostname.")
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="Login username.")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Login password.")
    parser.add_argument("--page-path", default="/", help="Page to download after login.")
    parser.add_argument("--sse-path", default="/cgi/sse", help="SSE endpoint path.")
    parser.add_argument("--sse-id", default=None, help="Optional SSE id. Defaults to a generated value.")
    parser.add_argument("--min-period", type=int, default=DEFAULT_MIN_PERIOD, help="SSE minPeriod parameter.")
    parser.add_argument("--duration", type=int, default=30, help="How many seconds to listen to SSE.")
    parser.add_argument("--max-assets", type=int, default=25, help="Maximum number of page assets to download.")
    parser.add_argument(
        "--output-dir",
        default="test/output",
        help="Base output directory. A timestamped subdirectory is created automatically.",
    )
    parser.add_argument(
        "--skip-page-dump",
        action="store_true",
        help="Only test the SSE endpoint and skip downloading the webpage.",
    )
    parser.add_argument(
        "--no-force-login",
        action="store_true",
        help="Do not retry login with forceLogin=true when the controller refuses a normal login.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = make_output_dir(Path(args.output_dir))
    probe = LeisurePoolProbe(args.host, args.username, args.password)

    run_summary = {
        "host": args.host,
        "page_path": args.page_path,
        "sse_path": args.sse_path,
        "min_period": args.min_period,
        "duration": args.duration,
        "output_dir": str(output_dir),
    }

    try:
        login_result = probe.login(force=False)
        if not login_result["ok"] and not args.no_force_login:
            if login_result["status_text"] in {"#e_too_many_users", "#e_re-login_attempt"} or not login_result["status_text"]:
                login_result = probe.login(force=True)

        if not login_result["ok"]:
            raise RuntimeError(login_result["body"].strip() or "Onbekende loginfout")

        run_summary["login"] = {
            "status_code": login_result["status_code"],
            "force": login_result["force"],
            "status_text": login_result["status_text"],
            "cookies": {cookie.name: cookie.value for cookie in probe.cookie_jar},
        }
        print(f"[+] Login OK naar {args.host}")
    except Exception as exc:  # noqa: BLE001
        run_summary["login_error"] = str(exc)
        save_json(output_dir / "run_summary.json", run_summary)
        print(f"[!] Login mislukt: {exc}")
        return 1

    web_project = None
    config_summary = None
    setup_commands = ["na=*"]

    try:
        web_project = discover_web_project(probe)
        run_summary["project"] = web_project
        print(f"[+] HMI project gevonden: {web_project['normalized_project_path']}")
    except Exception as exc:  # noqa: BLE001
        run_summary["project_error"] = str(exc)
        print(f"[!] HMI projectpad niet gevonden: {exc}")

    if web_project:
        try:
            config_summary = fetch_project_config(probe, web_project["web_path"], output_dir)
            run_summary["config"] = {
                "url": config_summary["url"],
                "tag_count": config_summary["tag_count"],
                "group_count": config_summary["group_count"],
                "alarm_count": config_summary["alarm_count"],
            }
            setup_commands = build_group_subscription_queries(config_summary["groups"])
            print(f"[+] Config opgeslagen, {config_summary['tag_count']} tags en {config_summary['group_count']} groepen gevonden")
        except Exception as exc:  # noqa: BLE001
            run_summary["config_error"] = str(exc)
            print(f"[!] Config ophalen mislukt: {exc}")

    if not args.skip_page_dump:
        try:
            target_page = web_project["main_page"] if web_project else args.page_path
            webpage_summary = dump_webpage(probe, target_page, output_dir, args.max_assets)
            run_summary["webpage"] = webpage_summary
            print(f"[+] Webpagina opgeslagen, {webpage_summary['asset_count']} assets gevonden")
        except Exception as exc:  # noqa: BLE001
            run_summary["webpage_error"] = str(exc)
            print(f"[!] Webpagina ophalen mislukt: {exc}")

    sse_url = build_sse_url(probe.base_url, args.sse_path, args.sse_id, args.min_period)
    run_summary["sse_url"] = sse_url
    print(f"[+] Luisteren naar SSE: {sse_url}")

    try:
        sse_summary = probe.stream_sse(sse_url, args.duration, output_dir, setup_commands=setup_commands)
        run_summary["sse"] = sse_summary
        print(f"[+] SSE opgeslagen, {sse_summary['event_count']} events ontvangen")
    except Exception as exc:  # noqa: BLE001
        run_summary["sse_error"] = str(exc)
        print(f"[!] SSE stream mislukt: {exc}")
        save_json(output_dir / "run_summary.json", run_summary)
        return 1

    try:
        logout_body = probe.logout()
        run_summary["logout"] = logout_body.strip()
    except Exception as exc:  # noqa: BLE001
        run_summary["logout_error"] = str(exc)

    save_json(output_dir / "run_summary.json", run_summary)
    print(f"[+] Klaar. Output staat in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
