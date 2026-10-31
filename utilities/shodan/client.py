"""Read-only Shodan host lookup with NVD summaries and Exploit-DB pivots."""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

SHODAN_HOST_ENDPOINT = "https://api.shodan.io/shodan/host/{ip}"
SHODAN_INTERNETDB_ENDPOINT = "https://internetdb.shodan.io/{ip}"
NVD_CVE_ENDPOINT = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class ShodanClientError(RuntimeError):
    """Safe user-facing error that never contains an API key."""


@dataclass(frozen=True)
class VulnerabilityFinding:
    cve: str
    severity: str
    cvss: float | None
    explanation: str
    services: tuple[str, ...]
    exploit_db_url: str
    source: str


@dataclass
class ShodanReport:
    queried_target: str
    resolved_ip: str
    timestamp: str
    organization: str | None
    operating_system: str | None
    country: str | None
    ports: list[int]
    last_update: str | None
    total_cves: int
    findings: list[VulnerabilityFinding]
    omitted_cves: list[str]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["findings"] = [asdict(finding) for finding in self.findings]
        return value


class ShodanVulnerabilityClient:
    """Use Shodan's cached host data; no scan request is submitted."""

    def __init__(
        self,
        shodan_api_key: str,
        nvd_api_key: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._shodan_key = shodan_api_key.strip() or None
        self._nvd_key = nvd_api_key.strip() if nvd_api_key else None
        self._session = session or requests.Session()
        self._timeout = timeout

    def inspect(self, target: str, detail_limit: int = 10) -> ShodanReport:
        if not 1 <= detail_limit <= 25:
            raise ShodanClientError("The detail limit must be between 1 and 25.")
        resolved_ip = resolve_target(target)
        payload = self._get_shodan_host(resolved_ip)
        evidence = _collect_vulnerabilities(payload)
        ordered_cves = sorted(evidence, key=_cve_sort_key, reverse=True)

        findings: list[VulnerabilityFinding] = []
        for cve in ordered_cves[:detail_limit]:
            item = evidence[cve]
            metadata = item["metadata"]
            explanation = _first_text(metadata, "summary", "description")
            cvss = _parse_score(metadata.get("cvss"))
            severity = _severity_from_score(cvss)
            source = "Shodan"

            if not explanation or cvss is None:
                nvd = self._get_nvd_cve(cve)
                if nvd:
                    explanation = explanation or nvd.get("description")
                    cvss = cvss if cvss is not None else nvd.get("cvss")
                    severity = nvd.get("severity") or _severity_from_score(cvss)
                    source = "Shodan + NVD"

            findings.append(VulnerabilityFinding(
                cve=cve,
                severity=severity,
                cvss=cvss,
                explanation=_shorten(explanation or "No public description was returned.", 320),
                services=tuple(sorted(item["services"])),
                exploit_db_url=exploit_db_url(cve),
                source=source,
            ))

        ports = sorted({
            int(port)
            for port in payload.get("ports", [])
            if isinstance(port, int) or (isinstance(port, str) and port.isdigit())
        })
        return ShodanReport(
            queried_target=target,
            resolved_ip=resolved_ip,
            timestamp=datetime.now(timezone.utc).isoformat(),
            organization=_optional_text(payload.get("org")),
            operating_system=_optional_text(payload.get("os")),
            country=_optional_text(payload.get("country_name")),
            ports=ports,
            last_update=_optional_text(payload.get("last_update")),
            total_cves=len(ordered_cves),
            findings=findings,
            omitted_cves=ordered_cves[detail_limit:],
        )

    def _get_shodan_host(self, ip: str) -> dict[str, Any]:
        endpoint = (
            SHODAN_HOST_ENDPOINT.format(ip=quote(ip, safe=":"))
            if self._shodan_key
            else SHODAN_INTERNETDB_ENDPOINT.format(ip=quote(ip, safe=":"))
        )
        params = {"key": self._shodan_key, "minify": "false"} if self._shodan_key else None
        try:
            response = self._session.get(
                endpoint,
                params=params,
                timeout=self._timeout,
                headers={"Accept": "application/json", "User-Agent": "VoidXTool/3.2"},
            )
        except requests.RequestException as exc:
            raise ShodanClientError("Shodan could not be reached.") from exc

        if response.status_code in {401, 403}:
            raise ShodanClientError("Shodan rejected the API key or account permissions.")
        if response.status_code == 404:
            raise ShodanClientError("Shodan has no host record for this IP.")
        if response.status_code == 429:
            raise ShodanClientError("Shodan rate limit reached. Try again later.")
        if response.status_code != 200:
            raise ShodanClientError(f"Shodan returned HTTP {response.status_code}.")
        return _safe_json_object(response, "Shodan")

    def _get_nvd_cve(self, cve: str) -> dict[str, Any] | None:
        headers = {"Accept": "application/json", "User-Agent": "VoidXTool/3.2"}
        if self._nvd_key:
            headers["apiKey"] = self._nvd_key
        try:
            response = self._session.get(
                NVD_CVE_ENDPOINT,
                params={"cveId": cve},
                timeout=self._timeout,
                headers=headers,
            )
        except requests.RequestException:
            return None
        if response.status_code != 200:
            return None
        try:
            payload = _safe_json_object(response, "NVD")
        except ShodanClientError:
            return None
        vulnerabilities = payload.get("vulnerabilities")
        if not isinstance(vulnerabilities, list) or not vulnerabilities:
            return None
        cve_data = vulnerabilities[0].get("cve", {})
        if not isinstance(cve_data, dict):
            return None
        return _parse_nvd_cve(cve_data)


def resolve_target(target: str) -> str:
    candidate = target.strip().strip("[]")
    if not candidate or "/" in candidate:
        raise ShodanClientError("Provide one hostname or IP address, not a network range.")
    if candidate.count(":") == 1:
        host, possible_port = candidate.rsplit(":", 1)
        if possible_port.isdigit():
            candidate = host
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        pass
    try:
        answers = socket.getaddrinfo(candidate, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ShodanClientError("The target hostname could not be resolved.") from exc
    addresses = sorted({str(ipaddress.ip_address(item[4][0])) for item in answers})
    if not addresses:
        raise ShodanClientError("The target hostname did not resolve to an IP address.")
    return sorted(addresses, key=lambda value: ipaddress.ip_address(value).version)[0]


def exploit_db_url(cve: str) -> str:
    return f"https://www.exploit-db.com/search?cve={quote(cve.upper(), safe='-')}"


def save_report(report: ShodanReport, directory: str | Path) -> Path:
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_ip = report.resolved_ip.replace(":", "_")
    path = output / f"shodan_{safe_ip}_{stamp}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _collect_vulnerabilities(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}

    def add(raw_cve: object, metadata: object = None, service: str | None = None) -> None:
        cve = str(raw_cve).upper()
        if not CVE_PATTERN.fullmatch(cve):
            return
        record = evidence.setdefault(cve, {"metadata": {}, "services": set()})
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if key not in record["metadata"] and isinstance(value, (str, int, float, bool)):
                    record["metadata"][key] = value
        if service:
            record["services"].add(service)

    _consume_vulnerability_value(payload.get("vulns"), add, None)
    services = payload.get("data")
    if isinstance(services, list):
        for item in services:
            if not isinstance(item, dict):
                continue
            port = item.get("port")
            transport = item.get("transport") or "tcp"
            product = item.get("product")
            label = f"{port}/{transport}" if port is not None else str(transport)
            if product:
                label += f" · {product}"
            _consume_vulnerability_value(item.get("vulns"), add, label)
    return evidence


def _consume_vulnerability_value(value: object, add, service: str | None) -> None:
    if isinstance(value, dict):
        for cve, metadata in value.items():
            add(cve, metadata, service)
    elif isinstance(value, list):
        for cve in value:
            add(cve, None, service)


def _parse_nvd_cve(cve_data: dict[str, Any]) -> dict[str, Any]:
    description = None
    descriptions = cve_data.get("descriptions")
    if isinstance(descriptions, list):
        english = [item.get("value") for item in descriptions if item.get("lang") == "en"]
        other = [item.get("value") for item in descriptions]
        description = next((text for text in [*english, *other] if isinstance(text, str)), None)

    metrics = cve_data.get("metrics") if isinstance(cve_data.get("metrics"), dict) else {}
    for family in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(family)
        if not isinstance(entries, list) or not entries:
            continue
        cvss_data = entries[0].get("cvssData", {})
        score = _parse_score(cvss_data.get("baseScore"))
        severity = _optional_text(cvss_data.get("baseSeverity"))
        if not severity:
            severity = _optional_text(entries[0].get("baseSeverity"))
        return {"description": description, "cvss": score, "severity": (severity or "unknown").lower()}
    return {"description": description, "cvss": None, "severity": "unknown"}


def _safe_json_object(response: requests.Response, source: str) -> dict[str, Any]:
    content = response.content
    if len(content) > MAX_RESPONSE_BYTES:
        raise ShodanClientError(f"{source} response exceeded the size limit.")
    try:
        value = response.json()
    except ValueError as exc:
        raise ShodanClientError(f"{source} returned invalid JSON.") from exc
    if not isinstance(value, dict):
        raise ShodanClientError(f"{source} returned an unexpected response.")
    return value


def _cve_sort_key(cve: str) -> tuple[int, int]:
    _, year, number = cve.split("-", 2)
    return int(year), int(number)


def _first_text(values: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _optional_text(values.get(key))
        if value:
            return value
    return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_score(value: object) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if 0 <= score <= 10 else None


def _severity_from_score(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 9:
        return "critical"
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _shorten(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1].rstrip() + "…"
