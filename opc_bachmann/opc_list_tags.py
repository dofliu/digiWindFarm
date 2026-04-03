#!/usr/bin/env python3
"""
Enumerate all readable OPC DA tags from a Bachmann server via OpenOPC2.

Use this to discover the exact item names before feeding them into `opc_client.py`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

from opc_common import connect


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List OPC tags (items) available on the configured server."
    )
    parser.add_argument(
        "--server",
        default="BACHMANN.Enterprise.2",
        help="OPC server prog-id (defaults to the Bachmann server from the doc).",
    )
    parser.add_argument(
        "--host",
        help="Hostname/IP of the OPC gateway (`OPC_GATEWAY_HOST` in openopc2/config.py).",
    )
    parser.add_argument(
        "--pattern",
        default="*",
        help="Wildcard pattern passed to OpenOPC.list (default '*').",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only list the immediate results for --pattern (skip deeper browsing).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the discovered tags (one per line).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def _call_opc_list(client, pattern: str, recursive: bool):
    """Try different OpenOPC.list signatures for compatibility."""
    attempts = [
        (pattern, {"recursive": recursive, "flat": True}),
        (pattern, {"recursive": recursive}),
        (pattern, {}),
    ]
    last_exc: Exception | None = None
    for pattern_arg, kwargs in attempts:
        try:
            logging.debug("Calling client.list(%s, %s)", pattern_arg, kwargs)
            return client.list(pattern_arg, **kwargs)
        except TypeError as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    raise RuntimeError("Unable to call OpenOPC.list with the supported signatures.")


def _normalize_entries(entries: Iterable) -> List[str]:
    """Turn OpenOPC list output into a list of fully qualified tag names."""
    normalized: List[str] = []
    for entry in entries or []:
        if isinstance(entry, (list, tuple)):
            if entry:
                normalized.append(str(entry[0]))
        else:
            normalized.append(str(entry))
    return normalized


def discover_tags(client, pattern: str, recursive: bool) -> List[str]:
    raw_entries = _call_opc_list(client, pattern, recursive=recursive)
    tags = _normalize_entries(raw_entries)
    if recursive and not tags and hasattr(client, "list"):
        logging.warning("No tags were returned. Try a narrower --pattern or --no-recursive.")
    unique_tags = sorted(dict.fromkeys(tags))
    return unique_tags


def write_output(tags: Sequence[str], output_path: str) -> None:
    path = Path(output_path)
    path.write_text("\n".join(tags), encoding="utf-8")
    logging.info("Saved %d tags to %s", len(tags), path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    client = connect(args.server, args.host)
    try:
        tags = discover_tags(client, args.pattern, recursive=not args.no_recursive)
    finally:
        try:
            client.close()
        except Exception:
            pass

    if not tags:
        logging.warning("No tags matched pattern %s", args.pattern)
        return 1

    for tag in tags:
        print(tag)

    if args.output:
        write_output(tags, args.output)
    logging.info("Discovered %d tags.", len(tags))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
