import ipaddress
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


PING_TIMEOUT_MS = 250
PORT_SCAN_TIMEOUT_S = 0.5
DEFAULT_PORTS = [21, 22, 23, 80, 443, 502, 3389]


@dataclass
class AdapterInfo:
    name: str
    ipv4: str
    mask: str
    gateway: Optional[str]

    def network(self) -> str:
        net = ipaddress.IPv4Network(f"{self.ipv4}/{self.mask}", strict=False)
        return str(net)

    def prefixlen(self) -> int:
        net = ipaddress.IPv4Network(f"{self.ipv4}/{self.mask}", strict=False)
        return net.prefixlen


def run(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)


def parse_ipconfig() -> List[AdapterInfo]:
    # Parse ipconfig output into adapter records with IPv4, mask, and gateway.
    out = run("ipconfig")
    adapters: List[AdapterInfo] = []

    name = None
    ipv4 = None
    mask = None
    gw = None
    reading_gw = False

    def flush():
        if name and ipv4 and mask:
            adapters.append(AdapterInfo(name=name, ipv4=ipv4, mask=mask, gateway=gw))

    for line in out.splitlines():
        if line and not line.startswith(" "):
            flush()
            name = line.strip().rstrip(":")
            ipv4 = mask = gw = None
            reading_gw = False
            continue

        if "IPv4 Address" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                ipv4 = m.group(1)
            reading_gw = False
        elif "Subnet Mask" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                mask = m.group(1)
            reading_gw = False
        elif "Default Gateway" in line:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                gw = m.group(1)
                reading_gw = False
            else:
                reading_gw = True
        elif reading_gw:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                gw = m.group(1)
                reading_gw = False

    flush()
    return adapters


def choose_adapter(adapters: List[AdapterInfo]) -> AdapterInfo:
    # Pick a usable adapter automatically when possible, otherwise prompt.
    if not adapters:
        raise RuntimeError("No IPv4 adapters found from ipconfig.")

    def is_link_local(ip: Optional[str]) -> bool:
        return bool(ip) and ip.startswith("169.254.")

    def is_private_ip(ip: str) -> bool:
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False

    usable = [
        a
        for a in adapters
        if a.gateway and not is_link_local(a.gateway) and a.prefixlen() < 32
    ]
    if len(usable) == 1:
        return usable[0]

    print("Multiple IPv4 adapters detected. Choose one:")
    for i, a in enumerate(adapters, start=1):
        gw = a.gateway if a.gateway else "none"
        hint = "private IP" if is_private_ip(a.ipv4) else "public/other IP"
        print(f"{i}) {a.name}  {a.ipv4}/{a.mask}  gw={gw}  ({hint})")

    while True:
        choice = input(f"Select 1-{len(adapters)}: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(adapters):
                return adapters[idx - 1]
        print("Invalid selection.")


def ping_sweep(subnet: str) -> None:
    # Ping every host in the subnet to populate the ARP cache.
    net = ipaddress.ip_network(subnet, strict=False)
    hosts = list(net.hosts())
    total = len(hosts)
    for idx, ip in enumerate(hosts, start=1):
        subprocess.run(
            f"ping -n 1 -w {PING_TIMEOUT_MS} {ip}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if idx == 1 or idx % 10 == 0 or idx == total:
            print(f"\rPing sweep: {idx}/{total} hosts", end="", flush=True)
    print()


def read_arp_table() -> Dict[str, str]:
    # Read Windows ARP cache and return IP -> MAC entries.
    out = run("arp -a")
    entries = {}
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith("Interface:") or line.startswith("Internet Address"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            ip, mac = parts[0], parts[1]
            if "-" in mac:
                entries[ip] = mac
    return entries


def parse_ports(raw: str) -> List[int]:
    # Parse comma/range input like "22,80,1000-1010".
    if not raw.strip():
        return DEFAULT_PORTS[:]
    ports: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            if start_s.isdigit() and end_s.isdigit():
                start, end = int(start_s), int(end_s)
                if start > end:
                    start, end = end, start
                ports.extend(range(start, end + 1))
        elif part.isdigit():
            ports.append(int(part))
    return sorted({p for p in ports if 1 <= p <= 65535})


def scan_ports(ip: str, ports: List[int]) -> List[int]:
    # Connect to each TCP port and report those that accept a connection.
    open_ports: List[int] = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(PORT_SCAN_TIMEOUT_S)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
    return open_ports


def detect_subnet() -> str:
    # Step 1: identify the local adapter/subnet that has internet access.
    adapter = choose_adapter(parse_ipconfig())
    subnet = adapter.network()
    print(f"Using adapter: {adapter.name} ({adapter.ipv4}/{adapter.mask})")
    print(f"Subnet detected: {subnet}")
    return subnet


def find_new_devices(subnet: str) -> List[str]:
    # Step 2: compare ARP tables before/after to find newly seen devices.
    print(f"Sweeping {subnet} to populate ARP cache...")
    ping_sweep(subnet)
    baseline = read_arp_table()
    print(f"Baseline captured: {len(baseline)} entries.")
    input("Connect new device, then press Enter to rescan...")

    time.sleep(2)
    ping_sweep(subnet)
    after = read_arp_table()

    new_entries = {ip: mac for ip, mac in after.items() if ip not in baseline}
    changed = {ip: mac for ip, mac in after.items() if ip in baseline and baseline[ip] != mac}

    print("\nNew devices:")
    for ip, mac in sorted(new_entries.items()):
        print(f"{ip:15}  {mac}")

    print("\nChanged MACs (same IP, different MAC):")
    for ip, mac in sorted(changed.items()):
        print(f"{ip:15}  {mac}")

    if not new_entries and not changed:
        print("\nNo new/changed entries found. Try repeating after another power-cycle.")
        return []

    return sorted(new_entries.keys())


def select_ip(candidates: List[str]) -> str:
    # Step 3 helper: choose an IP (newly found or manually entered).
    if not candidates:
        while True:
            raw = input("Enter IP to scan: ").strip()
            try:
                ipaddress.ip_address(raw)
                return raw
            except ValueError:
                print("Invalid IP.")
    if len(candidates) == 1:
        return candidates[0]

    print("Multiple IPs found. Choose one:")
    for i, ip in enumerate(candidates, start=1):
        print(f"{i}) {ip}")
    while True:
        choice = input(f"Select 1-{len(candidates)} or enter an IP: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1]
        try:
            ipaddress.ip_address(choice)
            return choice
        except ValueError:
            print("Invalid selection.")


def scan_ports_prompt(ip: str) -> None:
    # Step 3: scan user-selected TCP ports on the chosen IP.
    raw_ports = input("Enter ports (comma or range, blank for defaults): ").strip()
    ports = parse_ports(raw_ports)
    if not ports:
        print("No valid ports specified; skipping scan.")
        return
    open_ports = scan_ports(ip, ports)
    if open_ports:
        ports_str = ", ".join(str(p) for p in open_ports)
        print(f"{ip}: open ports -> {ports_str}")
    else:
        print(f"{ip}: no open ports found in selection")


def main() -> None:
    # Interactive menu to run step-by-step or all at once.
    subnet: Optional[str] = None
    last_ips: List[str] = []

    while True:
        print("\nSelect a step:")
        print("1) Detect internet-connected adapter/subnet")
        print("2) Identify new device on subnet")
        print("3) Scan ports on an IP")
        print("4) Run all steps")
        print("5) Quit")

        choice = input("Choice: ").strip()
        if choice == "1":
            subnet = detect_subnet()
        elif choice == "2":
            if not subnet:
                raw = input(
                    "Enter subnet (e.g. 192.168.0.0/24) or blank to auto-detect: "
                ).strip()
                subnet = raw if raw else detect_subnet()
            last_ips = find_new_devices(subnet)
        elif choice == "3":
            ip = select_ip(last_ips)
            scan_ports_prompt(ip)
        elif choice == "4":
            subnet = detect_subnet()
            last_ips = find_new_devices(subnet)
            if last_ips:
                ip = select_ip(last_ips)
                scan_ports_prompt(ip)
        elif choice == "5":
            return
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()
