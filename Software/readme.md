1. BIOS routine reference
BIOS address	Routine	Input	Result
0100H	PUTCHAR	A = ASCII character	Prints one character
0103H	GETCHAR	None	Waits for input; returns character in A
0106H	PUTSTR	HL = string address	Prints a null-terminated string
0109H	GETSTR	HL = buffer, B = capacity	Reads and echoes a line; returns length in A
010CH	NEWLINE	None	Prints CR + LF
010FH	PUTHEX8	A = 8-bit value	Prints two hexadecimal digits
0112H	PUTHEX16	HL = 16-bit value	Prints four hexadecimal digits
0115H	PUTSPACE	None	Prints one space
0118H	PUTBIN8	A = 8-bit value	Prints eight binary digits
011BH	TOUPPER	A = ASCII character	Returns uppercase character in A
0121H	CLS	None	Clears an ANSI-compatible terminal
