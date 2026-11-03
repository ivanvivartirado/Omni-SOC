import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.db import session_factory
from app.core.deps import user_from_token
from app.core.security import ACCESS_COOKIE

router = APIRouter()


@router.websocket("/api/ws/events")
async def events_ws(ws: WebSocket) -> None:
    settings = ws.app.state.settings
    origin = ws.headers.get("origin")
    if origin and origin not in settings.origins:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    async with session_factory()() as s:
        user = await user_from_token(s, ws.cookies.get(ACCESS_COOKIE))
    if not user:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws.accept()
    bus = ws.app.state.bus
    q = bus.subscribe()

    async def drain_client() -> None:
        while True:
            await ws.receive_text()  # mantiene viva la conexión y detecta el cierre

    reader = asyncio.create_task(drain_client())
    try:
        while not reader.done():
            try:
                msg = await asyncio.wait_for(q.get(), timeout=20)
            except TimeoutError:
                msg = {"type": "ping"}
            await ws.send_json(msg)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        bus.unsubscribe(q)
        reader.cancel()
        with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect, RuntimeError):
            await reader
