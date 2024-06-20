import sys
import logging
from aiohttp import web, ClientSession

from monstr.encrypt import Keys

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

async def serve_root(request):
    return web.FileResponse("index.html")

async def redir(request):
    path = request.match_info['path']

    if '@' in path:
        name, domain = path.split('@')
    else:
        name = '_'
        domain = path

    async with ClientSession() as sess:
        async with sess.get(f"https://{domain}/.well-known/nostr.json") as resp:
            if resp.status != 200:
                return web.Response(text=f"nostr.json not found on {domain}")

            json = await resp.json()
            names = json.get('names')
            if names is None:
                return web.Response(text=f"nostr.json on [{domain}] does not have \"names\" key.")

            pubkey = names.get(name)
            if pubkey is None:
                return web.Response(text=f"nostr.json on [{domain}] does not include the npub for [{name}].")

            k = Keys(pub_k=pubkey)
            npub = k.public_key_bech32()

            raise web.HTTPFound(location=f"{npub}.{request.host}")

    return web.Response(text="nothing to do")

app = web.Application()
app.add_routes([
    web.get("/", serve_root),
    web.get("/{path:.*}", redir)
])
web.run_app(app, host='0.0.0.0', port=8001)
