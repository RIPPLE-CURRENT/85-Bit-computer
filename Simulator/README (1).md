<div align="center">

<img src="85bit-logo.png" alt="85-BIT retro computing logo" width="620">

# 85-BIT — Intel 8085 Development Studio

**A desktop Intel 8085 assembler, simulator and EEPROM image generator.**

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-informational) ![CPU](https://img.shields.io/badge/CPU-Intel%208085-orange) ![Status](https://img.shields.io/badge/Status-Development-yellow)

</div>

## Overview

85-BIT is a Python/Tkinter development environment for writing, assembling, running and debugging Intel 8085 assembly programs before transferring them to a physical 8-bit computer. It combines a source editor, instruction-level CPU emulator, serial terminal, interactive parallel I/O and ROM image export in one application.

The interface features a dark theme, the 85-BIT logo, assembly syntax highlighting and a live CPU register dashboard.

## Features

- **8085 assembler:** two-pass assembly with symbolic labels (including forward references), expressions and common directives such as `ORG`, `EQU`, `DB`, `DW`, `DS` and `END`.
- **CPU simulation:** registers, flags, program counter, stack pointer, step/run/stop controls and address breakpoints.
- **Assembly editor:** syntax highlighting for mnemonics, registers, labels, directives, literals and comments.
- **Live dashboard:** boxed register values and status flags in the top-right of the GUI.
- **8251 USART:** simplified I/O-mapped serial interface and built-in ASCII terminal.
- **8255 PPI:** interactive input switches and output indicators for Ports A, B and C; Mode 0 and bit set/reset (BSR) emulation.
- **Memory inspection:** hexadecimal memory viewer.
- **EEPROM programming:** export a complete 16 KB ROM as raw binary (`.bin`) or Motorola S-record (`.s19`).

## Memory map

| Address range | Size | Function |
|---|---:|---|
| `0000H–3FFFH` | 16 KB | ROM / assembled program |
| `4000H–7FFFH` | 16 KB | Unmapped / future expansion |
| `8000H–FFFFH` | 32 KB | RAM |

## I/O map

| I/O port | Device | Register |
|---|---|---|
| `00H` | Intel 8251 USART | Data |
| `01H` | Intel 8251 USART | Status / control |
| `10H` | Intel 8255 PPI | Port A |
| `11H` | Intel 8255 PPI | Port B |
| `12H` | Intel 8255 PPI | Port C |
| `13H` | Intel 8255 PPI | Control |

## Getting started

### Requirements

- Windows computer
- Python 3 with Tkinter (included with typical Windows Python installations)
- No third-party pip packages

### Run

1. Download or clone this repository.
2. Keep `simulator.py`, `start_windows.bat` and `85bit-logo.png` together in the same directory.
3. Double-click **`start_windows.bat`**, or run:

   ```powershell
   python simulator.py
   ```

4. Open `example.asm` or enter your own source code.
5. Click **Assemble**, then **Run** or **Step**.
6. Use the serial terminal, register dashboard, memory viewer and 8255 controls to observe execution.

> If Windows reports that `py` or `python` is not recognised, install Python 3 and ensure it is available on your PATH.

## Example: 8255 input-to-output test

This program configures Port A as output and Port B as input. Toggle the Port B input switches in the GUI and observe the Port A output indicators.

```asm
        ORG 0000H
START:  MVI A,82H
        OUT 13H
LOOP:   IN  11H
        OUT 10H
        JMP LOOP
        END START
```

The bundled `example.asm` demonstrates serial output and echo through the simulated 8251 USART.

## EEPROM image export

After successful assembly, choose one of the export buttons:

| Button | File | Contents |
|---|---|---|
| **Export ROM BIN** | `.bin` | Exactly 16,384 raw bytes |
| **Export ROM S19** | `.s19` | Motorola S-record ASCII with addresses and checksums |

Both exports represent ROM addresses `0000H–3FFFH`; unused bytes are filled with `FFH`. RAM initialisation data is **not** included in the ROM export.

The Motorola S-record exporter produces an `S0` identification record, `S1` data records (16 data bytes per record), an `S5` record count and an `S9` termination record containing the assembly entry address. Each record includes a one's-complement checksum. See the [Motorola S-record format](https://en.wikipedia.org/wiki/Motorola_S-record).

**Programming notes:** Select the appropriate import format in your EEPROM programmer. A 16 KB image fits a 16 KB ROM region; if using a larger EEPROM, confirm address-line wiring, bank selection and any required padding before burning. Verify the programmed device against the exported file.

## 8255 interactive I/O

On reset, the emulated 8255 control word is `9BH` (all ports configured as inputs). The GUI provides per-bit input switches and visual pin-level indicators. The current implementation supports basic Mode 0 direction control and Port C bit set/reset commands. Mode 1/2 handshaking and interrupts are not implemented.

## Project files

```text
85-BIT/
├── simulator.py         # Assembler, CPU emulator, devices and GUI
├── start_windows.bat    # Windows launcher
├── example.asm          # Sample 8085 program
├── 85bit-logo.png       # GUI / README artwork
└── README.md            # Project documentation
```

## Current limitations

This is a **functional, instruction-level development simulator**, not a cycle-accurate hardware model. The 8251 is a simplified terminal-oriented emulation; the 8255 currently supports Mode 0 and BSR only. Not every assembler dialect or vendor-specific syntax extension is supported. Validate timing, hardware interfaces and the final EEPROM image on the physical system.

## Development roadmap

Potential future enhancements include a disassembly window, symbol browser, watchpoints, expanded peripheral emulation, richer debugging and additional assembler compatibility.

---

<div align="center">

**85-BIT — Build it. Assemble it. Run it.**

</div>
