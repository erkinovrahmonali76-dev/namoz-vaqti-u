import os

from aiohttp import web


async def _health(request: web.Request) -> web.Response:
    return web.Response(text="NAMOZ VAQTI UZ ishlayapti")


async def start_web_server() -> None:
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
