# Modular Intel 8085 Computer
<p align="center">
<img width="1395" height="650" alt="github-original-logo" src="https://github.com/user-attachments/assets/e8988773-652f-4a6a-8cf0-3520545f9e69" />
</p>
A three-board, expandable 8-bit computer built around the Intel 8085, with TTL serial, PS/2 keyboard, two SNES controllers, and RP2040 VGA graphics and audio.


## System architecture
<p align="center">
<img width="770" height="334" alt="image" src="https://github.com/user-attachments/assets/40f3316c-780f-4d07-b410-e2983e4f82bc" />
</p>

## Fixed 8085 memory map

All addresses hexadecimal. The 8085 has a 16-bit memory address bus and an independent 8-bit I/O address space.
<p align="center">
<img width="458" height="336" alt="image" src="https://github.com/user-attachments/assets/1d9182b7-a357-40f5-85d2-852dab6e0b5b" />
</p>
The 8 Kb VRAM window is **not** the full video memory size. The RP2040 has 264 KiB internal SRAM in total; a preliminary target is **192 Kb shared video allocation**, equivalent to 24 × 8 Kb banks. Actual available capacity depends on firmware, framebuffers, tilemaps, sprites, and audio buffers.

### Proposed RAM conventions

| Address | Use |
|---|---|
| `8000–80FF` | 256 B software variable area (not a hardware zero page) |
| `8100–81FF` | System variables |
| `8200–EFFF` | General programs, buffers and BASIC workspace |
| `F000–FFFF` | Stack and system workspace (stack starts near top and grows downward) |

## Fixed Video / Audio allocations
<p align="center">
<img width="435" height="218" alt="image" src="https://github.com/user-attachments/assets/90cbc19c-c615-4357-9e50-d34d729b9969" />
</p>
<p align="center">
<img width="418" height="213" alt="image" src="https://github.com/user-attachments/assets/0b8d56b7-28bc-4cc4-b100-341976df0698" />
</p>

**All video and audio registers are memory-mapped, not I/O-mapped.**

## Fixed I/O allocations
<p align="center">
<img width="536" height="267" alt="image" src="https://github.com/user-attachments/assets/7eeaa759-3996-44ba-be3e-b5f0fb2adc9c" />
</p>
<p align="center">
<img width="349" height="501" alt="image" src="https://github.com/user-attachments/assets/7cab82fc-a444-4626-9435-2db9193f156f" />
</p>
<p align="center">
<img width="536" height="235" alt="image" src="https://github.com/user-attachments/assets/b18a7fd7-49a0-411b-916f-6c54490798ac" />
</p>
The 8251A and two 8255As are I/O-mapped.

## Board documentation

- [PCB 1 — CPU, ROM, RAM, reset and bus](docs/01-cpu-board.md)
- [PCB 2 — Serial, 8255s, keyboard and SNES](docs/02-io-board.md)
- [PCB 3 — RP2040 VGA, audio and VRAM](docs/03-video-audio.md)


