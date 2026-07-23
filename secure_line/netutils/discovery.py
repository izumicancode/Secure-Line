"""LAN address discovery: enumerate this machine's local IPv4 addresses
and derive broadcast targets from them."""
import socket


def local_ips() -> set:
    """Best-effort gathering of every local IPv4 address we can find, so
    discovery works even on machines with multiple interfaces or with no
    real default route (offline / sandboxed / same-machine testing)."""
    ips = set()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            ips.add(ip)
    except OSError:
        pass
    ips.add("127.0.0.1")
    return ips


def broadcast_targets() -> list:
    targets = {"255.255.255.255", "127.255.255.255"}
    for ip in local_ips():
        parts = ip.split(".")
        if len(parts) == 4:
            targets.add(".".join(parts[:3]) + ".255")
    return list(targets)
