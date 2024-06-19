import json
import base64
import aiohttp
import mimetypes

from monstr.event.event import Event

async def check(blossom, sha256):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(f"{blossom}/{sha256}") as resp:
            #FIXME: use HEAD once https://github.com/hzrd149/blossom-server/issues/4 is fixed
            return resp.status == 200


async def store(sk, data, blossom_server, sha256, path):
    auth_event = Event(
        kind=24242,
        content=f"Upload {path}",
        pub_key=sk.public_key_hex(),
        tags=[
            ["t", "upload"],
            ["x", sha256],
            ["expiration", "1777777777"]
        ]
    )
    auth_event.sign(sk.private_key_hex())
    json_auth = json.dumps(auth_event.data(), separators=(',',':'))
    b64_auth = base64.b64encode(json_auth.encode()).decode()

    content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'

    # Upload object to blossom.
    async with aiohttp.ClientSession() as sess:
        async with sess.put(
                f"{blossom_server}/upload",
                data=data,
                headers={
                    "Authorization": f"Nostr {b64_auth}",
                    "Content-Type": content_type
                }) as resp:

            if resp.status != 200:
                txt = await resp.text()
                raise Exception(txt)

            await resp.text()
