import asyncio

from fastapi import APIRouter, WebSocket

from .access import AuthStreamingProcessor
from .adapters.fastapi_connection import FastApiConnection
from .domain import extract_raw_api_key

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    runtime = websocket.app.state.runtime
    auth: AuthStreamingProcessor = runtime.auth
    connection = FastApiConnection(websocket)
    raw_key = extract_raw_api_key(
        authorization=websocket.headers.get("authorization"),
        x_api_key=websocket.headers.get("x-api-key"),
        body_key=websocket.query_params.get("api_key"),
    )
    ctx = await auth.connect_if_allowed(connection, raw_key)
    if ctx is None:
        return
    stop = asyncio.Event()
    task = asyncio.create_task(
        auth.ws_key_watchdog(
            connection=connection, raw_key=ctx.raw_key, stop=stop
        )
    )
    try:
        while not stop.is_set():
            await websocket.receive()
    except Exception:
        pass
    finally:
        stop.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await runtime.manager.disconnect(connection, kid=ctx.kid)
