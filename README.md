Nostr Hosting Unit
==================

It is a solution for having a static site (nsite) deployed under your npub.
The raw data is stored on blossom servers, and the mapping from path to sha256 of the content is stored on relays.

Nostr Hosting Unit (this repo) acts as a frontend to your previously uploaded site (nsite). It fetches data from your relays and your blossom servers and presents it under `<your_npub>.nostr.hu`. It does not store anything, and stands on its own. Anyone can deploy the frontend under a different domain, thus making the hosting part redundant, too.

With this architecture it is possible to deploy a static site, or a simple application that doesn't use a backend.

Links in html pages work seamlessly using absolute paths to refer images or js and css files: `<img src="/img/avatar.jpg">`

By the end of the day it is a system that have redundant relays, redundant blossom servers and redundant frontends to ensure freedom of speech and censorship resistance.

Event spec
==========

Nostr event kind `34128` is used for mapping from the file path (that comes after the domain in the http request) to the sha256 of the file content that is fetched by the frontend from the blossom servers.

```
{
    "kind": 34128,
    "tags": [
        ["d", "<path/to/file>"],
        ["sha256", "<hash_of_the_file_content>"]
    ],
    "content": "",
    "created_at": <mtime_of_file>,
    ...
}
```

Install
=======

`pip install -r requirements.txt`

Upload
======

A script is provided in the repository to upload a directory which contains the files of the static msite:

`python uploadr.py dir/to/msite`

Server
======

`python hostr.py`

You will need a certificate for `*.yourdomain.org`, and also set up a wildcard domain in the DNS. You need to configure your webserver to handle wildcard domains and route its traffic to `hostr.py`.
