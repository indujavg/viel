"""Private, single-GPU development API. Deploy behind authenticated infrastructure."""
import asyncio
from contextlib import asynccontextmanager
import hmac
import json
import logging
import os
import threading
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from .images import MAX_BYTES, decode_image
from .engine import PROFILES


def create_app(engine=None, token=None, load_engine=True):
    access_token = token if token is not None else os.environ.get("VIEL_API_TOKEN", "")
    state = {"engine": engine, "busy": False}

    @asynccontextmanager
    async def lifespan(app):
        if len(access_token) < 32:
            raise RuntimeError("Set VIEL_API_TOKEN to a random secret of at least 32 characters.")
        if state['engine'] is None and load_engine:
            try:
                from .engine import ShieldEngine
                state['engine'] = await asyncio.to_thread(ShieldEngine)
            except Exception:
                logging.getLogger('viel').exception("Shield engine startup failed")
        yield
        state['engine'] = None

    app = FastAPI(title="viel experimental engine", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    def failure(status, code, message):
        return JSONResponse({"error": {"code": code, "message": message}}, status_code=status,
                            headers={"Cache-Control": "no-store"})

    @app.middleware("http")
    async def authenticate(request, call_next):
        if not access_token or not hmac.compare_digest(request.headers.get('authorization',''), f'Bearer {access_token}'):
            return failure(401, 'unauthorized', 'The service needs valid server-side credentials.')
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/health')
    async def health():
        return {"ready": state['engine'] is not None, "busy": state['busy'],
                "method": "targeted-vae-pgd-v1", "experimental": True,
                "profiles": list(PROFILES), "max_side": 1024}

    @app.post('/protect')
    async def protect(request: Request, profile: str = 'subtle', seed: int = 42):
        if profile not in PROFILES or not 0 <= seed <= 2**32-1:
            return failure(422, 'settings', 'Choose a supported profile and seed.')
        if state['engine'] is None:
            return failure(503, 'unavailable', 'The GPU engine is unavailable. Check the service setup.')
        if state['busy']:
            return failure(429, 'busy', 'The GPU is processing another image. Try again shortly.')
        if request.headers.get('content-type','').split(';')[0] not in ('image/png','image/jpeg'):
            return failure(415, 'format', 'Send a PNG or JPEG image.')
        state['busy'] = True
        cancelled = threading.Event()
        task = None
        try:
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > MAX_BYTES:
                    return failure(413, 'size', 'Choose an image up to 10 MB.')
            try:
                image = decode_image(bytes(data))
            except ValueError as error:
                return failure(422, 'image', str(error))
            data.clear()
            task = asyncio.create_task(asyncio.to_thread(state['engine'].protect, image, profile, seed, cancelled))
            started = asyncio.get_running_loop().time()
            while not task.done():
                await asyncio.wait({task}, timeout=0.25)
                if await request.is_disconnected():
                    cancelled.set()
                    return failure(499, 'cancelled', 'Request cancelled.')
                if asyncio.get_running_loop().time() - started > 240:
                    cancelled.set()
                    return failure(504, 'timeout', 'The experiment exceeded four minutes.')
            result, report = task.result()
            return Response(result, media_type='image/png', headers={
                'Content-Disposition': 'attachment; filename="viel-candidate.png"',
                'X-Viel-Report': json.dumps(report, separators=(',',':'))})
        except Exception:
            logging.getLogger('viel').exception('Protection experiment failed')
            return failure(500, 'experiment_failed', 'The experiment failed. No candidate was returned. Check the service logs.')
        finally:
            cancelled.set()
            # Keep the GPU slot occupied until its worker has actually stopped.
            if task is not None:
                try:
                    await asyncio.shield(task)
                except (Exception, asyncio.CancelledError):
                    pass
            state['busy'] = False
    return app

app = create_app()
