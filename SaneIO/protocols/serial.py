import asyncio
import typing
from pathlib import Path

import serial
import serial_asyncio

from ..core import SIOTransport
from ..utils.asyncIO import AsyncIOSIOTransportServerConnectionAdapter


class AsyncSIO_UARTServer(AsyncIOSIOTransportServerConnectionAdapter):
	__slots__ = ("readyFut",)

	def __init__(self):
		super().__init__()
		self.readyFut = asyncio.Future()

	def prepare(self):
		self.transport.serial.read()
		self.readyFut.set_result(True)

	@property
	def lowestLevelResourceID(self) -> str:
		"""The unique lowest level stuff that the layer uniquiely takes. It can be a TCP or UDP port, or file descriptor. It is intended to be used as a key for muxers"""
		return self.transport.serial.port

	@classmethod
	# Async function because there are no async CTORs in python!
	async def create(cls, port: typing.Union[Path, str]):
		sioTransport = cls()
		coro = serial_asyncio.create_serial_connection(
			asyncio.get_event_loop(),
			lambda: sioTransport,
			port,
			# baudrate=9600,
			# bytesize=8,  # CS8
			# parity=serial.PARITY_EVEN,  # PARENB
			# stopbits=1,
		)
		transport, protocol = await coro
		await sioTransport.readyFut
		return sioTransport
