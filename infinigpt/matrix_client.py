from __future__ import annotations

import asyncio
import mimetypes
import os
from typing import Any, Awaitable, Callable, Optional

import markdown
from nio import AsyncClient, AsyncClientConfig, MatrixRoom, RoomMessageText, KeyVerificationEvent


TextHandler = Callable[[Any, Any], Awaitable[None]]


class MatrixClientWrapper:
    def __init__(
        self,
        server: str,
        username: str,
        password: str,
        device_id: str = "",
        store_path: str = "store",
        encryption_enabled: bool = True,
    ) -> None:
        # Ensure store path exists for nio's SQLite store (peewee) to open DB
        try:
            os.makedirs(store_path, exist_ok=True)
        except Exception:
            # If creation fails, nio will surface an error; continue
            pass
        cfg = AsyncClientConfig(encryption_enabled=encryption_enabled, store_sync_tokens=True)
        self.client = AsyncClient(server, username, device_id=device_id or None, store_path=store_path, config=cfg)
        try:
            self.client.user_id = username
        except Exception:
            pass
        self.password = password

    async def login(self) -> Any:
        return await self.client.login(self.password, device_name=self.client.device_id or "infinigpt")

    async def ensure_keys(self) -> None:
        if getattr(self.client, "should_upload_keys", False):
            await self.client.keys_upload()

    async def load_store(self) -> None:
        result = getattr(self.client, "load_store", None)
        if callable(result):
            maybe = result()
            if asyncio.iscoroutine(maybe):
                await maybe

    async def join(self, room_id: str) -> None:
        await self.client.join(room_id)

    async def send_text(self, room_id: str, body: str, html: Optional[str] = None) -> None:
        content = {"msgtype": "m.text", "body": body}
        if html is not None:
            content.update({"format": "org.matrix.custom.html", "formatted_body": html})
        await self.client.room_send(room_id=room_id, message_type="m.room.message", content=content, ignore_unverified_devices=True)

    async def send_markdown(self, room_id: str, message: str) -> None:
        try:
            html = markdown.markdown(message, extensions=["extra", "fenced_code", "nl2br", "sane_lists", "tables", "codehilite", "wikilinks", "footnotes"])  # type: ignore
        except Exception:
            html = None
        await self.send_text(room_id, message, html=html)

    async def send_image(self, room_id: str, path: str, filename: str | None, log) -> None:
        if not path or not os.path.exists(path):
            log(f"Error sending image: Invalid path '{path}'")
            await self.send_markdown(room_id, f"Error: Could not find image file at {path}")
            return
        if not filename:
            filename = os.path.basename(path)
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        file_stat = os.stat(path)
        try:
            with open(path, "rb") as fp:
                upload_response, _ = await self.client.upload(fp, content_type=mime_type, filename=filename, filesize=file_stat.st_size)
            if not upload_response or not hasattr(upload_response, "content_uri"):
                log(f"Failed to upload image: Invalid response {upload_response}")
                await self.send_markdown(room_id, f"Failed to upload image '{filename}'.")
                return
            content_uri = upload_response.content_uri
            content = {"body": filename, "info": {"mimetype": mime_type, "size": file_stat.st_size}, "msgtype": "m.image", "url": content_uri}
            await self.client.room_send(room_id=room_id, message_type="m.room.message", content=content, ignore_unverified_devices=True)
        except Exception as e:
            log(f"Error sending image to {room_id}: {e}")
            await self.send_markdown(room_id, f"Sorry, an error occurred while trying to send the image: {e}")

    async def display_name(self, user_id: str) -> str:
        try:
            res = await self.client.get_displayname(user_id)
            return getattr(res, "displayname", user_id)
        except Exception:
            return user_id

    def add_text_handler(self, handler: TextHandler) -> None:
        async def _cb(room: MatrixRoom, event: RoomMessageText) -> None:  # type: ignore
            await handler(room, event)
        self.client.add_event_callback(_cb, RoomMessageText)  # type: ignore

    def add_to_device_callback(self, callback, event_types=None) -> None:
        try:
            self.client.add_to_device_callback(callback, event_types)
        except Exception:
            pass

    async def initial_sync(self, timeout_ms: int = 3000) -> None:
        await self.client.sync(timeout=timeout_ms, full_state=True)

    async def sync_forever(self, timeout_ms: int = 30000) -> None:
        await self.client.sync_forever(timeout=timeout_ms, full_state=True)

    async def shutdown(self) -> None:
        try:
            if hasattr(self.client, "logout"):
                await self.client.logout()  # type: ignore[arg-type]
        except Exception:
            pass
        try:
            if hasattr(self.client, "close"):
                await self.client.close()  # type: ignore[arg-type]
        except Exception:
            pass
