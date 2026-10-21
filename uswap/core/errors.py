"""Exceptions raised by the conversion engines."""


class ConversionError(Exception):
    """A conversion failed (message is safe to show to the user)."""


class MissingDependency(ConversionError):
    """A required external tool or library is not installed."""

    def __init__(self, tool: str):
        super().__init__(tool)
        self.tool = tool


class Cancelled(ConversionError):
    """The conversion was cancelled by the user."""
