"""Local user session used by the open-source build.

The original project depended on a private authentication service which is no
longer part of this source distribution. The local session preserves the
attributes consumed by the command layer while avoiding credential transfer.
"""

from __future__ import annotations

import getpass
import hashlib
import os
import platform
import secrets


class Authentication:
    """Represent a local, non-networked VoidXTool session."""

    def __init__(self) -> None:
        self.username = os.getenv("VOIDXTOOL_USERNAME") or getpass.getuser() or "local-user"
        self.plan = "local"
        self.password = ""
        machine = f"{platform.node()}:{self.username}"
        self.system_code = hashlib.sha256(machine.encode("utf-8")).hexdigest()[:16]
        self._session_signature = secrets.token_hex(24)

    def login(self) -> bool:
        """Create a local session; no account or network request is required."""

        return True

