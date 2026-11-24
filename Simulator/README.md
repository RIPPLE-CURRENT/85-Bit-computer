<div align="center">

<img width="100%" alt="85-BIT retro rocket and Intel 8085 logo" src="85bit-logo.png" />


# 85-BIT — Intel 8085 Development Studio

**A desktop Intel 8085 assembler, simulator, debugger and EEPROM image generator.**

![Python](https://img.shields.io/badge/Python-3.x-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-informational) ![CPU](https://img.shields.io/badge/CPU-Intel%208085-orange) ![Status](https://img.shields.io/badge/Status-Development-yellow)

</div>

## Overview

85-BIT is a Python/Tkinter development environment for writing, assembling, running and debugging Intel 8085 assembly programs before transferring them to a physical 8-bit computer. It combines a source editor, instruction-level CPU emulator, serial terminal, interactive parallel I/O and ROM image export in one application.

The interface features a dark theme, the 85-BIT logo, assembly syntax highlighting, line numbers, scrollbars and a live CPU register dashboard.

<div align="center">
  <img src="docs/simulator.png" alt="85-BIT simulator interface" width="100%" />
</div>

## User manual

[Download the illustrated simulator user manual (PDF)](docs/85BIT_Simulator_Only_User_Manual.pdf) for installation, programming, debugging, serial transfers and peripheral operation.

## Features

- **8085 assembler:** two-pass assembly with symbolic labels (including forward references), expressions and common directives such as `ORG`, `EQU`, `DB`, `DW`, `DS` and `END`.
- **CPU simulation:** registers, flags, program counter, stack pointer, step/run/stop controls and address breakpoints.
- **Assembly editor:** syntax highlighting for mnemonics, registers, labels, directives, literals and comments.
- **Live dashboard:** boxed register values and status flags in the top-right of the GUI.
- **8251 USART:** simplified I/O-mapped serial interface and built-in ASCII terminal.
- **8255 PPI:** interactive input switches and output indicators for Ports A, B and C; Mode 0, Mode 1/2 handshaking and bit set/reset (BSR) emulation.
- **Memory inspection:** hexadecimal memory viewer and selected RAM range export.
- **Intel HEX:** export assembled source or RAM with addresses and checksums; validate and transmit HEX files over the simulated serial interface.
- **Serial tools:** live keyboard input, clipboard paste, ASCII file transfers, RX progress and cancellation.
- **Terminal display:** green text, ANSI clear/home support, automatic scrolling and scrollback.
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

## Debugging and execution

Use **Open ASM** and **Save ASM** to manage source files. **Assemble** builds the current source, loads memory and sets the entry point. The assembler output shows symbols and the listing.

| Control | Purpose |
|---|---|
| **Run / Stop** | Start or pause execution |
| **Step** | Execute one instruction |
| **Reset** | Reset CPU and terminal state |
| **Toggle Breakpoint** | Add or remove a breakpoint at the hexadecimal address entered beside the button |
| **Refresh** | Update the memory viewer at the selected address |

The register dashboard displays the accumulator, general-purpose registers, flags, PC and SP. Use the memory viewer to inspect code, data and stack contents.

## Serial terminal and Intel HEX

The CPU / UART tab provides a simulated 8251 serial interface. Your assembly program must read received bytes and write transmitted bytes using the mapped I/O ports.

| Control | Purpose |
|---|---|
| **Paste / Ctrl+V / right-click Paste** | Queue clipboard text for serial reception |
| **Send HEX File** | Validate an Intel HEX file and queue its ASCII records |
| **Send Text File** | Queue text from a file |
| **Send CR / LF / Ctrl+C** | Queue individual control characters |
| **Cancel RX** | Discard pending receive bytes |
| **Save / Export Intel HEX** | Assemble current source and save addressed HEX records without resetting execution |
| **Save RAM HEX** | Export an inclusive RAM range within `8000H–FDFFH` |

The RX progress indicator tracks queued data consumed by the simulated CPU. Sending a HEX file does **not** directly write memory: the running assembly program must implement the receiving protocol. The terminal supports ANSI clear-screen and cursor-home sequences and retains scrollback.

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

On reset, the emulated 8255 control word is `9BH` (all ports configured as inputs). The GUI provides per-bit input switches and visual pin-level indicators. The implementation supports Mode 0 direction control, Port C bit set/reset commands and Mode 1/2 pin-level handshaking. Active-low STB and ACK inputs can be exercised using the GUI. This is functional emulation, not a guarantee of hardware timing.

## Project files

```text
85-BIT/
├── simulator.py         # Assembler, CPU emulator, devices and GUI
├── ansi_terminal.py     # ANSI terminal renderer
├── ppi8255.py           # 8255 peripheral emulation
├── start_windows.bat    # Windows launcher
├── example.asm          # Sample 8085 program
├── 85bit-logo.png       # GUI / README artwork
├── test_program.hex    # Sample Intel HEX file
├── test_8255.py        # Peripheral tests
├── test_intel_hex.py   # HEX tests
├── test_terminal.py    # Terminal tests
├── docs/
│   ├── simulator.png
│   └── 85BIT_Simulator_Only_User_Manual.pdf
└── README.md            # Project documentation
```

## Current limitations

This is a **functional, instruction-level development simulator**, not a cycle-accurate hardware model. The 8251 is a simplified terminal-oriented emulation; the 8255 models functional pin-level behaviour rather than electrical timing. Not every assembler dialect or vendor-specific syntax extension is supported. Validate timing, hardware interfaces and the final EEPROM image on the physical system.

## Development roadmap

Potential future enhancements include a disassembly window, symbol browser, watchpoints, expanded peripheral emulation, richer debugging and additional assembler compatibility.

---

<div align="center">

**85-BIT — Build it. Assemble it. Run it.**

</div>
