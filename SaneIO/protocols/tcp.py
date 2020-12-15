import asyncio
import typing
from pathlib import Path
from socket import AddressFamily

from ..core import SIOTransport
from ..utils.asyncIO import AsyncIOSIOMuxedTransportServerConnectionAdapter, AsyncIOSIOTransportServerAdapter


class AsyncSIO_TCPServerConnection(AsyncIOSIOMuxedTransportServerConnectionAdapter):
	__slots__ = ()

	@property
	def lowestLevelResourceID(self) -> str:
		"""The unique lowest level stuff that the layer uniquiely takes. It can be a TCP or UDP port, or file descriptor. It is intended to be used as a key for muxers"""
		t = self.transport
		return t.get_extra_info("sockname") + t.get_extra_info("peername")


class AsyncSIO_TCPServer(AsyncIOSIOTransportServerAdapter):
	__slots__ = ("mux", "server")

	CONNECTION_CLASS = AsyncSIO_TCPServerConnection

	@classmethod
	def SERVER_FACTORY(cls, protocolFactory, *args, **kwargs):
		l = asyncio.get_event_loop()
		s = l.create_server(protocolFactory, *args, **kwargs)
		return s
