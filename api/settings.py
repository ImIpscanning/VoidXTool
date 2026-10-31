"""Defaults for the optional local VoidXTool API."""


class APISettings:
    """Retained compatibility hook for callers in the original source."""

    DEFAULT_PORT = 8765

    def __init__(self) -> None:
        self.enabled = False
        self.port = self.DEFAULT_PORT

