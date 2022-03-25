from abc import abstractmethod, ABC
from asyncio import Queue as AioQueue
from asyncio import Lock as AioLock


class DigestionQueue(ABC):
    @abstractmethod
    def push(self, data):
        pass

    @abstractmethod
    def get_digestion(self) -> callable:
        pass


class AsyncStream:
    lock = AioLock()
    queue = AioQueue()

    async def push(self, data):
        await self.queue.put(data)

    async def read(self):
        await self.lock.acquire()
        await self.queue.get()
        self.lock.release()


class StreamManager(DigestionQueue):
    _streams = {str: AsyncStream}

    def get_stream(self, stream_name):
        if stream_name in self._streams:
            return self._streams[stream_name]
        else:
            stream = AsyncStream()
            self._streams[stream_name] = stream
            return stream

    def disconnect_stream(self, stream_name):
        if stream_name in self._streams:
            stream = self._streams[stream_name]
            self._streams.pop(stream_name)
            return stream
        else:
            return None



