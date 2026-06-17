import os
import sys
import logging
from aiohttp import web, ClientSession
from dotenv import load_dotenv

from monstr.client.client import Client, ClientPool
from monstr.encrypt import Keys

load_dotenv()

SERVER_DOMAIN = os.getenv('SERVER_DOMAIN')
RELAY = os.getenv('RELAY')
BLOSSOM = os.getenv('BLOSSOM')
FILEMAP_KIND = "34128"

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

async def serve_file(request):
    host = request.host

    if ':' in host:
        # Remove port from the end.
        host = host.split(':')[0]

    assert host.endswith(f".{SERVER_DOMAIN}"), f'web server configuration error: host={host}'
    npub = host.split(f".{SERVER_DOMAIN}")[0]

    path = request.path

    if path.endswith("/"):
        path += "index.html"

    if path.startswith("/"):
        path = path[1:]

    try:
        pubkey = Keys(pub_k=npub).public_key_hex()
    except Exception as e:
        log.debug(str(e))
        raise web.HTTPNotFound(reason="Subdomain is not a valid npub.")

    async with Client(RELAY) as c:
        #TODO: make it a subscription, group authors per relay!
        evs = await c.query({
            'kinds': [FILEMAP_KIND],
            'authors': [pubkey],
            '#d': [path],
        })

        if len(evs) == 0:
            raise web.HTTPNotFound(
                reason=f"Nostr filemap event for [{path}] not found on relay [{RELAY}].")

        ev = evs[0]
        sha256 = ev.tags.get_tags_value("sha256")[0]

        async with ClientSession() as sess:
            async with sess.get(f"{BLOSSOM}/{sha256}") as resp:
                if resp.status >= 300:
                    t = await resp.text()
                    return web.Response(
                        status=resp.status, text=f"Blossom server returned [{t}]")

                data = await resp.read()
                return web.Response(content_type=resp.content_type, body=data)

app = web.Application()
app.add_routes([
    web.get("/", serve_file),
    web.get("/{path:.*}", serve_file)
])

if __name__ == "__main__":
    web.run_app(app, host='0.0.0.0', port=8000)
