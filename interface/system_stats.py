"""CPU / RAM / disk / network sampling with no required third-party packages.

Uses psutil when present, otherwise platform-specific standard-library calls.
Every function degrades to None rather than raising."""
import os
import platform
import shutil
import sys
import time

_IS_WIN = platform.system() == "Windows"
try:
    import psutil  # optional
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


# ---------- CPU ----------
def _cpu_times():
    if _IS_WIN:
        import ctypes
        from ctypes import wintypes
        idle, kernel, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel),
                                                     ctypes.byref(user)):
            return None
        def ft(f):
            return (f.dwHighDateTime << 32) | f.dwLowDateTime
        i, k, u = ft(idle), ft(kernel), ft(user)
        return i, k + u  # kernel already includes idle on Windows
    try:
        with open("/proc/stat") as f:
            parts = [int(x) for x in f.readline().split()[1:]]
    except OSError:
        return None
    idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
    total = sum(parts)
    return idle, total


_last_cpu = None


def cpu_percent() -> float:
    """CPU busy percentage since the previous call."""
    global _last_cpu
    if _HAS_PSUTIL:
        return float(psutil.cpu_percent(interval=None))
    now = _cpu_times()
    if now is None:
        return None
    if _last_cpu is None:
        _last_cpu = now
        if _IS_WIN:
            _last_cpu = now
        time.sleep(0.05)
        return 0.0
    idle0, total0 = _last_cpu
    idle1, total1 = now
    _last_cpu = now
    d_total = total1 - total0
    if d_total <= 0:
        return 0.0
    return max(0.0, min(100.0, 100.0 * (1 - (idle1 - idle0) / d_total)))


# ---------- RAM ----------
def memory() -> dict:
    if _HAS_PSUTIL:
        vm = psutil.virtual_memory()
        return {"total": vm.total, "used": vm.total - vm.available,
                "percent": vm.percent}
    if _IS_WIN:
        import ctypes

        class MEMSTATUS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = MEMSTATUS()
        st.dwLength = ctypes.sizeof(MEMSTATUS)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return None
        used = st.ullTotalPhys - st.ullAvailPhys
        return {"total": st.ullTotalPhys, "used": used, "percent": float(st.dwMemoryLoad)}
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, _, rest = line.partition(":")
                info[key] = int(rest.split()[0]) * 1024
        total, avail = info["MemTotal"], info["MemAvailable"]
        used = total - avail
        return {"total": total, "used": used, "percent": 100.0 * used / total}
    except (OSError, KeyError, ValueError):
        return None


# ---------- disk ----------
def disk(path: str = None) -> dict:
    try:
        target = path or (os.environ.get("SystemDrive", "C:\\") if _IS_WIN else "/")
        usage = shutil.disk_usage(target)
        return {"total": usage.total, "used": usage.used, "free": usage.free,
                "percent": 100.0 * usage.used / usage.total}
    except OSError:
        return None


# ---------- network ----------
def _net_bytes():
    if _HAS_PSUTIL:
        c = psutil.net_io_counters()
        return c.bytes_recv, c.bytes_sent
    if _IS_WIN:
        return _net_bytes_windows()
    try:
        recv = sent = 0
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                name, _, rest = line.partition(":")
                if name.strip() == "lo":
                    continue
                cols = rest.split()
                recv += int(cols[0])
                sent += int(cols[8])
        return recv, sent
    except (OSError, IndexError, ValueError):
        return None


def _net_bytes_windows():
    """Sum IPv4/IPv6 bytes via GetIfTable2; returns None if the layout differs."""
    try:
        import ctypes
        from ctypes import wintypes

        class MIB_IF_ROW2(ctypes.Structure):
            _fields_ = [("InterfaceLuid", ctypes.c_ulonglong),
                        ("InterfaceIndex", wintypes.DWORD),
                        ("InterfaceGuid", ctypes.c_byte * 16),
                        ("Alias", wintypes.WCHAR * 257),
                        ("Description", wintypes.WCHAR * 257),
                        ("PhysicalAddressLength", wintypes.DWORD),
                        ("PhysicalAddress", ctypes.c_byte * 32),
                        ("PermanentPhysicalAddress", ctypes.c_byte * 32),
                        ("Mtu", wintypes.DWORD), ("Type", wintypes.DWORD),
                        ("TunnelType", wintypes.DWORD), ("MediaConnectState", wintypes.DWORD),
                        ("MediaDuplexState", wintypes.DWORD),
                        ("TransmitLinkSpeed", ctypes.c_ulonglong),
                        ("ReceiveLinkSpeed", ctypes.c_ulonglong),
                        ("InOctets", ctypes.c_ulonglong), ("InUcastPkts", ctypes.c_ulonglong),
                        ("InNUcastPkts", ctypes.c_ulonglong), ("InDiscards", ctypes.c_ulonglong),
                        ("InErrors", ctypes.c_ulonglong), ("InUnknownProtos", ctypes.c_ulonglong),
                        ("InUcastOctets", ctypes.c_ulonglong), ("InMulticastOctets", ctypes.c_ulonglong),
                        ("InBroadcastOctets", ctypes.c_ulonglong), ("OutOctets", ctypes.c_ulonglong),
                        ("OutUcastPkts", ctypes.c_ulonglong), ("OutNUcastPkts", ctypes.c_ulonglong),
                        ("OutDiscards", ctypes.c_ulonglong), ("OutErrors", ctypes.c_ulonglong),
                        ("OutUcastOctets", ctypes.c_ulonglong), ("OutMulticastOctets", ctypes.c_ulonglong),
                        ("OutBroadcastOctets", ctypes.c_ulonglong), ("OutQLen", ctypes.c_ulonglong)]

        table = ctypes.POINTER(ctypes.c_void_p)()
        if ctypes.windll.iphlpapi.GetIfTable2(ctypes.byref(table)) != 0:
            return None
        # MIB_IF_TABLE2 = {ULONG NumEntries; MIB_IF_ROW2 Table[1];}
        num = ctypes.cast(table, ctypes.POINTER(ctypes.c_ulong)).contents.value
        base = ctypes.addressof(table.contents) + ctypes.sizeof(ctypes.c_ulong)
        row_size = ctypes.sizeof(MIB_IF_ROW2)
        recv = sent = 0
        for i in range(min(num, 256)):
            row = MIB_IF_ROW2.from_address(base + i * row_size)
            recv += row.InOctets
            sent += row.OutOctets
        ctypes.windll.iphlpapi.FreeMibTable(table)
        return recv, sent
    except Exception:
        return None


_last_net = None


def network_rates() -> dict:
    """Download/upload bytes per second since the previous call."""
    global _last_net
    now_bytes = _net_bytes()
    if now_bytes is None:
        return None
    now_t = time.time()
    if _last_net is None:
        _last_net = (now_bytes, now_t)
        return {"down_bps": 0.0, "up_bps": 0.0}
    (prev_bytes, prev_t) = _last_net
    dt = max(1e-6, now_t - prev_t)
    _last_net = (now_bytes, now_t)
    return {"down_bps": max(0.0, (now_bytes[0] - prev_bytes[0]) / dt),
            "up_bps": max(0.0, (now_bytes[1] - prev_bytes[1]) / dt)}


def snapshot() -> dict:
    mem = memory() or {}
    net = network_rates() or {}
    return {"cpu": cpu_percent(), "mem_percent": mem.get("percent"),
            "mem_used": mem.get("used"), "mem_total": mem.get("total"),
            "disk_percent": (disk() or {}).get("percent"),
            "disk_free": (disk() or {}).get("free"),
            "down_bps": net.get("down_bps"), "up_bps": net.get("up_bps")}


def human_bytes(n, suffix: str = "") -> str:
    if n is None:
        return "n/a"
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}{suffix}"
        n /= 1024
    return f"{n:.1f} TB{suffix}"
