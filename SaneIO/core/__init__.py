import typing
from collections.abc import MutableMapping, MutableSequence
from queue import Queue
from warnings import warn

"""Python AsyncIO is complex shit. Let's wrap it a bit into a simple impl, detached from AsyncIO and IO in general, compatible to SansI/O fashion.
Design goals: be mimimalistic, simple and portable to different languages and architectures.
So composition over inheritance style is preferred..
"""


class SIOLayer:
	__slots__ = ("higher", "lower")

	def __init__(self):
		self.higher = None  # type: typing.Union["SIOResponder", "SIOSender"]
		self.lower = None  # type: "SIOTransport"

	def bindHigher(self, higher):
		self.higher = higher
		higher._bindLower(self)

	def unbindHigher(self, higher):
		self.higher._unbindLower(self)
		self.higher = None

	def _bindLower(self, lower: "SIOTransport"):
		self.lower = lower

	def _unbindLower(self, lower: "SIOTransport"):
		self.lower = None

	@property
	def lowestLevelResourceID(self) -> typing.Optional[typing.Any]:
		"""The unique lowest level stuff that the layer uniquiely takes. It can be a TCP or UDP port, or file descriptor. It is intended to be used as a key for muxers.
		`None` means the layer cannot be multiplexed. Usually it is because I have not invented a good way how to multiplex the lower level resources for now."""
		return self.lower.lowestLevelResourceID


class SIOResponder(SIOLayer):
	"""The entity that can receive data and return responses to them. Previous level is ALWAYS provided as a pointer. It cannot initiate connections itself."""

	__slots__ = ()

	def onReceive(self, lowerLevelTransport: "SIOTransport", data: bytes):
		raise NotImplementedError(self.__class__, "onReceive")


class SIOSender(SIOLayer):
	__slots__ = ()

	def sendBytes(self, data: bytes):
		raise NotImplementedError(self.__class__, "sendBytes")


class SIOTransport(SIOResponder, SIOSender):
	"""The entity that can unwrap the lower level of protocol into the higher level.
	Important: Servers also belong here.
	By default it just passes through to the lower and upper layers"""

	__slots__ = ()

	def onReceive(self, proto, commandRaw: bytes):
		return self.higher.onReceive(proto, commandRaw)

	def sendBytes(self, data: bytes):
		return self.lower.sendBytes(data)


class SIO1HiNLoMux(SIOTransport, MutableMapping):
	"""A multiplexor from higher level to lower ones.
	One higher level corresponds to multiple lower levels. All the messages sent from higher levels are copied to all the lower levels. Any message from any of lower levels is passed indiscriminately to higher levels."""

	__slots__ = ()

	def __init__(self):
		super().__init__()
		self.lower = {}

	def __getitem__(self, k):
		return self.lower[k]

	def __setitem__(self, k, v):
		self.lower[k] = v

	def __delitem__(self, k):
		del self.lower[k]

	def __iter__(self):
		return self.lower.keys()

	def __len__(self):
		return len(self.lower)

	def _bindLower(self, lower: "SIOTransport"):
		self[lower.lowestLevelResourceID] = lower

	def _unbindLower(self, lower: "SIOTransport"):
		del self[lower.lowestLevelResourceID]

	def lowestLevelResourceID(self):
		return None

	def onReceive(self, lowerLevelTransport: "SIOTransport", data: bytes):
		return self.higher.onReceive(self, data)

	def sendBytes(self, data: bytes):
		for el in self.lower.values():
			el.sendBytes(data)


class HigherMultiplexableSIOResponder(SIOResponder):
	"""A mixin class that defines the facilities needed to map raw bytes to upper levels"""

	__slots__ = ()

	def ifThisResponder(self, data: bytes):
		raise NotImplementedError


class SIONHi1LoMux(SIOTransport, MutableMapping):
	"""A multiplexor from lower level to higher ones.
	Multiple higher levels correspond to single lower level. All the messages received get through the upper level target identification. Then when the level is identified, the message is sent to it."""

	__slots__ = ()

	def __init__(self):
		super().__init__()
		self.higher = []

	def __getitem__(self, k):
		return self.higher[k]

	def __setitem__(self, k, v):
		self.higher[k] = v

	def __delitem__(self, k):
		del self.higher[k]

	def __iter__(self):
		return self.higher

	def __len__(self):
		return len(self.higher)

	def bindHigher(self, higher: HigherMultiplexableSIOResponder):
		self.higher.append(higher)

	def unbindHigher(self, higher: HigherMultiplexableSIOResponder):
		del self[a.index(higher)]

	def identifyHigherLevelTarget(self, data: bytes) -> HigherMultiplexableSIOResponder:
		for el in self:
			if el.ifThisResponder(data):
				return el

	def onReceive(self, lowerLevelTransport: SIOTransport, data: bytes):
		higherLevelTransport = self.identifyHigherLevelTarget(data)
		return higherLevelTransport.onReceive(self, data)

	def sendBytes(self, data: bytes):
		self.lower.sendBytes(data)


class HigherMultiplexableSIOResponder(SIOResponder):
	"""A mixin class that defines the facilities needed to map raw bytes to upper levels"""

	__slots__ = ()

	NHI_1LO_MUX_MARKER_BYTES = None  # type: bytes
	NHI_1LO_MUX_MARKER_POSITION = None  # type: slice

	@classmethod
	def getMarkerSlice(cls) -> slice:
		return slice(cls.NHI_1LO_MUX_MARKER_POSITION, cls.NHI_1LO_MUX_MARKER_POSITION + len(cls.NHI_1LO_MUX_MARKER_BYTES))

	def ifThisResponder(self, data: bytes):
		slc = self.__class__.getMarkerSlice()
		marker = data[slc]
		return marker == self.__class__.NHI_1LO_MUX_MARKER_BYTES


class SIOIdentificationBytesNHi1LoMux(SIONHi1LoMux):
	__slots__ = ("markBytesSlice",)

	def __init__(self, markBytesSlice: slice):
		self.markBytesSlice = markBytesSlice
		self.higher = {}

	def __iter__(self):
		return self.higher.values()

	def identifyHigherLevelTarget(self, data: bytes):
		marker = data[self.markBytesSlice]
		return self.higher[marker]

	def bindHigher(self, higher: HigherMultiplexableSIOResponder):
		assert higher.getMarkerSlice() != self.markBytesSlice, "This " + repr(higher) + " has incompatible location of marker slice: higher.getMarkerSlice() (" + higher.getMarkerSlice() + ") != self.markBytesSlice (" + self.markBytesSlice + ")"
		self[higher.NHI_1LO_MUX_MARKER_BYTES] = higher

	def unbindHigher(self, higher: HigherMultiplexableSIOResponder):
		del self[higher.NHI_1LO_MUX_MARKER_BYTES]


class UnsafelyMuxableSIO1HiNLoMux(SIO1HiNLoMux):
	"""A mux that can be muxed, but unsafely"""

	def lowestLevelResourceID(self):
		return id(self)


class HalfDuplex_SIOTransport(SIOTransport):
	"""The SIOTransport that works on byte-by-byte. These protocols usually use in-band signalling, so we have to handle them. So we process the input byte-by-byte."""

	__slots__ = ("tx",)

	immediateSend = True
	if not immediateSend:
		warn("Some software requires the responses to be sent within a strict time windows (50 ms by default, but no more than 999). If we delay sending using the queue (immediateSend = False), we don't fit this time window.")

	def __init__(self):
		super().__init__()
		self.tx = Queue()

	def canSend(self) -> bool:
		"""Determines if the remote party has finished its communication, so we can send own one"""
		raise NotImplementedError

	def sendCommandsInCertainStates(self):
		# print("self.inCommand", self.inCommand)
		if self.canSend():
			while not self.tx.empty():
				commandB = self.tx.get()
				# print("commandB", commandB)
				self.lower.sendBytes(commandB)
				self.tx.task_done()
				# print("written")

	def sendBytes(self, data: bytes):
		if self.__class__.immediateSend:
			return self.lower.sendBytes(data)
		else:
			self.tx.put(data)
			self.sendCommandsInCertainStates()


class StreamingHalfDuplexInBandSignalling_SIOTransport(HalfDuplex_SIOTransport):
	__slots__ = ()

	def receiveByte(self, b: int):
		raise NotImplementedError

	def filterSentBytes(self, b: bytes) -> bytes:
		raise NotImplementedError

	def onReceive(self, lowerLevelTransport: "SIOTransport", data: bytes):
		for b in data:
			self.receiveByte(b)

	def sendBytes(self, data: bytes):
		return super().sendBytes(self.filterSentBytes(data))
