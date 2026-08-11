from aiohttp import web

from PekoMusic.config import Config


async def _health(request):
    return web.Response(text="Peko Music is alive and streaming! 🎶")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    return app


async def run_web_server():
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
