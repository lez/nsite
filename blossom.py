import json
import base64
import aiohttp
from monstr.event.event import Event

async def store(sk, data, blossom_server, sha256):
    auth_event = Event(
        kind=24242,
        content=f"Upload {sha256}",
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

    # Upload object to blossom.
    async with aiohttp.ClientSession() as sess:
        async with sess.put(
                f"{blossom_server}/upload",
                data=data,
                headers={
                    "Authorization": f"Nostr {b64_auth}",
                    "Content-Type": "text/html"
                }) as resp:

            if resp.status != 200:
                txt = await resp.text()
                raise Exception(txt)

            await resp.text()
