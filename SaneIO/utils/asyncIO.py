import asyncio

from ..core import SIO1HiNLoMux, SIOSender, SIOTransport


class AsyncIOSIOTransportConnectionAdapter(asyncio.Protocol, SIOSender):
	"""A class to wrap `asyncio` transports and protocols.
	You must implement something:
		1. calling `self.higher.onReceive`
		2. calling `self.transport.write`
		3. property returning `lowestLevelResourceID` from the underlying resource"""

	__slots__ = ("transport",)

	def __init__(self, transport: asyncio.Transport = None):
		self.transport = transport

	###### Sans I/O callbacks######

	def sendBytes(self, data: bytes):
		self.transport.write(data)


class AsyncIOSIOTransportServerConnectionAdapter(AsyncIOSIOTransportConnectionAdapter):
	__slots__ = ()

	###### Asyncio I/O callbacks########

	def data_received(self, data: bytes):
		self.higher.onReceive(self, data)

	def connection_made(self, transport: asyncio.Transport):
		self.transport = transport
		self.prepare()

	def connection_lost(self, exc):
		self.transport.loop.stop()

	def eof_received(self):
		pass

	def pause_writing(self):
		pass

	def resume_writing(self):
		pass

	###############################

	def prepare(self):
		"""Sets the lower asyncio transport into a sane clean state"""
		pass


class AsyncIOSIOMuxedTransportServerConnectionAdapter(AsyncIOSIOTransportServerConnectionAdapter):
	__slots__ = ("mux",)

	def __init__(self, mux):
		super().__init__()
		self.mux = mux

	###### Asyncio I/O callbacks########

	def connection_made(self, transport: asyncio.Transport):
		self.transport = transport
		self.prepare()
		self.bindHigher(self.mux)

	def connection_lost(self, exc):
		self.unbindHigher(self.mux)


class AsyncIOSIOTransportServerAdapter(asyncio.Protocol):
	__slots__ = ("mux", "server")

	CONNECTION_CLASS = AsyncIOSIOMuxedTransportServerConnectionAdapter
	SERVER_FACTORY = None

	def __init__(self, mux: SIO1HiNLoMux):
		self.mux = mux
		self.server = None  # populated in factory

	@classmethod
	# Async function because there are no async CTORs in python!
	async def create(cls, mux: SIO1HiNLoMux, *args, **kwargs):
		sioServer = cls(mux)
		sioServer.server = await cls.SERVER_FACTORY(lambda: cls.CONNECTION_CLASS(mux), *args, **kwargs)
		await sioServer.server.start_serving()
		return sioServer
