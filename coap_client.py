import logging
import asyncio
import ipaddress

from aiocoap import *
from aiocoap.numbers.codes import Code as Method
from aiocoap.numbers.types import Type as Mtype
logging.basicConfig(level=logging.INFO)





async def main():
    protocol = await Context.create_client_context()
    while(True):
        try:
            request = Message(code=Method.PUT, payload=b"0",
                uri='coap://192.168.1.105/status/switch')
            response = await protocol.request(request).response
            print('Answer from: %s\n'%(response.code))

            request = Message(code=Method.GET, 
                uri='coap://192.168.1.105/status')
            response = await protocol.request(request).response
            print('Answer from: %s\n%r'%(response.code, response.payload))

            request = Message(code=Method.PUT, payload=b"crock",
                uri='coap://192.168.1.105/status/switch')
            response = await protocol.request(request).response
            print('Answer from: %s\n'%(response.code))

            request = Message(code=Method.PUT, payload=b"0",
                uri='coap://127.0.0.1/discovery')
            response = await protocol.request(request).response
            print('Answer from server: %s\n'%(response.code))
        except Exception as e:
            print('Failed to fetch resource:')
            print(e)
            

if __name__ == "__main__":
    asyncio.run(main())