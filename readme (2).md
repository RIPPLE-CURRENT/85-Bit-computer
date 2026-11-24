# 85-BIT Computer — Software

![CPU](https://img.shields.io/badge/CPU-Intel%208085-orange) ![Language](https://img.shields.io/badge/Language-8085%20Assembly-blue) ![Status](https://img.shields.io/badge/Status-Active%20Development-green)

## Overview

This directory contains the firmware, system software, utilities and applications developed for the **85-BIT Computer**, a modular 8-bit computer based on the Intel 8085 microprocessor.

Software can be developed and tested using the 85-BIT Intel 8085 Development Studio before deployment to physical hardware.

## Software index

| Project | Description | Status |
|---|---|---|
| [85-BIT Monitor](./85-BIT%20Monitor/) | BIOS and ROM monitor providing serial communication, memory inspection and editing, I/O access, Intel HEX loading, program execution and CPU register inspection. | V1.0 — Working in simulator |

## System memory map

| Address range | Size | Function |
|---|---:|---|
| `0000H–3FFFH` | 16 KiB | System ROM |
| `4000H–5FFFH` | 8 KiB | Expansion |
| `6000H–7FFFH` | 8 KiB | Bank-switched video RAM (planned) |
| `8000H–FDFFH` | 31.5 KiB | User program RAM |
| `FE00H–FEFFH` | 256 bytes | BIOS workspace |
| `FF00H–FFFFH` | 256 bytes | System stack |

## Software development

User applications should normally be assembled with an origin of `8000H` and exported in Intel HEX format. The ROM monitor provides a serial loader and a command to execute loaded programs. Applications can use the documented BIOS jump table for common services and return to the monitor using `RET` with a balanced stack.

Refer to the [85-BIT Monitor documentation](./85-BIT%20Monitor/) for the BIOS API, command reference and technical manuals.

## Future software

The following are potential additions to the software collection:

- BASIC interpreter
- Hardware diagnostic and test programs
- Serial communication utilities
- Graphics and sound demonstrations
- Games and general-purpose applications
- Reusable 8085 assembly libraries

## Project organisation

Each software project should have its own directory containing source code, documentation, version information and, where applicable, assembled binary or Intel HEX files.

[Return to the 85-BIT Computer repository](../)

---

<div align="center">

**85-BIT — Build it. Assemble it. Run it.**

</div>
