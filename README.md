<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:09090F,50:6127C9,100:151325&height=220&section=header&text=VoidXTool&fontSize=64&fontColor=FFFFFF&animation=fadeIn&fontAlignY=38&desc=Minecraft%20Security%20Assessment%20Framework&descAlignY=59&descSize=18" alt="VoidXTool Header" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=19&duration=2600&pause=950&color=BDA4FF&center=true&vCenter=true&width=850&height=45&lines=Explore.+Inspect.+Audit.+Document.;Built+around+Minecraft+network+security.;Authorized+assessments+only.;Know+your+scope.+Protect+your+network." alt="VoidXTool Typing Animation" />

<p>
  <img src="https://img.shields.io/badge/Python-Project-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Version-3.2.0-6D39C5?style=for-the-badge" alt="Source Version" />
  <img src="https://img.shields.io/badge/Minecraft-Security%20Assessment-1F7A59?style=for-the-badge" alt="Minecraft Security" />
  <img src="https://img.shields.io/badge/Scope-Authorization%20Required-20212D?style=for-the-badge" alt="Authorization Required" />
</p>

**A modular Python project for reviewing Minecraft server and network security in authorized environments.**

[Repository](https://github.com/ImIpscanning/VoidXTool) · [Issues](https://github.com/ImIpscanning/VoidXTool/issues)

</div>

---

## Overview

**VoidXTool** is a Minecraft-focused security assessment project organized around a command system, network inspection utilities, configuration management, local logging, and authorization-aware workflows.

The public source includes code for inspecting server and network information, validating inputs, managing local settings, recording activity, and checking whether a target is within an explicitly defined assessment scope.

> **Important:** This repository is a **source snapshot**, not a verified, ready-to-run distribution. Some referenced application modules and external assets are absent from the public tree. Features mentioned below describe the source structure and registered interfaces; they are **not** a guarantee that every command is functional in this checkout.

> **Authorized use only:** Run security assessments solely against systems that you own or are explicitly permitted to test. Avoid disruptive activity against public servers and third-party infrastructure.

---

## What You'll Find

```txt
Minecraft-oriented server inspection
Network and DNS information utilities
Modular command registration and validation
Authorization scope checks
Local settings and language configuration
Session and authentication compatibility layer
Local logging and diagnostic records
Optional loopback-only status API
Update and installation support code
Windows and Linux filesystem path handling
```

---

## Project Focus

```diff
+ Understand Minecraft network exposure
+ Organize authorized security assessments
+ Verify scope before network-facing operations
+ Collect and review diagnostic information
+ Store local configuration and event logs
+ Support modular command development
+ Keep local API access limited to loopback
```

### What VoidXTool Is Not

```diff
- Permission to test infrastructure you do not own
- A guarantee that a server is secure
- A replacement for updates and backups
- A fully verified standalone release in this snapshot
- An invitation to run disruptive tests on public networks
```

---

## Architecture

The source is separated into focused components, allowing the command system, application lifecycle, security checks, and supporting utilities to be reviewed independently.

| Component | Role |
|---|---|
| `app.py` | Main application lifecycle, configuration loading, session creation, optional API startup |
| `cli.py` | Console entry point |
| `commands/` | Command loader, base command interface, argument validation |
| `security/` | Authorization scope policy and application integrity checks |
| `api/` | Optional local status service and defaults |
| `auth/` | Local session compatibility layer |
| `files/` | Settings, paths, local assets, installer helpers |
| `updater/` | Update-related modules |
| `utilities/` | Reusable application and network utilities |
| `logs.py` | Command-oriented log file management |
| `constants.py` | Version, language definitions, optional service URLs |

---

## Security Assessment Areas

### Server & Network Information

The command registry references modules for Minecraft server metadata, IP information, DNS records, subdomain inspection, and related network discovery tasks.

```txt
Server metadata
Network addressing
DNS information
Host and service inspection
Assessment diagnostics
```

### Minecraft Infrastructure

The source references Minecraft-specific networking and proxy concepts, including **Velocity** and **Waterfall**. These are areas for authorized configuration reviews; actual runtime support depends on the modules and assets present in a complete build.

### Application Management

The project also organizes general-purpose commands around settings, language selection, help, history, debugging, and local file maintenance.

### Restricted Operations

The registry contains names for intrusive or potentially disruptive testing functions. The scope policy classifies these separately and requires additional authorization settings. Such functions should be confined to approved, isolated lab environments; no intrusive usage procedures are provided here.

---

## Authorization & Scope Protection

VoidXTool includes a `ScopePolicy` implementation intended to evaluate network-facing commands against a local **`scope.json`** policy.

The policy checks for:

- An explicit ownership or authorization acknowledgement.
- A valid expiry date for the assessment.
- A list of authorized targets.
- Separate authorization controls for discovery, local listeners, sensitive-data queries, and disruptive testing.

The implementation denies protected operations when the scope is missing, malformed, expired, or does not include the requested target.

```txt
Select an authorized assessment
              ↓
Define ownership and permitted scope
              ↓
Review the assessment policy
              ↓
Validate the requested target
              ↓
Proceed only if authorized
              ↓
Document observations and remediation
```

> A local scope file is a technical safeguard, **not** a substitute for real permission from the system owner. Command-level enforcement should be tested before relying on it in production.

---

## Configuration

The source creates a default `settings.json` with settings such as:

```json
{
  "language": "en",
  "theme": "dark",
  "auto_update": false,
  "debug": false,
  "discordPresence": false,
  "serverStatusGetMode": "local",
  "serverShowMode": "default",
  "api": {
    "enabled": false,
    "port": 8765
  },
  "customports": [],
  "webhooks": []
}
```

The source also defines configuration entries for scanner executable names. The presence of these entries does **not** mean that their binaries are included in the repository.

### Optional Backend

VoidXTool does not assume a public backend. External service endpoints are derived only when an operator has provided a trusted `VOIDXTOOL_API_BASE_URL` environment setting.

The open-source authentication compatibility layer creates a **local session** without sending account credentials to a remote authentication service.

---

## Local Status API

An optional status API is implemented with Python's HTTP server classes.

```txt
Binding:   127.0.0.1 (loopback only)
Default:   port 8765
Endpoint:  GET /health
Response:  {"status":"ok","service":"voidxtool-local"}
```

The API is disabled in the default configuration. It is a local health endpoint, not a public management interface.

---

## Languages

Language identifiers declared in the current source:

| Language | Code |
|---|---|
| English | `en` |
| Spanish | `es` |
| Russian | `ru` |
| Urdu | `ur` |
| French | `fr` |
| Persian | `fa` |
| German | `de` |
| Portuguese | `pt` |
| Japanese | `ja` |

> Language support depends on the corresponding translation assets being available. Those assets are referenced by the source, but are not all distributed in this public snapshot.

---

## Local Data & Logs

The source uses platform-aware storage paths:

```txt
Windows:
%APPDATA%\VoidXToolData\

Linux:
~/.config/VoidXToolData/
```

Expected data includes configuration, language assets, and logs.

```txt
VoidXToolData/
├── settings.json
├── languages/        # When provided
├── logs.log           # Application log
└── logs/              # Per-command logs when created
```

`LogsManager` supports command-specific log folders and timestamped logs for selected operations. Treat logs as potentially sensitive: limit access, review retention, and avoid publishing infrastructure details or credentials.

---

## Source Layout

```txt
VoidXTool/
├── api/
├── auth/
├── commands/
├── files/
├── security/
├── updater/
├── utilities/
├── README.md
├── __init__.py
├── app.py
├── cli.py
├── constants.py
└── logs.py
```

### Source Snapshot Notice

The public tree currently lacks some modules imported by `app.py` and the command loader (for example, the `gui` package and `commands.command`). The project also references auxiliary assets supplied outside the repository.

Consequently, **a working installation or build cannot be guaranteed from these files alone**. Before publishing installation instructions, complete the missing dependencies and assets, add a reproducible dependency manifest, and test the documented startup process on supported operating systems.

---

## Development & Verification Checklist

```txt
[ ] Confirm that all imported Python packages are present
[ ] Add and lock dependency versions
[ ] Restore or replace missing application modules
[ ] Review any external assets before packaging
[ ] Test startup and shutdown on supported systems
[ ] Validate scope enforcement for each command
[ ] Keep disruptive capabilities disabled in safe defaults
[ ] Test local API binding and configuration
[ ] Verify log handling and data protection
[ ] Document a reproducible release process
```

---

## Technologies

<p align="center">
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="48" height="48" alt="Python" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/nodejs/nodejs-original.svg" width="48" height="48" alt="Node.js" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg" width="48" height="48" alt="Git" />
  <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg" width="48" height="48" alt="GitHub" />
</p>

**Primary implementation:** Python. **Referenced auxiliary runtime:** Node.js. The repository includes imports or references to libraries such as Rich, Loguru, Requests and EZJsonPy; a complete dependency specification is not currently included in the repository root.

---

## Responsible Use

Use VoidXTool in an isolated test network or another environment for which you have documented authorization. Set a clear testing scope, coordinate maintenance windows where appropriate, preserve diagnostic evidence responsibly, and disclose findings privately to the relevant administrators.

Security testing should help owners identify risk and improve protections—not interrupt other people's servers.

---

## Project Status

```diff
+ Python application entry point
+ Modular command registry and validation
+ Authorized-target scope policy
+ Local authentication compatibility layer
+ Platform-aware configuration paths
+ Optional local-only health API
+ Local logging utilities
+ Language identifiers and update scaffolding

! Public source snapshot requires integration work
! Some referenced modules and resources are unavailable
! Registered functionality has not been verified end-to-end
```

**Source version:** `3.2.0`, as declared in `constants.py`. This is not a claim that a packaged release has been verified.

**License:** No license file was visible in the public repository root at the time this README was prepared. Check with the author before assuming redistribution or modification rights.

---

## Author

Developed by **[ImIpscanning](https://github.com/ImIpscanning)**.

```txt
Inspect.
Understand.
Document.
Secure.
```

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=18&duration=2500&pause=1000&color=BDA4FF&center=true&vCenter=true&width=810&height=42&lines=Thanks+for+exploring+VoidXTool.;Built+for+responsible+Minecraft+security+research.;Know+your+scope.+Protect+your+network." alt="VoidXTool Footer" />

<strong>VoidXTool</strong> — Minecraft Security Assessment Framework

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:151325,50:6127C9,100:09090F&height=115&section=footer" alt="VoidXTool Footer Wave" />

</div>
