"""Low-impact Minecraft Java and Bedrock status probes."""

from __future__ import annotations

import json
import os
import socket
import struct
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_PACKET = 1_048_576


@dataclass(frozen=True)
class Finding:
    severity: str
    title: str
    evidence: str
    recommendation: str


@dataclass
class AuditReport:
    target: str
    edition: str
    port: int
    timestamp: str
    online: bool
    latency_ms: float | None
    server: dict[str, Any]
    findings: list[Finding]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["findings"] = [asdict(item) for item in self.findings]
        return value


def parse_target(value: str, edition: str) -> tuple[str, int]:
    default_port = 25565 if edition == "java" else 19132
    raw = value.strip()
    if raw.startswith("[") and "]" in raw:
        end = raw.index("]")
        host = raw[1:end]
        suffix = raw[end + 1 :]
        return host, int(suffix[1:]) if suffix.startswith(":") else default_port
    if raw.count(":") == 1:
        host, port_text = raw.rsplit(":", 1)
        if port_text.isdigit():
            port = int(port_text)
            if not 1 <= port <= 65535:
                raise ValueError("port must be between 1 and 65535")
            return host, port
    if not raw:
        raise ValueError("target is empty")
    return raw, default_port


def audit_server(target: str, edition: str = "java", timeout: float = 3.0) -> AuditReport:
    edition = edition.lower()
    if edition not in {"java", "bedrock"}:
        raise ValueError("edition must be java or bedrock")
    host, port = parse_target(target, edition)
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        if edition == "java":
            data, latency = _java_status(host, port, timeout)
            findings = _java_findings(data)
            server = _sanitize_java(data)
        else:
            data, latency = _bedrock_status(host, port, timeout)
            findings = _bedrock_findings(data)
            server = data
        return AuditReport(target=host, edition=edition, port=port, timestamp=timestamp,
                           online=True, latency_ms=latency, server=server, findings=findings)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return AuditReport(target=host, edition=edition, port=port, timestamp=timestamp,
                           online=False, latency_ms=None, server={}, findings=[], error=str(exc))


def save_report(report: AuditReport, directory: str | os.PathLike[str]) -> Path:
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_target = "".join(char if char.isalnum() or char in ".-" else "_" for char in report.target)
    path = output / f"audit_{safe_target}_{stamp}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _encode_varint(value: int) -> bytes:
    output = bytearray()
    value &= 0xFFFFFFFF
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(output)


def _recv_exact(connection: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = connection.recv(size - len(chunks))
        if not chunk:
            raise OSError("connection closed before the status packet completed")
        chunks.extend(chunk)
    return bytes(chunks)


def _read_varint(connection: socket.socket) -> int:
    value = 0
    for position in range(5):
        current = _recv_exact(connection, 1)[0]
        value |= (current & 0x7F) << (7 * position)
        if not current & 0x80:
            return value
    raise ValueError("invalid VarInt")


def _java_status(host: str, port: int, timeout: float) -> tuple[dict[str, Any], float]:
    encoded_host = host.encode("utf-8")
    handshake = (
        _encode_varint(0)
        + _encode_varint(769)
        + _encode_varint(len(encoded_host))
        + encoded_host
        + struct.pack(">H", port)
        + _encode_varint(1)
    )
    started = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.settimeout(timeout)
        connection.sendall(_encode_varint(len(handshake)) + handshake + b"\x01\x00")
        packet_length = _read_varint(connection)
        if packet_length <= 0 or packet_length > MAX_PACKET:
            raise ValueError("status packet size is outside the accepted limit")
        packet_id = _read_varint(connection)
        if packet_id != 0:
            raise ValueError(f"unexpected status packet id {packet_id}")
        json_length = _read_varint(connection)
        if json_length <= 0 or json_length > MAX_PACKET:
            raise ValueError("status JSON size is outside the accepted limit")
        payload = _recv_exact(connection, json_length)
    latency = round((time.perf_counter() - started) * 1000, 2)
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("status response is not an object")
    return value, latency


def _bedrock_status(host: str, port: int, timeout: float) -> tuple[dict[str, Any], float]:
    magic = bytes.fromhex("00ffff00fefefefefdfdfdfd12345678")
    client_guid = int.from_bytes(os.urandom(8), "big", signed=False)
    packet = b"\x01" + struct.pack(">Q", int(time.time() * 1000)) + magic + struct.pack(">Q", client_guid)
    started = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.settimeout(timeout)
        connection.sendto(packet, (host, port))
        response, _ = connection.recvfrom(4096)
    latency = round((time.perf_counter() - started) * 1000, 2)
    if len(response) < 35 or response[0] != 0x1C:
        raise ValueError("unexpected Bedrock pong packet")
    text_length = struct.unpack(">H", response[33:35])[0]
    text = response[35 : 35 + text_length].decode("utf-8", errors="replace")
    fields = text.split(";")
    names = ["edition", "motd", "protocol", "version", "players_online", "players_max",
             "server_id", "motd_secondary", "game_mode", "game_mode_id", "port_ipv4", "port_ipv6"]
    return {name: fields[index] for index, name in enumerate(names) if index < len(fields)}, latency


def _sanitize_java(data: dict[str, Any]) -> dict[str, Any]:
    players = data.get("players") if isinstance(data.get("players"), dict) else {}
    version = data.get("version") if isinstance(data.get("version"), dict) else {}
    sanitized = {
        "version": {"name": version.get("name"), "protocol": version.get("protocol")},
        "players": {"online": players.get("online"), "max": players.get("max")},
        "description": data.get("description"),
        "enforces_secure_chat": data.get("enforcesSecureChat"),
    }
    sample = players.get("sample")
    if isinstance(sample, list):
        sanitized["players"]["sample_count_redacted"] = len(sample)
    return sanitized


def _java_findings(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    players = data.get("players") if isinstance(data.get("players"), dict) else {}
    sample = players.get("sample")
    if isinstance(sample, list) and sample:
        findings.append(Finding(
            "low",
            "Player sample is exposed",
            f"The status response disclosed {len(sample)} sampled player record(s); names were redacted.",
            "Disable player samples if public player enumeration is not required.",
        ))
    if data.get("enforcesSecureChat") is False:
        findings.append(Finding(
            "info",
            "Secure chat is not enforced",
            "The Java status response reports enforcesSecureChat=false.",
            "Review enforce-secure-profile for the server version and deployment requirements.",
        ))
    if not findings:
        findings.append(Finding(
            "info",
            "No status-level exposure detected",
            "The single status response contained only normal service metadata.",
            "Continue with authenticated configuration review and plugin inventory.",
        ))
    return findings


def _bedrock_findings(data: dict[str, Any]) -> list[Finding]:
    return [Finding(
        "info",
        "Bedrock service metadata is public",
        f"The unconnected pong exposed version {data.get('version', 'unknown')} and player counts.",
        "Confirm that public discovery and MOTD disclosure match the server policy.",
    )]
