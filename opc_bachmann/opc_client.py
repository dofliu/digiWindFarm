#!/usr/bin/env python3
"""
Utility for reading live values from a Bachmann OPC DA server via OpenOPC2.

This script follows the setup instructions captured in `OpenOPC...docx`:
  * Install the 32-bit `openopc2` Python package (`pip install openopc2`).
  * Register `gbda_aut.dll` inside the `openopc2/lib` folder (`regsvr32 gbda_aut.dll`).
  * Update `OPC_SERVER`/`OPC_GATEWAY_HOST` in `openopc2/config.py` so they match
    the Bachmann server (defaulting to `BACHMANN.Enterprise.2`) and the gateway IP.

Once that plumbing is in place, run this module to connect to the OPC server and
poll one or more items/tags.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence

from opc_common import connect


def _load_items(args: argparse.Namespace) -> List[str]:
    """Aggregate OPC item names from CLI flags and optional files."""
    items: List[str] = []
    if args.items:
        items.extend(args.items)
    if args.items_file:
        text = Path(args.items_file).read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            items.append(line)
    items = [item for item in items if item]
    if not items:
        raise SystemExit(
            "No OPC items were provided. Use --items TAG1 TAG2 or --items-file path."
        )
    return items


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect to a Bachmann OPC DA server via OpenOPC2 and read tags."
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
        "--items",
        nargs="*",
        help="One or more OPC item/tag names to read (can repeat).",
    )
    parser.add_argument(
        "--items-file",
        help="Plain-text file with additional OPC items (one per line, # for comments).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.0,
        help="Seconds between polling iterations (0 = single read).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="How many times to poll (0 = run forever until Ctrl+C).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON rows instead of human-readable text.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity.",
    )
    args = parser.parse_args(argv)
    args.items = _load_items(args)
    if args.count == 0 and args.interval <= 0:
        parser.error("--count 0 requires --interval > 0 to avoid a tight loop.")
    return args


def _read_item(client, item: str) -> dict:
    """Read a single OPC item and normalize the payload."""
    try:
        value, quality, timestamp = client.read(item)
        return {
            "item": item,
            "value": value,
            "quality": quality,
            "timestamp": timestamp,
        }
    except Exception as exc:  # noqa: BLE001 - show OPC faults verbatim
        logging.error("Failed to read %s: %s", item, exc)
        return {"item": item, "error": str(exc)}


def _emit_json(iteration: int, rows: Sequence[dict]) -> None:
    payload = {
        "iteration": iteration,
        "polled_at": time.time(),
        "rows": rows,
    }
    print(json.dumps(payload, ensure_ascii=False))


def _emit_text(iteration: int, rows: Sequence[dict]) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{timestamp}] Iteration {iteration}")
    for row in rows:
        if "error" in row:
            print(f"  {row['item']}: ERROR - {row['error']}")
        else:
            print(
                f"  {row['item']}: value={row['value']} "
                f"quality={row['quality']} timestamp={row['timestamp']}"
            )


def poll(client, items: Iterable[str], *, count: int, interval: float, as_json: bool):
    """Poll the requested OPC items count times."""
    iteration = 0
    while True:
        iteration += 1
        rows = [_read_item(client, item) for item in items]
        if as_json:
            _emit_json(iteration, rows)
        else:
            _emit_text(iteration, rows)

        if count and iteration >= count:
            break
        if interval > 0:
            time.sleep(interval)
        else:
            continue


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    client = connect(args.server, args.host)
    try:
        poll(
            client,
            args.items,
            count=args.count,
            interval=args.interval,
            as_json=args.json,
        )
    finally:
        try:
            client.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
