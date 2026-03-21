import asyncio
import json
import logging
import time
from contextlib import suppress
from typing import Any, Callable
from urllib.parse import quote

import aiohttp

from .const import (
    BASE_URL,
    DEFAULT_MIN_PERIOD,
    EXTRA_SUBSCRIBED_TAGS,
    FORCE_LOGIN_QUERY,
    GROUP_SUBSCRIPTION_CHUNK_SIZE,
    LOGIN_URL,
    PROJECT_CONFIG_PATH,
    PROJECT_PROPERTY,
    SSE_PATH,
    WRITE_TAGS_URL,
)

_LOGGER = logging.getLogger(__name__)


class LeisurePoolAPI:
    """API client for interacting with the Leisure Pool system."""

    def __init__(self, host: str, username: str, password: str) -> None:
        self._host = host
        self._username = username
        self._password = password
        self._base_url = BASE_URL.format(host=host)
        self._headers = {"User-Agent": "LeisurePoolsHomeAssistant/2.0"}
        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=30)
        self._stream_timeout = aiohttp.ClientTimeout(total=None, connect=15, sock_read=90)
        self._login_cooldown = 2
        self._last_login_attempt = 0.0
        self._login_info: dict[str, Any] = {}
        self._project_path: str | None = None
        self._web_project_url: str | None = None
        self._config: dict[str, Any] = {}
        self._tag_values: dict[str, Any] = {}
        self._tag_payloads: dict[str, dict[str, Any]] = {}
        self._listeners: set[Callable[[], None]] = set()
        self._sse_task: asyncio.Task | None = None
        self._running = False
        self._sse_client_id: str | None = None

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            # The controller is typically reached by IP address; aiohttp's default
            # cookie jar rejects cookies from IP hosts unless unsafe=True.
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers=self._headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True),
            )

    async def async_setup(self) -> bool:
        """Initialize login, project metadata, and the SSE worker."""
        try:
            if not await self.login(force_refresh=True):
                return False

            await self._ensure_project_metadata()
            await self.async_start()
            return True
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to complete Leisure Pool setup for %s", self._host)
            return False

    async def async_start(self) -> None:
        """Start the SSE background task."""
        if self._sse_task and not self._sse_task.done():
            return

        self._running = True
        self._sse_task = asyncio.create_task(self._sse_loop(), name=f"leisure_pool_sse_{self._host}")

    async def close(self) -> None:
        """Close background tasks and the HTTP session."""
        self._running = False
        if self._sse_task:
            self._sse_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._sse_task
            self._sse_task = None

        if self._session and not self._session.closed:
            try:
                await self._request_text("GET", "/cgi/logout", allow_reauth=False)
            except Exception:  # noqa: BLE001
                pass
            await self._session.close()

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for live state changes."""
        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error while notifying Leisure Pool listeners")

    async def login(self, force_refresh: bool = False) -> bool:
        """Log in and keep the session cookies."""
        current_time = time.time()
        if not force_refresh and current_time - self._last_login_attempt < self._login_cooldown:
            return bool(self._login_info)

        await self._ensure_session()
        self._last_login_attempt = current_time

        if force_refresh and self._session is not None:
            self._session.cookie_jar.clear()
            self._login_info = {}

        result = await self._login_once(force=False)
        if not result["ok"] and result["status_text"] in {"#e_too_many_users", "#e_re-login_attempt"}:
            result = await self._login_once(force=True)

        if not result["ok"]:
            _LOGGER.error("Login failed: %s", result["body"].strip())
            self._login_info = {}
            return False

        self._login_info = result
        _LOGGER.info("Login successful for %s", self._host)
        return True

    async def _login_once(self, force: bool) -> dict[str, Any]:
        assert self._session is not None
        login_url = LOGIN_URL.format(host=self._host)
        if force:
            login_url += FORCE_LOGIN_QUERY

        payload = {"username": self._username, "password": self._password}
        async with self._session.post(login_url, data=payload, headers=self._headers) as response:
            body = await response.text()
            if response.cookies:
                self._session.cookie_jar.update_cookies(response.cookies)
            parsed = self._parse_login_response(body)
            parsed["body"] = body
            parsed["status_code"] = response.status
            parsed["force"] = force
            return parsed

    def _parse_login_response(self, body: str) -> dict[str, Any]:
        normalized_lines = [line.strip().lower() for line in body.splitlines()]
        token = None
        info: dict[str, Any] = {}
        for line in body.splitlines():
            if line.startswith("IDALToken="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("INFO="):
                with suppress(json.JSONDecodeError):
                    info = json.loads(line.split("=", 1)[1])

        status_text = next((line for line in normalized_lines if line.startswith("#")), "")
        error_code = next((line for line in normalized_lines if line.startswith("-")), "")
        return {
            "ok": "#s_ok" in normalized_lines and token is not None,
            "token": token,
            "info": info,
            "status_text": status_text,
            "error_code": error_code,
        }

    async def _ensure_project_metadata(self) -> None:
        if self._project_path and self._web_project_url and self._config:
            return

        prop_text = await self._request_text("GET", f"/cgi/getProperties?n=1&it1={PROJECT_PROPERTY}")
        parts = prop_text.split("\t")
        if len(parts) < 3 or parts[1].strip() != "S_OK":
            raise RuntimeError(f"Unable to read project path: {prop_text.strip()}")

        self._project_path = self._normalize_project_path(parts[2].strip())
        self._web_project_url = f"http://{self._host}/{self._project_path}/web/web"
        config_text = await self._request_text("GET", f"/{self._project_path}/{PROJECT_CONFIG_PATH}")
        self._config = json.loads(config_text)

    def _normalize_project_path(self, project_path: str) -> str:
        normalized = project_path.strip().strip("/")
        if normalized.startswith("workspace/"):
            normalized = normalized.split("/", 1)[1]
        return normalized

    async def _request_text(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: Any = None,
        allow_reauth: bool = True,
        timeout: aiohttp.ClientTimeout | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        await self._ensure_session()
        assert self._session is not None

        url = path if path.startswith("http") else f"http://{self._host}{path}"
        request_headers = dict(self._headers)
        if headers:
            request_headers.update(headers)

        try:
            async with self._session.request(
                method,
                url,
                params=params,
                data=data,
                timeout=timeout or self._timeout,
                headers=request_headers,
            ) as response:
                text = await response.text()
                if response.status == 500 and allow_reauth:
                    _LOGGER.debug("Got HTTP 500 for %s, retrying after fresh login", url)
                    if await self.login(force_refresh=True):
                        return await self._request_text(
                            method,
                            path,
                            params=params,
                            data=data,
                            allow_reauth=False,
                            timeout=timeout,
                            headers=headers,
                        )
                    _LOGGER.error("Fresh login retry failed for %s", url)
                response.raise_for_status()
                return text
        except aiohttp.ClientResponseError:
            raise
        except Exception:
            _LOGGER.exception("Request failed: %s %s", method, url)
            raise

    async def send_request(self, action: str, value: int) -> bool:
        """Send a writeTags request."""
        params = {
            "n": 1,
            "t1": action,
            "v1": value,
            "nocache": int(time.time() * 1000),
        }
        await self._request_text("GET", WRITE_TAGS_URL.format(host=self._host), params=params)
        return True

    async def turn_light_on(self) -> bool:
        await self.send_request("bLightsON.0", 1)
        await self.send_request("bLightsON.0", 0)
        return True

    async def turn_light_off(self) -> bool:
        await self.send_request("nLichtKleur.-1", 0)
        return True

    async def open_cover(self) -> bool:
        await self.send_request("bOpenCover.0", 1)
        await self.send_request("bOpenCover.0", 0)
        return True

    async def close_cover(self) -> bool:
        await self.send_request("bCloseCover.0", 1)
        await self.send_request("bCloseCover.0", 0)
        return True

    def get_tag_value(self, tag_name: str, default: Any = None) -> Any:
        return self._tag_values.get(tag_name, default)

    def get_tag_payload(self, tag_name: str) -> dict[str, Any] | None:
        return self._tag_payloads.get(tag_name)

    def get_all_tag_values(self) -> dict[str, Any]:
        return dict(self._tag_values)

    def get_config(self) -> dict[str, Any]:
        return self._config

    def is_light_on(self) -> bool | None:
        color = self.get_tag_value("nLichtKleur")
        changing = self.get_tag_value("bColorChanging")
        if color is None and changing is None:
            return None
        return bool(changing) or (color not in (None, "", 0, "0"))

    def get_cover_position(self) -> int | None:
        position = self.get_tag_value("nPositieRolluik")
        if position in (None, ""):
            return None
        try:
            raw_position = float(position)
            if raw_position > 100:
                raw_position = raw_position / 10
            return max(0, min(100, int(round(raw_position))))
        except (TypeError, ValueError):
            return None

    def is_cover_closed(self) -> bool | None:
        position = self.get_cover_position()
        if position is not None:
            return position <= 0
        unlocked = self.get_tag_value("bCoverUnlocked")
        if unlocked is None:
            return None
        return not bool(unlocked)

    def get_cover_status(self) -> str:
        position = self.get_cover_position()
        if position is not None:
            if position <= 0:
                return "closed"
            if position >= 100:
                return "open"
            return "partial"

        unlocked = self.get_tag_value("bCoverUnlocked")
        if unlocked is None:
            return "unknown"
        return "unlocked" if bool(unlocked) else "locked"

    async def _sse_loop(self) -> None:
        retry_delay = 5
        while self._running:
            try:
                if not await self.login():
                    await asyncio.sleep(retry_delay)
                    continue

                await self._ensure_project_metadata()
                await self._run_sse_stream()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning("SSE loop error for %s: %s", self._host, exc)
                await asyncio.sleep(retry_delay)

    async def _run_sse_stream(self) -> None:
        assert self._session is not None
        self._sse_client_id = f"{int(time.time() * 1000)}{int(time.monotonic() * 1000) % 1000:03d}"
        sse_url = f"http://{self._host}{SSE_PATH}?id={self._sse_client_id}&minPeriod={DEFAULT_MIN_PERIOD}"
        setup_commands = self._build_sse_setup_commands()

        async with self._session.get(
            sse_url,
            timeout=self._stream_timeout,
            headers={**self._headers, "Accept": "text/event-stream", "Cache-Control": "no-cache"},
        ) as response:
            response.raise_for_status()

            for query in setup_commands:
                await self._request_text("GET", f"{SSE_PATH}?id={self._sse_client_id}&{query}")

            current_event: dict[str, Any] = {"event": "message", "data": []}

            async for raw_line in response.content:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == "":
                    await self._consume_sse_event(current_event)
                    current_event = {"event": "message", "data": []}
                    continue

                if line.startswith(":"):
                    continue

                field, _, value = line.partition(":")
                value = value.lstrip(" ")
                if field == "data":
                    current_event.setdefault("data", []).append(value)
                else:
                    current_event[field] = value

                if not self._running:
                    break

    async def _consume_sse_event(self, event: dict[str, Any]) -> None:
        if not event.get("data"):
            return

        event_type = event.get("event", "message")
        data = "\n".join(event["data"])
        if event_type != "tags":
            return

        try:
            tags = json.loads(data)
        except json.JSONDecodeError:
            _LOGGER.debug("Ignoring unparsable SSE payload: %s", data)
            return

        changed = False
        for item in tags:
            tag_name = item.get("n")
            tag_payload = item.get("v", {})
            if not tag_name:
                continue

            tag_value = tag_payload.get("v")
            previous_value = self._tag_values.get(tag_name)
            self._tag_values[tag_name] = tag_value
            self._tag_payloads[tag_name] = tag_payload
            if previous_value != tag_value:
                changed = True

        if changed:
            self._notify_listeners()

    def _build_sse_setup_commands(self) -> list[str]:
        commands = ["na=*"]

        groups = list(self._config.get("groups.json", {}).keys())
        for index in range(0, len(groups), GROUP_SUBSCRIPTION_CHUNK_SIZE):
            chunk = groups[index : index + GROUP_SUBSCRIPTION_CHUNK_SIZE]
            parts = [f"ng={len(chunk)}"]
            for item_index, group_name in enumerate(chunk):
                parts.append(f"g{item_index}={quote(group_name, safe='')}")
            commands.append("&".join(parts))

        subscribed_group_tags = {
            tag_name
            for group_conf in self._config.get("groups.json", {}).values()
            for tag_name in group_conf.get("tgs", {})
        }
        extra_tags = [tag for tag in EXTRA_SUBSCRIBED_TAGS if tag not in subscribed_group_tags]
        if extra_tags:
            parts = [f"nt={len(extra_tags)}"]
            for item_index, tag_name in enumerate(extra_tags):
                parts.append(f"t{item_index}={quote(tag_name, safe='')}")
            commands.append("&".join(parts))

        return commands
