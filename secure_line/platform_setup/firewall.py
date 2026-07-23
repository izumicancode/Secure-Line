"""Best-effort local-firewall configuration for the discovery/chat ports.
Fails silently and prints a manual fallback rather than blocking
startup."""
import platform
import shutil
import subprocess

from ..constants import DISCOVERY_PORT, CHAT_PORT_BASE

_UDP_PORT = DISCOVERY_PORT
_TCP_RANGE = f"{CHAT_PORT_BASE}:{CHAT_PORT_BASE + 99}"
_TCP_RANGE_DASH = f"{CHAT_PORT_BASE}-{CHAT_PORT_BASE + 99}"


def try_configure_firewall():
    system = platform.system()

    if system == "Linux" and shutil.which("ufw"):
        try:
            status = subprocess.run(["sudo", "ufw", "status"], capture_output=True, text=True, timeout=20)
            output = (status.stdout or "") + (status.stderr or "")
            if "Status: active" in output:
                need_udp = f"{_UDP_PORT}/udp" not in output
                need_tcp = f"{_TCP_RANGE}/tcp" not in output
                if need_udp or need_tcp:
                    print("[line] ufw is active — opening required ports "
                          "(you may be asked for your sudo password)...")
                    if need_udp:
                        subprocess.run(["sudo", "ufw", "allow", f"{_UDP_PORT}/udp"], timeout=20)
                    if need_tcp:
                        subprocess.run(["sudo", "ufw", "allow", f"{_TCP_RANGE}/tcp"], timeout=20)
                    print("[line] firewall rules added.")
                else:
                    print("[line] ufw is active, required ports already allowed.")
            else:
                print("[line] ufw is installed but inactive — no changes needed.")
        except Exception as e:
            print(f"[line] Could not auto-configure ufw ({e}).")
            print("  Run manually if peers aren't found:")
            print(f"    sudo ufw allow {_UDP_PORT}/udp")
            print(f"    sudo ufw allow {_TCP_RANGE}/tcp")

    elif system == "Linux" and shutil.which("firewall-cmd"):
        try:
            active = subprocess.run(["sudo", "firewall-cmd", "--state"], capture_output=True,
                                     text=True, timeout=20)
            if "running" in (active.stdout or ""):
                print("[line] firewalld is active — opening required ports "
                      "(you may be asked for your sudo password)...")
                subprocess.run(["sudo", "firewall-cmd", f"--add-port={_UDP_PORT}/udp"], timeout=20)
                subprocess.run(["sudo", "firewall-cmd", f"--add-port={_TCP_RANGE_DASH}/tcp"], timeout=20)
                subprocess.run(["sudo", "firewall-cmd", f"--add-port={_UDP_PORT}/udp", "--permanent"], timeout=20)
                subprocess.run(["sudo", "firewall-cmd", f"--add-port={_TCP_RANGE_DASH}/tcp", "--permanent"], timeout=20)
                print("[line] firewall rules added.")
        except Exception as e:
            print(f"[line] Could not auto-configure firewalld ({e}).")
            print("  Run manually if peers aren't found:")
            print(f"    sudo firewall-cmd --add-port={_UDP_PORT}/udp --permanent")
            print(f"    sudo firewall-cmd --add-port={_TCP_RANGE_DASH}/tcp --permanent")
            print("    sudo firewall-cmd --reload")

    elif system == "Windows":
        try:
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                             "name=Line UDP", "dir=in", "action=allow",
                             "protocol=UDP", f"localport={_UDP_PORT}"], timeout=20, check=True)
            subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule",
                             "name=Line TCP", "dir=in", "action=allow",
                             "protocol=TCP", f"localport={_TCP_RANGE_DASH}"], timeout=20, check=True)
            print("[line] Windows Firewall rules added.")
        except Exception:
            print("[line] Could not auto-configure Windows Firewall "
                  "(needs an Administrator terminal). If peers aren't found, run this "
                  "script as Administrator once, or allow Python through Windows "
                  "Defender Firewall manually.")
    else:
        pass  # macOS generally prompts its own "allow incoming connections?" dialog
