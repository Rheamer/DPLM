import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
import channels.exceptions as exceptions
from rest_framework import permissions
from .domain.interfaces import get_gateway_factory
from .domain.streams import AsyncStream


class AsyncReadView(AsyncWebsocketConsumer):
    def __init__(self):
        stream = AsyncStream()
        # TODO: put interface type here
        self.gateway = get_gateway_factory().get_instance()

    permission_classes = [permissions.IsAuthenticated]
    group_name: str = ''
    clientID: str = ''
    endpoint: str = ''

    @staticmethod
    def get_digestion(stream, loop):
        # TODO: how do i know these arguments?
        #  need some sort of abstraction to pass functions
        #  to mqtt callback handler
        def digestion(client, userdata, msg):
            task = asyncio.create_task(stream.push(msg))
            asyncio.run_coroutine_threadsafe(task, loop).result()
        return digestion

    async def connect(self):
        self.clientID = self.scope['url_route']['kwargs']['clientID']
        for head in self.scope['headers']:
            if head[0] == b'endpoint':
                self.endpoint = str(head[1])
        if self.endpoint == '':
            raise exceptions.DenyConnection
        self.group_name = self.clientID + self.endpoint
        self.gateway.connectStream(
            self.endpoint, self.clientID,
            digest_stream=self.get_digestion(
                self.stream,
                asyncio.get_running_loop())
        )
        await self.accept()
        self.gateway.dev_read(self.endpoint, self.clientID)
        data = await self.stream.read()
        await self.send(bytes_data=bytes(data))
        await self.disconnect(0)

    async def disconnect(self, close_code):
        # Leave room group
        self.gateway.disconnect_stream(clientID=self.clientID,
                                       endpoint=self.endpoint)
        await self.close()


class AsyncStreamViewConsumer(AsyncWebsocketConsumer):

    """ Whole view is useless for realtime data broadcast, unless multiprocessed """
    """ Deprecated """

    permission_classes = [permissions.IsAdminUser]

    async def connect(self):
        self.groupname = "Stream"
        clientID = self.scope['url_route']['kwargs']['clientID']
        for head in self.scope['headers']:
            if head[0] == b'endpoint':
                endpoint = str(head[1])
        self.stream_name = clientID + endpoint
        self.stream_group_name = f'stream_{self.stream_name}'
        self.gateway = get_gateway_factory().get_instance()
        await self.accept()
        self.gateway.connectStream(endpoint, clientID, self.stream_name)
        while (self.gateway.callbackAvailable(endpoint, clientID)):
            if not self.gateway.isEmptyStream(self.stream_name):
                data = self.gateway.pullStream(self.stream_name)
                await self.send(bytes_data=bytes(data))

    async def disconnect(self, close_code):
        # Leave room group
        self.gateway.disconnectStream(self.stream_name)
        await self.channel_layer.group_discard(
            self.stream_group_name,
        )
        await self.close()