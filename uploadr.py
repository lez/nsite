import argparse
import blossom
import os
import asyncio
import hashlib
import time
from datetime import datetime

from monstr.encrypt import Keys
from monstr.client.client import Client
from monstr.event.event import Event

RELAY = "wss://relay.magnifiq.tech" # Right now it's hardcoded
BLOSSOM = "https://blossom.nostr.hu" # Same here.
FILEMAP_KIND = "34128"

parser = argparse.ArgumentParser()
parser.add_argument(
    '--sec',
    help="Secret key in nsec or hex format")
parser.add_argument(
    '--blossom', '-b', default=BLOSSOM,
    help="Blossom server to use")
parser.add_argument(
    '--relay', '-r', default=RELAY,
    help="Relay to upload filemap events to.")
parser.add_argument(
    "rootdir",
    help="Directory to upload as nsite (default: current directory)")

args = parser.parse_args()
if not args.sec:
    try:
        secfile = os.path.join(os.environ["HOME"], ".sec")
        print(f"Using secret from [{secfile}]")
        sec = open(secfile).read().strip()
    except:
        raise SystemExit("Need your secret key!")
else:
    sec = '{:>064s}'.format(args.sec)


async def upload_file(path, args, pubkey, sk):
    with open(path, "rb") as f:
        mtime = int(os.fstat(f.fileno()).st_mtime)

        data = f.read()
        h = hashlib.sha256()
        h.update(data)
        sha256 = h.digest().hex()

        async with Client(args.relay) as c:
            evs = await c.query({
                'kinds': 34128,
                'authors': [pubkey],
                '#d': [path],
            })
            if len(evs) == 1:
                ev = evs[0]
                evtime = int(time.mktime(ev.created_at.timetuple()))
                if evtime == mtime:
                    print(f"Up to date [{path}]")

                    #TODO: chk first!
                    print(f"Storing file [{sha256}] on blossom.")
                    await blossom.store(sk, data, BLOSSOM, sha256)

                    return
                else:
                    print(f"Updating existing file mtime=[{ev.created_at}], ours=[{datetime.fromtimestamp(mtime)}].")

            else:
                print(f"Uploading new file [{path}]")

            filemap_event = Event(
                kind=34128,
                pub_key=pubkey,
                created_at=mtime,
                tags=[
                    ['d', path],
                    ['sha256', sha256]
                ]
            )
            filemap_event.sign(sk.private_key_hex())

            c.publish(filemap_event)
            await asyncio.sleep(1)
            print(f"Published filemap event [{filemap_event.id}] on [{args.relay}]")

            print(f"Storing file [{sha256}] on blossom.")
            await blossom.store(sk, data, BLOSSOM, sha256)


async def _main(args):
    sk = Keys(sec)
    pubkey = sk.public_key_hex()
    os.chdir(args.rootdir)

    for curr, dirs, files in os.walk(args.rootdir):
        for file in files:
            filename = os.path.relpath(os.path.join(curr, file))
            await upload_file(filename, args, pubkey, sk)

asyncio.run(_main(args))
