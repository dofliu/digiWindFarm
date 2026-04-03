#!/usr/bin/env python3
"""
Shared helpers for OpenOPC-based utilities in this folder.

All scripts expect that the instructions from `OpenOPC...docx` were followed:
  * `pip install openopc2` inside a 32-bit Python environment.
  * `gbda_aut.dll` registered through `regsvr32` from the `openopc2/lib` folder.
  * `openopc2/config.py` patched with the Bachmann server prog-id and gateway IP.
"""

from __future__ import annotations

import logging


def import_openopc():
    """Import OpenOPC2/OpenOPC lazily so callers get clear guidance."""
    try:
        import OpenOPC2 as OpenOPC  # type: ignore
        return OpenOPC
    except ModuleNotFoundError:
        try:
            import OpenOPC  # type: ignore
            return OpenOPC
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise SystemExit(
                "OpenOPC2/OpenOPC is not installed. Install it with "
                "`pip install openopc2` and ensure gbda_aut.dll is registered."
            ) from exc


def connect(server: str, host: str | None):
    """Construct an OpenOPC client and connect to the requested server."""
    OpenOPC = import_openopc()
    client = OpenOPC.client()
    connect_args = (server,) if not host else (server, host)
    logging.info(
        "Connecting to OPC server %s%s",
        server,
        "" if not host else f" via gateway {host}",
    )
    client.connect(*connect_args)
    return client
