; ============================================================
; 85-BIT COMPUTER - BIOS JUMP TABLE
; Intel 8085A
; BIOS API Version 1.0
;
; ROM: 0000H - 3FFFH
; Jump table: 0100H - 017FH
;
; IMPORTANT:
; Do not change these entry addresses after release.
; Each JMP occupies exactly 3 bytes.
; ============================================================

; ============================================================
; 85-BIT COMPUTER - HARDWARE AND MEMORY DEFINITIONS
; ============================================================

; ------------------------------------------------------------
; 8251A UART
; ------------------------------------------------------------

UART_DATA       EQU 00H
UART_CTRL       EQU 01H
UART_STATUS     EQU 01H

; ------------------------------------------------------------
; User program memory
; ------------------------------------------------------------

USER_RAM_START  EQU 8000H
USER_RAM_END    EQU 0FDFFH

; ------------------------------------------------------------
; BIOS workspace
; ------------------------------------------------------------

BIOS_WORKSPACE  EQU 0FE00H
INPUT_BUFFER    EQU 0FE00H
IO_STUB         EQU 0FE40H
BIOS_VARIABLES  EQU 0FE43H
CPU_SAVE        EQU 0FE80H
HEX_BUFFER      EQU 0FE00H

; ------------------------------------------------------------
; CPU register snapshot
; ------------------------------------------------------------

REG_A           EQU CPU_SAVE+00H
REG_F           EQU CPU_SAVE+01H
REG_B           EQU CPU_SAVE+02H
REG_C           EQU CPU_SAVE+03H
REG_D           EQU CPU_SAVE+04H
REG_E           EQU CPU_SAVE+05H
REG_L           EQU CPU_SAVE+06H
REG_H           EQU CPU_SAVE+07H
REG_SP          EQU CPU_SAVE+08H
REG_PC          EQU CPU_SAVE+0AH
REG_VALID       EQU 0FEFFH

; ------------------------------------------------------------
; System stack
; ------------------------------------------------------------

STACK_BOTTOM    EQU 0FF00H
STACK_TOP       EQU 0FFFFH

; ==========================================
; ASCII CONTROL CHARACTERS
; ==========================================

NULL    EQU 00H
BEL     EQU 07H
BS      EQU 08H
TAB     EQU 09H
LF      EQU 0AH     ; Line Feed (\n)
CR      EQU 0DH     ; Carriage Return (\r)
ESC     EQU 1BH
SPACE   EQU 20H
DEL     EQU 7FH
; ============================================================
; RESET AND INTERRUPT VECTORS
; ============================================================
ORG 0000H
    JMP COLD_START

ORG 0008H
    JMP RST1_HANDLER

ORG 0010H
    JMP RST2_HANDLER

ORG 0018H
    JMP RST3_HANDLER

ORG 0020H
    JMP RST4_HANDLER

ORG 0024H
    JMP TRAP_HANDLER

ORG 0028H
    JMP RST5_HANDLER

ORG 002CH
    JMP RST55_HANDLER

ORG 0030H
    JMP RST6_HANDLER

ORG 0034H
    JMP RST65_HANDLER

ORG 0038H
    JMP RST7_HANDLER

ORG 003CH
    JMP RST75_HANDLER

ORG 0040H

COLD_START:

      DI
      LXI SP,STACK_TOP
        XRA A
        STA REG_VALID

; Initialise 8251A
; Requires hardware reset before execution
        MVI A,4EH       ; 8N1, 16x clock
        OUT UART_CTRL

        MVI A,37H       ; Enable TX/RX
        OUT UART_CTRL
; Initialise 8255A, Mode 0
        MVI A,9AH
        OUT 13H
; Jump to MONITOR
	JMP MONITOR

; ============================================================
; BIOS JUMP TABLE
; ============================================================
BIOS:   ORG 0100H

        JMP PUTCHAR   				; 0100H
        JMP GETCHAR    				; 0103H
        JMP PUTSTR       				; 0106H
        JMP GETSTR       				; 0109H

        JMP NEWLINE    				; 010CH
        JMP PUTHEX8     				; 010FH
        JMP PUTHEX16    				; 0112H
        JMP PUTSPACE    				; 0115H
        JMP PUTBIN8     				; 0118H
        JMP TOUPPER     				; 011BH
        JMP CLS         				; 011EH

			
ORG 0200H 
; ==========================================
; PUTCHAR
; A = ASCII character to transmit
; Preserves A and other registers
; ==========================================
PUTCHAR:
        PUSH PSW
TX_WAIT:
        IN   UART_CTRL  ; Read status
        ANI  01H        ; TxRDY?
        JZ   TX_WAIT
        POP  PSW
        OUT  UART_DATA
        RET  
; ==========================================
; GETCHAR
; A = ASCII character to transmit
; Preserves A and other registers
; ==========================================
GETCHAR: 	
        IN   UART_STATUS  ; Read 8251A status
        ANI  02H          ; Test RxRDY (bit 1)
        JZ   GETCHAR			  ; Wait while no data
        IN   UART_DATA    ; Read received character
        RET               ; Return character in A			
; ==========================================
; PUTSTR
; HL = Null-terminated string address
; ==========================================
PUTSTR:
        MOV  A,M
        ORA  A
        RZ
        CALL PUTCHAR
        INX  H
        JMP  PUTSTR  

; ============================================================
; GETSTR - Read a line from serial terminal
; Input:
;   HL = RAM buffer address
;   B  = total buffer capacity (1..255)
;
; Output:
;   Buffer = null-terminated ASCII string
;   A = number of characters stored
;
; Preserves:
;   BC, DE, HL
;
; Flags may change.
;
; Requires GETCHAR and PUTCHAR.
; ============================================================
GETSTR:
        PUSH B
        PUSH D
        PUSH H
        MOV A,B
        ORA A
        JZ GS_EMPTY
        MOV D,B
        DCR D           ; Maximum character count
        MVI E,00H       ; Current count
GS_WAIT:
        CALL GETCHAR
        CPI 0DH
        JZ GS_DONE
        CPI 0AH
        JZ GS_DONE
        CPI 08H
        JZ GS_BACKSPACE
        CPI 7FH
        JZ GS_BACKSPACE
        ; Save character
        MOV C,A
        ; Check buffer space
        MOV A,E
        CMP D
        JNC GS_WAIT
        ; Store and echo
        MOV A,C
        MOV M,A
        INX H
        INR E
        CALL PUTCHAR
        JMP GS_WAIT
GS_BACKSPACE:
        MOV A,E
        ORA A
        JZ GS_WAIT
        DCX H
        DCR E
        MVI A,08H
        CALL PUTCHAR
        MVI A,20H
        CALL PUTCHAR
        MVI A,08H
        CALL PUTCHAR
        JMP GS_WAIT
GS_DONE:
        MVI M,00H
        MVI A,0DH
        CALL PUTCHAR
        MVI A,0AH
        CALL PUTCHAR
        MOV A,E
        JMP GS_EXIT
GS_EMPTY:
        XRA A
GS_EXIT:
        POP H
        POP D
        POP B
        RET
; ==========================================
; NEWLINE
; Print CR + LF
; ==========================================
NEWLINE:
        MVI A,CR
        CALL PUTCHAR
        MVI A,LF
        CALL PUTCHAR
        RET    				
; ==========================================
; PUTHEX8
; Print an 8-bit value in hexadecimal
; ==========================================
PUTHEX8:
        PUSH PSW
        PUSH B
        MOV B,A
        RRC
        RRC
        RRC
        RRC
        ANI 0FH
        CALL HEX_DIGIT
        MOV A,B
        ANI 0FH
        CALL HEX_DIGIT
        POP B
        POP PSW
        RET
HEX_DIGIT:
        ANI 0FH
        CPI 0AH
        JC HEX_NUM
        ADI 07H
HEX_NUM:
        ADI 30H
        CALL PUTCHAR
        RET
; ==========================================
; PUTHEX16
; Print a 16-bit address in hexadecimal
; ==========================================
PUTHEX16:
        PUSH PSW
        PUSH H
        MOV A,H
        CALL PUTHEX8
        MOV A,L
        CALL PUTHEX8
        POP H
        POP PSW
        RET
; ==========================================
; PUTSPACE
; Print ' '
; ==========================================
PUTSPACE:
        MVI A,' '
        CALL PUTCHAR
        RET
; ==========================================
; PUTBIN8
; Print 8-bit binary
; ==========================================
PUTBIN8:
        PUSH PSW
        PUSH B
        PUSH D
        MOV D,A
        MVI B,08H
BIN_LOOP:
        MOV A,D
        RLC
        MOV D,A
        MVI A,'0'
        JNC BIN_PRINT
        MVI A,'1'
BIN_PRINT:
        CALL PUTCHAR
        DCR B
        JNZ BIN_LOOP
        POP D
        POP B
        POP PSW
        RET
; ==========================================
; TOUPPER
; Convert lowercase ASCII to uppercase
; ==========================================
TOUPPER:
        CPI 'a'
        RC
        CPI 'z'+1
        RNC
        SUI 20H
        RET
; ==========================================
; CLS - Clear serial terminal
; ANSI ESC[2J = Clear screen
; ANSI ESC[H  = Cursor home
; Preserves: BC, DE, HL
; ==========================================
CLS:
        MVI A,1BH       ; ESC
        CALL PUTCHAR
        MVI A,'['
        CALL PUTCHAR
        MVI A,'2'
        CALL PUTCHAR
        MVI A,'J'
        CALL PUTCHAR
        MVI A,1BH       ; ESC
        CALL PUTCHAR
        MVI A,'['
        CALL PUTCHAR
        MVI A,'H'
        CALL PUTCHAR
        RET
ORG 0400H

MONITOR:	
        CALL CLS
        LXI H,WELCOME
        CALL PUTSTR
 

LOOP:
        ; Display prompt
        MVI A,'>'
        CALL PUTCHAR
        CALL PUTSPACE
        ; Read command into RAM
        LXI H,INPUT_BUFFER
        MVI B,40H
        CALL GETSTR
        ; Check first character
        LXI H,INPUT_BUFFER
        MOV A,M
        ; Convert to uppercase
        CALL TOUPPER
        ; Ignore empty command
        ORA A
        JZ LOOP
        ; Check for HELP
        CPI 'H'
        JZ CMD_HELP
	; Check for DUMP
        CPI 'D'
        JZ CMD_DUMP
	; Check for IO read
        CPI 'I'
        JZ CMD_IN
	; Check for IO write
        CPI 'O'
        JZ CMD_OUT
	; Check for Edit memory
        CPI 'E'
        JZ CMD_EDIT
	; Check for GO program
        CPI 'G'
        JZ CMD_GO
	; Check for LOAD
        CPI 'L'
        JZ CMD_LOAD
        CPI 'R'
        JZ CMD_REGISTERS
        ; Unknown command
        LXI H,UNKNOWN_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; HELP COMMAND
; ============================================================

CMD_HELP:
        LXI H,HELP_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; CMD_DUMP - D XXXX
;
; Display 128 bytes of memory.
; 8 bytes per line, 16 lines.
;
; Example:
;   D 8000
;
; Uses:
;   HL = current memory address
;   B  = number of lines
;   C  = bytes per line
; ============================================================
CMD_DUMP:
        LXI H,INPUT_BUFFER+1
        CALL PARSE_SPACE
        JC DUMP_ERROR
        CALL PARSE_HEX16
        JC DUMP_ERROR
        ; PARSE_HEX16 returns the address in DE
        XCHG
        MVI B,10H          ; 16 lines
DUMP_LINE:
        CALL NEWLINE
        CALL PUTHEX16     ; Print line address
        MVI A,3AH         ; ':'
        CALL PUTCHAR
        CALL PUTSPACE
        MVI C,08H         ; Eight bytes per line
DUMP_BYTE:
        MOV A,M
        CALL PUTHEX8
        CALL PUTSPACE
        INX H
        DCR C
        JNZ DUMP_BYTE
        DCR B
        JNZ DUMP_LINE
        CALL NEWLINE
        JMP LOOP
DUMP_ERROR:
        LXI H,DUMP_ERR_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; PARSE_HEX16
;
; Input:
;   HL = pointer to 4 ASCII hex digits
;
; Output:
;   DE = converted address
;   Carry clear = success
;   Carry set = invalid input
;
; Preserves BC; advances HL
; ============================================================
PARSE_SPACE:
        MOV A,M
        CPI SPACE
        JNZ PARSE_BAD
        INX H
        ORA A
        RET
PARSE_BAD:
        STC
        RET

; Read two hex digits, advance HL, preserve BC and DE.
PARSE_HEX8:
        PUSH B
        MOV A,M
        CALL HEX_TO_NIBBLE
        CPI 0FFH
        JZ PARSE_BYTE_BAD
        RLC
        RLC
        RLC
        RLC
        MOV B,A
        INX H
        MOV A,M
        CALL HEX_TO_NIBBLE
        CPI 0FFH
        JZ PARSE_BYTE_BAD
        ORA B
        INX H
        POP B
        RET
PARSE_BYTE_BAD:
        POP B
        STC
        RET

; Read four digits into DE, advance HL; preserve BC.
PARSE_WORD:
        CALL PARSE_HEX8
        RC
        MOV D,A
        CALL PARSE_HEX8
        RC
        MOV E,A
        RET

; Strict address parser used by D and G.
PARSE_HEX16:
        CALL PARSE_WORD
        RC
        MOV A,M
        ORA A
        JNZ PARSE_BAD
        RET

; Carry set if DE is outside user RAM.
CHECK_USER_RAM:
        MOV A,D
        CPI 80H
        RC
        CPI 0FEH
        CMC
        RET

; ============================================================
; HEX_TO_NIBBLE
;
; Input:
;   A = ASCII character
;
; Output:
;   A = 00H to 0FH for valid hex
;   A = FFH for invalid hex
;
; Accepts 0-9, A-F and a-f
; ============================================================
HEX_TO_NIBBLE:
        ; Convert lowercase to uppercase
        CPI 61H          ; 'a'
        JC HTN_CHECK
        CPI 7BH          ; after 'z'
        JNC HTN_CHECK
        SUI 20H          ; Lowercase to uppercase
HTN_CHECK:
        CPI 30H          ; '0'
        JC HTN_BAD
        CPI 3AH          ; after '9'
        JC HTN_NUMBER
        CPI 41H          ; 'A'
        JC HTN_BAD
        CPI 47H          ; after 'F'
        JNC HTN_BAD
        ; Convert A-F into 10-15
        SUI 37H
        RET
HTN_NUMBER:
        ; Convert 0-9 into 0-9
        SUI 30H
        RET
HTN_BAD:
        MVI A,0FFH
        RET
; ============================================================
; CMD_IN - I XX
;
; Read an 8085 I/O port (00H to FFH)
;
; Example:
;   I 01
;   PORT 01 = 05
;
; Uses a RAM routine at FE40H:
;   DB XX C9 = IN XX / RET
; ============================================================
CMD_IN:
        LXI H,INPUT_BUFFER+1
        CALL PARSE_SPACE
        JC IN_ERROR
        CALL PARSE_HEX8
        JC IN_ERROR
        MOV B,A
        MOV A,M
        ORA A
        JNZ IN_ERROR
        ; Build IN XX / RET in RAM
        LXI H,IO_STUB
        MVI M,0DBH
        INX H
        MOV M,B
        INX H
        MVI M,0C9H
        ; Execute I/O read
        CALL IO_STUB
        MOV C,A
        ; Display result
        LXI H,IN_MSG
        CALL PUTSTR
        MOV A,B
        CALL PUTHEX8
        LXI H,IN_EQUALS
        CALL PUTSTR
        MOV A,C
        CALL PUTHEX8
        CALL NEWLINE
        JMP LOOP
IN_ERROR:
        LXI H,IN_ERR_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; CMD_OUT - O XX XX
;
; Write an 8-bit value to an I/O port.
;
; Example:
;   O 12 0F
;
; Registers:
;   B = I/O port address
;   C = Data to write
;   HL = Input buffer pointer
;
; RAM routine at FE40H:
;   D3 XX C9 = OUT XX / RET
; ============================================================
CMD_OUT:
        LXI H,INPUT_BUFFER+1
        CALL PARSE_SPACE
        JC OUT_ERROR
        CALL PARSE_HEX8
        JC OUT_ERROR
        MOV B,A
        CALL PARSE_SPACE
        JC OUT_ERROR
        CALL PARSE_HEX8
        JC OUT_ERROR
        MOV C,A
        MOV A,M
        ORA A
        JNZ OUT_ERROR
        ; Build OUT XX / RET in RAM
        LXI H,IO_STUB
        MVI M,0D3H       ; OUT opcode
        INX H
        MOV M,B          ; Port address
        INX H
        MVI M,0C9H       ; RET opcode
        ; Load data into accumulator
        MOV A,C
        ; Execute OUT instruction
        CALL IO_STUB
        ; Display confirmation
        LXI H,OUT_MSG
        CALL PUTSTR
        MOV A,B
        CALL PUTHEX8
        LXI H,OUT_EQUALS
        CALL PUTSTR
        MOV A,C
        CALL PUTHEX8
        CALL NEWLINE
        JMP LOOP
; Invalid command
OUT_ERROR:
        LXI H,OUT_ERR_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; CMD_EDIT - E XXXX XX
;
; Write one byte to a memory address.
;
; Example:
;   E 8000 3E
;
; Registers:
;   DE = Target memory address
;   HL = Input buffer pointer
;   B  = Digit counter
;   C  = Data byte
;
; Permitted addresses: 8000H - FDFFH
; ============================================================
CMD_EDIT:
        LXI H,INPUT_BUFFER+1
        CALL PARSE_SPACE
        JC EDIT_ERROR
        CALL PARSE_WORD
        JC EDIT_ERROR
        CALL PARSE_SPACE
        JC EDIT_ERROR
        CALL PARSE_HEX8
        JC EDIT_ERROR
        MOV C,A
        MOV A,M
        ORA A
        JNZ EDIT_ERROR
        CALL CHECK_USER_RAM
        JC EDIT_PROTECTED
        ; Write data to memory
        MOV A,C
        STAX D
        ; Read back and verify
        LDAX D
        CMP C
        JNZ EDIT_FAILED
        ; Display memory address
        XCHG
        CALL PUTHEX16
        ; Display separator
        LXI H,EDIT_EQUALS
        CALL PUTSTR
        ; Display written value
        MOV A,C
        CALL PUTHEX8
        CALL NEWLINE
        JMP LOOP
; Invalid command format
EDIT_ERROR:
        LXI H,EDIT_ERR_MSG
        JMP MON_PRINT_EXIT
; Protected memory address
EDIT_PROTECTED:
        LXI H,EDIT_PROT_MSG
        JMP MON_PRINT_EXIT
; Memory verification failed
EDIT_FAILED:
        LXI H,EDIT_FAIL_MSG
        JMP MON_PRINT_EXIT

; ============================================================
; CMD_GO - G XXXX
;
; Execute a user program from RAM.
;
; Valid addresses: 8000H - FDFFH
;
; User program can return using RET.
; ============================================================
CMD_GO:
        LXI H,INPUT_BUFFER+1
        CALL PARSE_SPACE
        JC GO_ERROR
        CALL PARSE_HEX16
        JC GO_ERROR
        ; Validate user RAM address
        CALL CHECK_USER_RAM
        JC GO_PROTECTED
        ; Display execution message
        PUSH D
        LXI H,GO_MSG
        CALL PUTSTR
        POP D
        XCHG
        CALL PUTHEX16
        CALL NEWLINE
        ; Push monitor return address
        LXI D,GO_RETURN
        PUSH D
        ; Execute user program
        PCHL
GO_RETURN:
        ; Capture registers before modifying flags or stack.
        STA REG_A
        SHLD REG_L
        MOV A,B
        STA REG_B
        MOV A,C
        STA REG_C
        MOV A,D
        STA REG_D
        MOV A,E
        STA REG_E
        PUSH PSW
        POP B
        MOV A,C
        STA REG_F
        LXI H,0000H
        DAD SP
        SHLD REG_SP
        LXI H,GO_RETURN
        SHLD REG_PC
        MVI A,01H
        STA REG_VALID
        DI
        LXI SP,STACK_TOP
        CALL NEWLINE
        LXI H,GO_RETURN_MSG
        JMP MON_PRINT_EXIT
GO_ERROR:
        LXI H,GO_ERR_MSG
        JMP MON_PRINT_EXIT
GO_PROTECTED:
        LXI H,GO_PROT_MSG
        JMP MON_PRINT_EXIT
; ============================================================
; 85-BIT COMPUTER
; INTEL HEX SERIAL LOADER V1.0
;
; Supported records:
;   00 = Data
;   01 = End of file
;
; User RAM: 8000H - FDFFH
; Buffer:   FE00H - FEFEH
;
; ESC aborts loading.
; ============================================================
CMD_LOAD:
        XRA A
        STA REG_VALID
        LXI H,LOAD_MSG
        CALL PUTSTR
; ------------------------------------------------------------
; Wait for the beginning of an Intel HEX record
; ------------------------------------------------------------
LOAD_WAIT:
        CALL GETCHAR
        CPI 1BH
        JZ LOAD_ABORT
        CPI 0DH
        JZ LOAD_WAIT
        CPI 0AH
        JZ LOAD_WAIT
        CPI 3AH          ; ASCII ':'
        JNZ LOAD_ERROR
; ------------------------------------------------------------
; Read record header
;
; B  = Record byte count
; C  = Running checksum
; DE = Destination address
; HL = Record buffer pointer
; ------------------------------------------------------------
        MVI C,00H
        ; Record length
        CALL LOAD_BYTE
        JC LOAD_ERROR
        MOV B,A
        ; Address high byte
        CALL LOAD_BYTE
        JC LOAD_ERROR
        MOV D,A
        ; Address low byte
        CALL LOAD_BYTE
        JC LOAD_ERROR
        MOV E,A
        ; Record type
        CALL LOAD_BYTE
        JC LOAD_ERROR
        CPI 00H
        JZ LOAD_DATA
        CPI 01H
        JZ LOAD_EOF
        JMP LOAD_TYPE_ERROR
; ------------------------------------------------------------
; Receive data into temporary buffer
; ------------------------------------------------------------
LOAD_DATA:
        LXI H,HEX_BUFFER
        ; Preserve original record length
        PUSH B
        MOV A,B
        ORA A
        JZ LOAD_DATA_CHECK
LOAD_DATA_LOOP:
        CALL LOAD_BYTE
        JC LOAD_POP_ERROR
        MOV M,A
        INX H
        DCR B
        JNZ LOAD_DATA_LOOP
; ------------------------------------------------------------
; Validate checksum
;
; Sum of all record bytes, including checksum,
; must equal zero modulo 256.
; ------------------------------------------------------------
LOAD_DATA_CHECK:
        CALL LOAD_BYTE
        JC LOAD_POP_ERROR
        MOV A,C
        ORA A
        JNZ LOAD_POP_CHECKSUM
        ; Restore original record length
        POP B
        MOV A,B
        ORA A
        JZ LOAD_RECORD_OK
; ------------------------------------------------------------
; Validate complete destination address range
;
; No memory is written until every destination
; address has been checked.
; ------------------------------------------------------------
        PUSH B
        PUSH D
LOAD_RANGE_LOOP:
        CALL CHECK_USER_RAM
        JC LOAD_RANGE_FAIL
        INX D
        DCR B
        JNZ LOAD_RANGE_LOOP
        POP D
        POP B
; ------------------------------------------------------------
; Copy validated record into user program RAM
; ------------------------------------------------------------
        LXI H,HEX_BUFFER
LOAD_COPY:
        MOV A,M
        STAX D
        ; Read back and verify
        LDAX D
        CMP M
        JNZ LOAD_WRITE_ERROR
        INX H
        INX D
        DCR B
        JNZ LOAD_COPY
; ------------------------------------------------------------
; Record successfully loaded
; Print one dot for each accepted data record.
; ------------------------------------------------------------
LOAD_RECORD_OK:
        MVI A,2EH
        CALL PUTCHAR
        JMP LOAD_WAIT
; ------------------------------------------------------------
; End-of-file record
;
; Must contain:
;   Length  = 00
;   Address = 0000
;   Type    = 01
;   Checksum = FF
; ------------------------------------------------------------
LOAD_EOF:
        MOV A,B
        ORA D
        ORA E
        JNZ LOAD_ERROR
        CALL LOAD_BYTE
        JC LOAD_ERROR
        MOV A,C
        ORA A
        JNZ LOAD_CHECKSUM_ERROR
        CALL NEWLINE
        LXI H,LOAD_DONE_MSG
        JMP LOAD_PRINT_EXIT
; ------------------------------------------------------------
; Error handling and stack cleanup
; ------------------------------------------------------------
LOAD_POP_ERROR:
        POP B
        JMP LOAD_ERROR
LOAD_POP_CHECKSUM:
        POP B
        JMP LOAD_CHECKSUM_ERROR
LOAD_RANGE_FAIL:
        POP D
        POP B
        JMP LOAD_ADDRESS_ERROR
LOAD_ERROR:
        CALL NEWLINE
        LXI H,LOAD_ERR_MSG
        JMP LOAD_PRINT_EXIT
LOAD_CHECKSUM_ERROR:
        CALL NEWLINE
        LXI H,LOAD_CHK_MSG
        JMP LOAD_PRINT_EXIT
LOAD_ADDRESS_ERROR:
        CALL NEWLINE
        LXI H,LOAD_ADDR_MSG
        JMP LOAD_PRINT_EXIT
LOAD_TYPE_ERROR:
        CALL NEWLINE
        LXI H,LOAD_TYPE_MSG
        JMP LOAD_PRINT_EXIT
LOAD_WRITE_ERROR:
        CALL NEWLINE
        LXI H,LOAD_WRITE_MSG
        JMP LOAD_PRINT_EXIT
LOAD_ABORT:
        CALL NEWLINE
        LXI H,LOAD_ABORT_MSG
        JMP LOAD_PRINT_EXIT
; ============================================================
; LOAD_BYTE
;
; Receive one hexadecimal byte and add it
; to the running checksum in C.
;
; Output:
;   A = Received byte
;   Carry clear = Success
;   Carry set   = Invalid character or ESC
;
; Preserves B, DE and HL.
; Updates C.
; ============================================================
LOAD_BYTE:
        CALL GET_HEX8
        RC
        PUSH PSW
        ADD C
        MOV C,A
        POP PSW
        ; Clear Carry without changing A
        ORA A
        RET
; ============================================================
; GET_HEX8
;
; Receive two ASCII hexadecimal characters
; and convert them into one binary byte.
;
; Example:
;   ASCII 'A', '5' becomes A5H
;
; Output:
;   A = Converted byte
;   Carry clear = Success
;   Carry set   = Invalid character or ESC
;
; Preserves BC, DE and HL.
; ============================================================
GET_HEX8:
        PUSH B
        ; Receive high nibble
        CALL GETCHAR
        CPI 1BH
        JZ GH8_ERROR
        CALL HEX_TO_NIBBLE
        CPI 0FFH
        JZ GH8_ERROR
        ; Move nibble into upper four bits
        RLC
        RLC
        RLC
        RLC
        MOV B,A
        ; Receive low nibble
        CALL GETCHAR
        CPI 1BH
        JZ GH8_ERROR
        CALL HEX_TO_NIBBLE
        CPI 0FFH
        JZ GH8_ERROR
        ; Combine high and low nibbles
        ORA B
        POP B
        ORA A
        RET
GH8_ERROR:
        POP B
        STC
        RET




; ============================================================
; LOAD_EXIT - invalidate snapshot after shared buffer use
; ============================================================
LOAD_PRINT_EXIT:
        CALL PUTSTR
LOAD_EXIT:
        XRA A
        STA REG_VALID
        JMP LOOP

; ============================================================
; CMD_REGISTERS - display last user program return state
; PC is the monitor return address, SP is after RET.
; ============================================================
CMD_REGISTERS:
        LDA REG_VALID
        CPI 01H
        JNZ REG_NOT_VALID
        LXI H,REG_TITLE
        CALL PUTSTR
        LXI H,REG_MSG_A
        CALL PUTSTR
        LDA REG_A
        CALL PUTHEX8
        LXI H,REG_MSG_F
        CALL PUTSTR
        LDA REG_F
        CALL PUTHEX8
        CALL NEWLINE
        LXI H,REG_MSG_BC
        CALL PUTSTR
        LDA REG_B
        CALL PUTHEX8
        LDA REG_C
        CALL PUTHEX8
        LXI H,REG_MSG_DE
        CALL PUTSTR
        LDA REG_D
        CALL PUTHEX8
        LDA REG_E
        CALL PUTHEX8
        LXI H,REG_MSG_HL
        CALL PUTSTR
        LDA REG_H
        CALL PUTHEX8
        LDA REG_L
        CALL PUTHEX8
        CALL NEWLINE
        LXI H,REG_MSG_SP
        CALL PUTSTR
        LHLD REG_SP
        CALL PUTHEX16
        LXI H,REG_MSG_PC
        CALL PUTSTR
        LHLD REG_PC
        CALL PUTHEX16
        CALL NEWLINE
        LXI H,REG_MSG_BITS
        CALL PUTSTR
        LDA REG_F
        CALL PUTBIN8
        CALL NEWLINE
        LXI H,REG_MSG_FLAGS
        CALL PUTSTR
        LDA REG_F
        ANI 80H
        CALL REG_PRINT_FLAG
        CALL PUTSPACE
        LDA REG_F
        ANI 40H
        CALL REG_PRINT_FLAG
        CALL PUTSPACE
        LDA REG_F
        ANI 10H
        CALL REG_PRINT_FLAG
        CALL PUTSPACE
        LDA REG_F
        ANI 04H
        CALL REG_PRINT_FLAG
        CALL PUTSPACE
        LDA REG_F
        ANI 01H
        CALL REG_PRINT_FLAG
        CALL NEWLINE
        JMP LOOP
REG_PRINT_FLAG:
        ORA A
        JZ REG_FLAG_ZERO
        MVI A,31H
        JMP PUTCHAR
REG_FLAG_ZERO:
        MVI A,30H
        JMP PUTCHAR
REG_NOT_VALID:
        LXI H,REG_NO_DATA
        JMP MON_PRINT_EXIT

MON_PRINT_EXIT:
        CALL PUTSTR
        JMP LOOP

RST1_HANDLER:
	RET
RST2_HANDLER:
	RET
RST3_HANDLER:
	RET
RST4_HANDLER:
	RET
TRAP_HANDLER:
	RET
RST5_HANDLER:
	RET
RST55_HANDLER:
	RET
RST6_HANDLER:
	RET
RST65_HANDLER:
	RET
RST7_HANDLER:
	RET
RST75_HANDLER:
	RET

; ============================================================
; MONITOR MESSAGES
; ============================================================

WELCOME:
        DB CR,LF
        DB '85-BIT COMPUTER',CR,LF
        DB 'INTEL 8085 SYSTEM',CR,LF
        DB '32KB RAM / 16KB ROM',CR,LF
        DB 'READY.',CR,LF,NULL
UNKNOWN_MSG:
        DB 'UNKNOWN COMMAND - TYPE H FOR HELP'
        DB CR,LF,NULL
DUMP_ERR_MSG:
        DB 'ERROR: USE D XXXX'
        DB CR,LF,NULL
IN_MSG:
        DB 'PORT ',NULL
IN_EQUALS:
        DB ' = ',NULL
IN_ERR_MSG:
        DB 'ERROR: USE I XX',CR,LF,NULL
OUT_MSG:
        DB 'PORT ',NULL
OUT_EQUALS:
        DB ' <- ',NULL
OUT_ERR_MSG:
        DB 'ERROR: USE O XX XX',CR,LF,NULL
EDIT_EQUALS:
        DB ' <- ',NULL
EDIT_ERR_MSG:
        DB 'ERROR: USE E XXXX XX',CR,LF,NULL
EDIT_PROT_MSG:
        DB 'ERROR: PROTECTED ADDRESS',CR,LF,NULL
EDIT_FAIL_MSG:
        DB 'ERROR: MEMORY WRITE FAILED',CR,LF,NULL
GO_MSG:
        DB 'EXECUTING AT ',NULL
GO_RETURN_MSG:
        DB 'RETURNED TO MONITOR',CR,LF,NULL
GO_ERR_MSG:
        DB 'ERROR: USE G XXXX',CR,LF,NULL
GO_PROT_MSG:
        DB 'ERROR: PROTECTED ADDRESS',CR,LF,NULL
LOAD_MSG:
        DB CR,LF
        DB 'INTEL HEX LOADER V1.0',CR,LF
        DB 'RAM: 8000-FDFF',CR,LF
        DB 'WAITING FOR DATA...',CR,LF
        DB NULL
LOAD_DONE_MSG:
        DB 'LOAD COMPLETE',CR,LF,NULL
LOAD_ERR_MSG:
        DB 'ERROR: INVALID HEX RECORD',CR,LF,NULL
LOAD_CHK_MSG:
        DB 'ERROR: CHECKSUM FAILED',CR,LF,NULL
LOAD_ADDR_MSG:
        DB 'ERROR: ADDRESS OUTSIDE USER RAM'
        DB CR,LF,NULL
LOAD_TYPE_MSG:
        DB 'ERROR: UNSUPPORTED RECORD TYPE'
        DB CR,LF,NULL
LOAD_WRITE_MSG:
        DB 'ERROR: MEMORY WRITE FAILED'
        DB CR,LF,NULL
LOAD_ABORT_MSG:
        DB 'LOAD ABORTED',CR,LF,NULL
REG_TITLE:
        DB 'CPU REGISTER SNAPSHOT',CR,LF,NULL
REG_NO_DATA:
        DB 'NO SAVED CPU REGISTERS',CR,LF,NULL
REG_MSG_A:
        DB 'A  = ',NULL
REG_MSG_F:
        DB '   F  = ',NULL
REG_MSG_BC:
        DB 'BC = ',NULL
REG_MSG_DE:
        DB ' DE = ',NULL
REG_MSG_HL:
        DB ' HL = ',NULL
REG_MSG_SP:
        DB 'SP = ',NULL
REG_MSG_PC:
        DB ' PC = ',NULL
REG_MSG_BITS:
        DB 'FLAGS: ',NULL
REG_MSG_FLAGS:
        DB 'S Z A P C',CR,LF,NULL
HELP_MSG:
        DB CR,LF
        DB '85-BIT MONITOR COMMANDS',CR,LF
        DB '-----------------------',CR,LF
        DB 'H         HELP',CR,LF
        DB 'D XXXX    MEMORY DUMP',CR,LF
        DB 'E XXXX XX EDIT MEMORY',CR,LF
        DB 'I XX      READ I/O PORT',CR,LF
        DB 'O XX XX   WRITE I/O PORT',CR,LF
        DB 'G XXXX    EXECUTE PROGRAM',CR,LF
        DB 'L         LOAD INTEL HEX',CR,LF
        DB 'R         DISPLAY CPU REGISTERS',CR,LF
        DB '-----------------------',CR,LF
        DB NULL

        END










