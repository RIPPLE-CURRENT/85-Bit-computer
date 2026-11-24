# 85-BIT Intel 8085 Development Studio

Run `start_windows.bat` on Windows with Python 3 and Tkinter. No pip packages required.

## Memory and I/O
- ROM: 0000H–3FFFH (16 KB)
- Expansion: 4000H–7FFFH (unmapped)
- RAM: 8000H–FFFFH (32 KB)
- 8251 UART: 00H data, 01H status/control
- 8255 PPI: 10H port A, 11H port B, 12H port C, 13H control

## EEPROM export
Click Assemble, then choose **Export ROM BIN** or **Export ROM S19**. The exported file is exactly 16,384 bytes (0000H–3FFFH), and all unused locations are filled with FFH. Select an EEPROM with at least 16 KB capacity and program the image starting at chip offset 0000H. For a 32 KB EEPROM, this image covers only half the device; arrange A14 or pad the image according to your hardware design. The assembler also permits RAM initialisation for simulation; RAM bytes are not included in the ROM export.

## 8255 controls
After reset the 8255 control register is 9BH (all input). The GUI's switches drive external input levels; the coloured indicators display pin levels. Amber means an input pin is high, green means an output pin is high. Mode 0 and BSR operations are emulated. Mode 1/2 handshake logic and interrupts are not implemented.

Example:
```asm
MVI A,80H  ; all ports output (mode 0)
OUT 13H
MVI A,55H
OUT 10H    ; write Port A
IN 11H     ; read Port B
```

## Limitations
Functional instruction-level CPU model, not cycle accurate. 8251 UART is a simplified functional model. 8255 supports basic mode 0 input/output and BSR, not hardware handshakes. Verify your physical pin wiring and EEPROM pinout before programming.

## Motorola S-record (.s19) export
The S19 export contains the same **complete 16,384-byte ROM** as the BIN export, including FF padding. It uses 16-byte S1 data records with 16-bit addresses 0000H through 3FFFH, an S0 ASCII header, optional S5 data-record count, and an S9 termination record with the assembler entry point. Each record includes the standard one's-complement checksum. CRLF line endings are used for compatibility with Windows EEPROM programmers. Select **Motorola S-record / S19** as the import format in the programmer; do not import the S19 file as raw binary.

## Intel 8255A full operating modes

The PPI at I/O `10H`–`13H` now supports **Mode 0**, **Mode 1** (strobed input/output for groups A and B), **Mode 2** (bidirectional Port A), and **BSR** control. The 8255 tab displays mode, interrupt enable, input/output buffer and interrupt status. Toggle the Port C switches to drive STB/ACK handshake inputs; these signals are **active low**. For input strobes, first set the input byte on Port A or B, drive STB low and then high. For output acknowledgements, drive ACK low then high. BSR writes to PC4/PC6/PC2 control the corresponding interrupt enables in handshake modes. The GUI reads a non-destructive port snapshot so it does not acknowledge pending data.

This is a functional, transaction-level model, **not a cycle-accurate electrical model**. It does not yet connect PPI INTR to the 8085's external interrupt pins or emulate analogue timing and setup/hold constraints. The 8255 control-register readback is a simulator convenience; real 8255A control registers are write-only.

Run the unit tests with `python -m unittest test_8255 -v`.

## Live serial terminal input

Type directly into the **LIVE TX** field or click the terminal and type. Each keystroke is immediately queued to the simulated 8251 receive FIFO at I/O `00H`; no Send button or Enter is required. Enter sends CR (`0D`), Backspace sends BS (`08`), and dedicated buttons send CR, LF or Ctrl+C. Terminal output is driven by the emulated CPU writing to port `00H` (no automatic local echo). The simulated CPU must be running or stepped to consume incoming bytes.

## Intel HEX and serial transfer

Use Save / Export Intel HEX to assemble the current editor without resetting the CPU. Save RAM HEX exports an inclusive range within 8000–FDFF. Run the BIOS, enter L, then use Send HEX File; the file is validated before queuing. Ctrl+V, Shift+Insert, right-click Paste and Paste send clipboard text. Send Text File queues ASCII-compatible text. RX progress measures bytes consumed, not successful BIOS writes. Cancel RX clears queued bytes; reset or abort the monitor if necessary. The simulated FIFO does not require character or line delays.
