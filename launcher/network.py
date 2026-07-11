"""
Module: launcher.network

Purpose:
    Provide cross-platform utilities to detect TCP port availability and
    identify the PID currently occupying a port.

Responsibilities:
    - Probe a port with a non-blocking socket connect attempt.
    - Identify the owning PID via netstat, lsof, fuser, or ss.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Stateless.
"""

import socket
import sys
import subprocess

def check_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_pid_occupying_port(port: int) -> int | None:
    if sys.platform == "win32":
        try:
            output = subprocess.check_output('netstat -aon', shell=True, text=True)
            for line in output.splitlines():
                if "TCP" in line.upper():
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        local_addr = parts[1]
                        pid = parts[-1]
                        if (local_addr.endswith(f":{port}") or local_addr.endswith(f"]:{port}")) and pid.isdigit() and pid != "0":
                            return int(pid)
        except Exception:
            pass
    else:
        try:
            output = subprocess.check_output(f'lsof -t -i:{port}', shell=True, text=True)
            pids = output.strip().split()
            if pids:
                return int(pids[0])
        except Exception:
            try:
                output = subprocess.check_output(f'fuser {port}/tcp', shell=True, text=True)
                parts = output.strip().split()
                if parts:
                    return int(parts[-1])
            except Exception:
                try:
                    output = subprocess.check_output(f'ss -lptn "sport = :{port}"', shell=True, text=True)
                    import re
                    m = re.search(r'pid=(\d+)', output)
                    if m:
                        return int(m.group(1))
                except Exception:
                    pass
    return None
