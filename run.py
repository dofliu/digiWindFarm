"""
Wind Farm Monitor Platform - Entry Point

Usage:
    python run.py                # Start backend (port from .env, default 8100)
    python run.py --port 9000    # Override port
"""

import sys
import os
import argparse
import socket

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))


def _load_dotenv():
    """Load .env file from project root into os.environ (no dependency needed)."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a TCP port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def _find_available_port(start: int, host: str = "0.0.0.0", max_tries: int = 10) -> int:
    """Find an available port starting from `start`, incrementing by 1."""
    for offset in range(max_tries):
        port = start + offset
        if _port_available(port, host):
            return port
    return start  # fallback


def main():
    _load_dotenv()

    default_port = int(os.environ.get("BACKEND_PORT", "8100"))
    default_host = os.environ.get("BACKEND_HOST", "0.0.0.0")
    modbus_port = int(os.environ.get("MODBUS_PORT", "5020"))

    parser = argparse.ArgumentParser(description="Wind Farm Monitor Platform")
    parser.add_argument("--port", type=int, default=default_port,
                        help=f"Server port (default: {default_port})")
    parser.add_argument("--host", type=str, default=default_host,
                        help=f"Server host (default: {default_host})")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload for development")
    parser.add_argument("--auto-port", action="store_true",
                        help="Auto-find available port if default is busy")
    args = parser.parse_args()

    port = args.port
    if not _port_available(port, args.host):
        if args.auto_port:
            old_port = port
            port = _find_available_port(port + 1, args.host)
            print(f"[run] Port {old_port} is busy, using {port} instead")
        else:
            print(f"[run] WARNING: Port {port} appears to be in use.")
            print(f"[run]   Use --auto-port to auto-select, or --port <N> to specify another.")

    # Export actual port so other code can reference it
    os.environ["BACKEND_PORT"] = str(port)

    print(f"[run] Starting backend on {args.host}:{port}")
    print(f"[run] Modbus TCP on port {modbus_port}")
    print(f"[run] Frontend should connect to http://localhost:{port}")

    import uvicorn
    uvicorn.run(
        "server.app:app",
        host=args.host,
        port=port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
