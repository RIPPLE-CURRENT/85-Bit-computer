# Modular Intel 8085 Computer
<img width="1395" height="650" alt="github-original-logo" src="https://github.com/user-attachments/assets/e8988773-652f-4a6a-8cf0-3520545f9e69" />


A three-board, expandable 8-bit computer built around the Intel 8085, with TTL serial, PS/2 keyboard, two SNES controllers, and RP2040 VGA graphics and audio.

> **Status:** Architecture and address allocations agreed; electrical design and register details are preliminary. This is a design reference, not a manufacturing-ready schematic.

## System architecture

<img width="770" height="334" alt="image" src="https://github.com/user-attachments/assets/40f3316c-780f-4d07-b410-e2983e4f82bc" />


## Fixed 8085 memory map

All addresses hexadecimal. The 8085 has a 16-bit memory address bus and an independent 8-bit I/O address space.

<img width="458" height="336" alt="image" src="https://github.com/user-attachments/assets/1d9182b7-a357-40f5-85d2-852dab6e0b5b" />


The 8 KiB VRAM window is **not** the full video memory size. The RP2040 has 264 KiB internal SRAM in total; a preliminary target is **192 KiB shared video allocation**, equivalent to 24 × 8 KiB banks. Actual available capacity depends on firmware, framebuffers, tilemaps, sprites, and audio buffers.

### Proposed RAM conventions

| Address | Use |
|---|---|
| `8000–80FF` | 256 B software variable area (not a hardware zero page) |
| `8100–81FF` | System variables |
| `8200–EFFF` | General programs, buffers and BASIC workspace |
| `F000–FFFF` | Stack and system workspace (stack starts near top and grows downward) |

## Fixed I/O allocations

| Port | Device / function |
|---|---|
| `00` | 8251A data: receive/read, transmit/write |
| `01` | 8251A status/read, mode-command/write |
| `02–0F` | Reserved |
| `10` | 8255A #1 Port A |
| `11` | 8255A #1 Port B |
| `12` | 8255A #1 Port C |
| `13` | 8255A #1 control |
| `14` | 8255A #2 Port A |
| `15` | 8255A #2 Port B |
| `16` | 8255A #2 Port C |
| `17` | 8255A #2 control |
| `18–FF` | Reserved / expansion |

**All video and audio registers are memory-mapped, not I/O-mapped.** The 8251A and two 8255As are I/O-mapped.

## Board documentation

- [PCB 1 — CPU, ROM, RAM, reset and bus](docs/01-cpu-board.md)
- [PCB 2 — Serial, 8255s, keyboard and SNES](docs/02-io-board.md)
- [PCB 3 — RP2040 VGA, audio and VRAM](docs/03-video-audio.md)


