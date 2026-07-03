"""
base_transport.py — Abstract base class for chassis transport.

All transport implementations must provide:
  connect() → bool
  disconnect()
  is_connected() → bool
  send_command(command: BaseCommand) → bool
  read_feedback() → BaseFeedback
"""

from abc import ABC, abstractmethod
from ..protocol import BaseCommand, BaseFeedback


class BaseTransport(ABC):
    """Abstract transport interface."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the chassis. Return True on success."""
        ...

    @abstractmethod
    def disconnect(self):
        """Close the connection."""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the transport is currently connected."""
        ...

    @abstractmethod
    def send_command(self, command: BaseCommand) -> bool:
        """Send a command to the chassis. Return True on success."""
        ...

    @abstractmethod
    def read_feedback(self) -> BaseFeedback:
        """Read feedback from the chassis."""
        ...
