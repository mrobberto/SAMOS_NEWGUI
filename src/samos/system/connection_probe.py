"""RC1.1 non-destructive reachability checks for core SAMOS TCP servers.

A successful TCP handshake establishes only that the host/port is reachable.
It does NOT establish controller readiness, detector power, or DMD mirror state.
No instrument-protocol messages are sent.
"""

import socket
from concurrent.futures import ThreadPoolExecutor


CORE_SERVERS = ("PCM", "CCD", "DMD")


def parse_endpoint(address):
    """Parse a configured HOST:PORT value, raising ValueError on invalid input."""
    if not isinstance(address, str) or ":" not in address:
        raise ValueError("expected HOST:PORT")
    host, port_text = address.rsplit(":", 1)
    host = host.strip()
    if not host:
        raise ValueError("missing host")
    try:
        port = int(port_text)
    except (ValueError, TypeError):
        raise ValueError("invalid TCP port") from None
    if not (1 <= port <= 65535):
        raise ValueError("TCP port outside 1..65535")
    return host, port


def probe_one(address, timeout=1.5):
    """Return (reachable, diagnostic); never send an instrument command."""
    try:
        host, port = parse_endpoint(address)
        with socket.create_connection((host, port), timeout=timeout):
            return True, "TCP handshake succeeded"
    except (OSError, ValueError) as exc:
        return False, str(exc)


def probe_core_servers(addresses, timeout=1.5):
    """Probe PCM/CCD/DMD concurrently; returns a dict of (bool, diagnostic)."""
    with ThreadPoolExecutor(max_workers=len(CORE_SERVERS)) as pool:
        futures = {name: pool.submit(probe_one, addresses[name], timeout)
                   for name in CORE_SERVERS}
        return {name: futures[name].result() for name in CORE_SERVERS}
