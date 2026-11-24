<div align="center">

<img src="85bit-logo.png" alt="85-BIT Computer logo" width="900" />

# 85-BIT — BIOS & ROM Monitor

**A serial-controlled firmware environment for the Intel 8085A computer.**

![CPU](https://img.shields.io/badge/CPU-Intel%208085A-orange) ![Assembly](https://img.shields.io/badge/Language-8085%20Assembly-blue) ![Version](https://img.shields.io/badge/Version-1.1-green) ![ROM](https://img.shields.io/badge/ROM-16%20KiB-purple)

</div>

## Overview

The 85-BIT BIOS and ROM Monitor provides a resident firmware interface for developing, loading and executing programs on the 85-BIT computer. Written in Intel 8085 assembly, it communicates through an Intel 8251A USART and provides a fixed BIOS jump table for application software.

The monitor runs on the emulated or physical CPU itself; it is not a command interpreter implemented by the simulator. Version 1.1 optimises the ROM layout and shared routines while retaining the version 1.0 BIOS API. Physical hardware validation remains a separate step.

## Documentation

| Document | Description |
|---|---|
| [ROM Monitor User Manual](docs/85BIT_ROM_Monitor_User_Manual.pdf) | Startup, command syntax, examples and troubleshooting |
| [BIOS & ROM Monitor Technical Reference](docs/85BIT_BIOS_Monitor_Technical_Reference.pdf) | Firmware architecture, memory allocation, API and internal routines |
| [Firmware source](85BIT_BIOS_Monitor_V1.1.asm) | Complete 8085 assembly source |

## Features

- Serial command interface with ANSI screen clearing and editable input.
- Hexadecimal memory dump and verified single-byte RAM editing.
- Direct access to all 256 I/O port addresses using a RAM instruction stub.
- User program execution with return to the monitor using `RET`.
- Intel HEX serial loader with record checksums, address protection and write verification.
- CPU register and flag snapshot after a user program returns.
- Eleven fixed BIOS API entry points for application developers.
- Initialisation of the 8251A USART and 8255A PPI.

## Getting started

### Simulator

1. Open `85BIT_BIOS_Monitor_V1.1.asm` in the 85-BIT simulator.
2. Assemble the source, reset the CPU and run from `0000H`.
3. Open the serial terminal and enter `H` followed by Enter.

### Physical computer

Assemble the firmware and program the ROM image into the device mapped at `0000H–3FFFH`. Connect an ANSI-compatible serial terminal using the appropriate electrical interface. The firmware configures the USART for 8 data bits, no parity, one stop bit and a 16× clock; the external clock determines the baud rate. Reset the hardware to start the monitor.

### Startup and help

```text
85-BIT COMPUTER
INTEL 8085 SYSTEM
32KB RAM / 16KB ROM
READY.
> H

85-BIT MONITOR COMMANDS
-----------------------
H         HELP
D XXXX    MEMORY DUMP
E XXXX XX EDIT MEMORY
I XX      READ I/O PORT
O XX XX   WRITE I/O PORT
G XXXX    EXECUTE PROGRAM
L         LOAD INTEL HEX
R         DISPLAY CPU REGISTERS
-----------------------
>
```

## Monitor commands

All arguments are hexadecimal without an `H` suffix. Enter the specified number of digits and separate arguments with spaces.

| Command | Function | Example |
|---|---|---|
| `H` | Display help | `H` |
| `D XXXX` | Dump 128 bytes, eight per line | `D 8000` |
| `E XXXX XX` | Write and verify one byte in user RAM | `E 8000 3E` |
| `I XX` | Read an I/O port | `I 01` |
| `O XX XX` | Write an I/O port | `O 12 0F` |
| `G XXXX` | Execute a program in user RAM | `G 8000` |
| `L` | Receive Intel HEX records | `L` |
| `R` | Display last saved CPU register snapshot | `R` |

## Memory map

| Address range | Size | Function |
|---|---:|---|
| `0000H–3FFFH` | 16 KiB | BIOS ROM |
| `4000H–5FFFH` | 8 KiB | Expansion (planned) |
| `6000H–7FFFH` | 8 KiB | Bank-switched video window (planned) |
| `8000H–FDFFH` | 31.5 KiB | User program RAM |
| `FE00H–FEFFH` | 256 B | BIOS workspace |
| `FF00H–FFFFH` | 256 B | Reserved system stack region |

The firmware restricts `E`, `G` and Intel HEX data writes to user RAM. This is monitor-level protection, not hardware memory protection against arbitrary user code.

### BIOS workspace

| Address | Purpose |
|---|---|
| `FE00H–FE3FH` | Command input buffer |
| `FE40H–FE42H` | Dynamic `IN` / `OUT` instruction stub |
| `FE43H–FE7FH` | BIOS variables / reserved |
| `FE80H–FE8BH` | CPU register snapshot
| `FEFFH` | Snapshot validity flag (outside HEX buffer) |
| `FE00H–FEFEH` | Temporary Intel HEX record buffer (overlays workspace) |

The loader invalidates the saved register snapshot when it exits. The stack is initialised to `FFFFH`.

## I/O map

| Port | Device | Register |
|---|---|---|
| `00H` | 8251A | Data |
| `01H` | 8251A | Status / control |
| `10H` | 8255A | Port A |
| `11H` | 8255A | Port B |
| `12H` | 8255A | Port C |
| `13H` | 8255A | Control |

The startup PPI control word is `9AH`: Ports A and B and upper Port C are inputs; lower Port C is output. Video control ports `40H–7FH` are reserved in the wider hardware design, not implemented as monitor video services.

## BIOS API

Application programs should call the fixed jump-table entries rather than internal implementation addresses. Each entry is a three-byte `JMP` instruction.

| Address | Routine | Interface |
|---|---|---|
| `0100H` | `PUTCHAR` | A = character to transmit |
| `0103H` | `GETCHAR` | Returns received character in A; blocking |
| `0106H` | `PUTSTR` | HL = null-terminated string |
| `0109H` | `GETSTR` | HL = buffer, B = capacity; returns length in A |
| `010CH` | `NEWLINE` | Transmit CR/LF |
| `010FH` | `PUTHEX8` | Print A as two hex digits |
| `0112H` | `PUTHEX16` | Print HL as four hex digits |
| `0115H` | `PUTSPACE` | Print a space |
| `0118H` | `PUTBIN8` | Print A as eight binary digits |
| `011BH` | `TOUPPER` | Convert ASCII in A to uppercase |
| `011EH` | `CLS` | ANSI clear screen and cursor home |

See the technical reference for register preservation and calling conventions. The jump-table region `0100H–017FH` is reserved for stable API entries.

## Example: load and run a program

```asm
        ORG 8000H
        MVI A,41H
        CALL 0100H       ; BIOS PUTCHAR
        RET              ; Return to monitor
        END
```

Assemble and export as Intel HEX, or use this equivalent file:

```text
:068000003E41CD0001C964
:00000001FF
```

Enter `L`, send the file over serial, then execute `G 8000`.

```text
> L
INTEL HEX LOADER V1.0
RAM: 8000-FDFF
WAITING FOR DATA...
.
LOAD COMPLETE
> G 8000
EXECUTING AT 8000
A
RETURNED TO MONITOR
>
```

The loader supports type `00` data and type `01` EOF records, up to 255 data bytes per record. It checks each record before copying it to RAM. On physical hardware, allow sufficient time between records to avoid receive overruns. ESC cancels loading (inside a record it may report an invalid record).

## CPU register inspection

Load and run the following test program:

```asm
        ORG 8000H
        LXI B,1234H
        LXI D,5678H
        LXI H,9ABCH
        XRA A
        STC
        MVI A,55H
        RET
        END
```

Enter `R` after the program returns. The saved accumulator is `55H`, BC is `1234H`, DE is `5678H`, HL is `9ABCH`, and the zero, parity and carry flags are set. SP represents the stack pointer after `RET`; PC represents the monitor return address, not the last user instruction. The snapshot is unavailable after reset or a subsequent HEX load until another program returns.

## Firmware organisation

| ROM origin | Purpose |
|---|---|
| `0000H` | Reset and interrupt vectors |
| `0040H` | Cold-start initialisation |
| `0100H` | BIOS jump table |
| `0200H` | BIOS service routines |
| `0400H` | Monitor command interpreter and handlers |

## V1.1 memory optimisation

| Metric | V1.0 | V1.1 |
|---|---:|---:|
| ROM address footprint | 6,406 B | 3,169 B |
| Contiguous free ROM | 9,978 B | 13,215 B |
| Monitor origin | `1000H` | `0400H` |
| Last occupied address | `1905H` | `0C60H` |

Free contiguous ROM: `0C61H–3FFFH`. The EEPROM image remains 16 KiB. Shared hexadecimal parsers, RAM range checking and message exits reduce duplication. All eight commands and eleven API entries remain compatible. The loader banner remains V1.0.

Firmware downloads: [ROM binary](85BIT_BIOS_Monitor_V1.1.bin) · [ROM Intel HEX](85BIT_BIOS_Monitor_V1.1.hex). These are EEPROM images, not user RAM loader files.

## Repository layout

```text
85-BIT-Monitor/
├── README.md
├── 85bit-logo.png
├── 85BIT_BIOS_Monitor_V1.1.asm
├── 85BIT_BIOS_Monitor_V1.1.bin
├── 85BIT_BIOS_Monitor_V1.1.hex
└── docs/
    ├── 85BIT_ROM_Monitor_User_Manual.pdf
    └── 85BIT_BIOS_Monitor_Technical_Reference.pdf
```

## Limitations and maintenance

The monitor is a compact development firmware, not a multitasking operating system or interactive instruction debugger. User programs must preserve a valid return stack and execute `RET` to return normally. Interrupt handlers are placeholders. The loader does not support extended Intel HEX addressing, and earlier accepted records remain in RAM if a later record fails. Register inspection is a saved snapshot, not a live debugger. Keep the published BIOS API addresses stable when developing future firmware.

---

<div align="center">

**85-BIT — Build it. Assemble it. Run it.**

</div>
