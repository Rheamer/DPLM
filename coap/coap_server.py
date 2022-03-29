import datetime
import logging

import asyncio

import aiocoap.resource as resource
import aiocoap
from os import environ

discovered_devs = set()

class Discovery(resource.Resource):
    async def render_put(self, request):
        print("Discovery incoming")
        text = ["Used protocol: %s." % request.remote.scheme]

        text.append("Request came from %s." % request.remote.hostinfo)
        discovered_devs.add(request.remote.hostinfo)
        text.append("The server address used %s." % request.remote.hostinfo_local)

        claims = list(request.remote.authenticated_claims)
        if claims:
            text.append("Authenticated claims of the client: %s." % ", ".join(repr(c) for c in claims))
        else:
            text.append("No claims authenticated.")
        print("Discovery: ".join(text))
        return aiocoap.Message(content_format=0,
                payload="Discovered".encode('utf8'))


logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.INFO)

async def main():
    root = resource.Site()

    root.add_resource(['discovery'], Discovery())

    port = int(environ.get('PORT', 5000))
    print(type(port), port)
    external_ip = environ.get('IP', "localhost")
    print(type(external_ip), external_ip)
    await aiocoap.Context.create_server_context(root, bind = (external_ip, port))
    print("Setup complete\n")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())