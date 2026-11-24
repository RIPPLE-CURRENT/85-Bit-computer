"""Intel 8255A PPI: modes 0, 1, 2, BSR and pin-level handshakes.
Active-low STB/ACK inputs are driven with set_input() (1=inactive).
"""
class PPI8255:
    def __init__(self): self.reset()
    def reset(self):
        self.control=0x9B
        self.latch=[0]*3; self.inputs=[0,0,0]
        self.ibf_a=self.ibf_b=self.obf_a=self.obf_b=False
        self.intr_a=self.intr_b=False
        self.inte_ai=self.inte_ao=self.inte_b=False
        self.input_a=self.input_b=0
        self.stb_a=self.stb_b=self.ack_a=self.ack_b=1
        self._prev_stb_a=self._prev_stb_b=self._prev_ack_a=self._prev_ack_b=1
        self._pending_ai=self._pending_bi=self._pending_ao=self._pending_bo=False
        self.inputs[2]=0xFF
    @property
    def mode_a(self):return 2 if (self.control&0x60)==0x40 or (self.control&0x60)==0x60 else (1 if self.control&0x20 else 0)
    @property
    def mode_b(self):return 1 if self.control&4 else 0
    @property
    def dir_a(self):return bool(self.control&0x10)
    @property
    def dir_b(self):return bool(self.control&2)
    def handshake_mask(self):
        mask=0
        if self.mode_a==2:mask|=0xF8 # PC3..7
        elif self.mode_a==1:mask|=(0x38 if self.dir_a else 0xC8) # PC3 INTR, PC4/5 input or PC6/7 output
        if self.mode_b==1:mask|=7
        return mask
    def input_mask(self,port):
        if port==0:return 0xFF if self.mode_a==2 or self.dir_a else 0
        if port==1:return 0xFF if self.dir_b else 0
        mask=(0xF0 if self.control&8 else 0)|(0x0F if self.control&1 else 0)
        return mask & ~self.handshake_mask()
    def _refresh_intr(self):
        self.intr_a=(self._pending_ai and self.inte_ai) or (self._pending_ao and self.inte_ao)
        self.intr_b=(self._pending_bi if self.dir_b else self._pending_bo) and self.inte_b
    def _port_c(self):
        val=(self.inputs[2]&self.input_mask(2))|(self.latch[2]&(~self.input_mask(2)&~self.handshake_mask()&255))
        def bit(n,v):
            nonlocal val
            val=(val|(1<<n)) if v else (val&~(1<<n))
        if self.mode_a==2:
            for n,v in ((3,self.intr_a),(4,self.stb_a),(5,self.ibf_a),(6,self.ack_a),(7,not self.obf_a)):bit(n,v)
        elif self.mode_a==1:
            bit(3,self.intr_a)
            if self.dir_a:
                for n,v in ((4,self.stb_a),(5,self.ibf_a)):bit(n,v)
            else:
                for n,v in ((6,self.ack_a),(7,not self.obf_a)):bit(n,v)
        if self.mode_b==1:
            for n,v in ((0,self.intr_b),(1,self.ibf_b if self.dir_b else not self.obf_b),(2,self.stb_b if self.dir_b else self.ack_b)):bit(n,v)
        return val&255
    def peek(self,port):
        """Non-destructive GUI view: unlike CPU IN, does not clear handshakes."""
        if port==3:return self.control
        if port==2:return self._port_c()
        if port==0 and (self.mode_a==2 or (self.mode_a==1 and self.dir_a)):return self.input_a
        if port==1 and self.mode_b==1 and self.dir_b:return self.input_b
        mask=self.input_mask(port)
        return ((self.inputs[port]&mask)|(self.latch[port]&(~mask&255)))&255
    def read(self,port):
        if port==3:return self.control
        if port==2:return self._port_c()
        if port==0 and (self.mode_a==2 or (self.mode_a==1 and self.dir_a)):
            value=self.input_a;self.ibf_a=False;self._pending_ai=False;self._refresh_intr();return value
        if port==1 and self.mode_b==1 and self.dir_b:
            value=self.input_b;self.ibf_b=False;self._pending_bi=False;self._refresh_intr();return value
        mask=self.input_mask(port)
        return ((self.inputs[port]&mask)|(self.latch[port]&(~mask&255)))&255
    def write(self,port,value):
        value&=255
        if port==3:
            if value&0x80:
                self.reset();self.control=value
            else:
                bit=(value>>1)&7;set_bit=bool(value&1)
                if set_bit:self.latch[2]|=1<<bit
                else:self.latch[2]&=~(1<<bit)
                # INTE is controlled via BSR, including handshake-reserved bits.
                if self.mode_a==2:
                    if bit==4:self.inte_ai=set_bit
                    if bit==6:self.inte_ao=set_bit
                elif self.mode_a==1:
                    if self.dir_a and bit==4:self.inte_ai=set_bit
                    if not self.dir_a and bit==6:self.inte_ao=set_bit
                if self.mode_b==1 and bit==2:self.inte_b=set_bit
                self._refresh_intr()
            return
        if port==2:
            mask=(~self.input_mask(2)&~self.handshake_mask())&255
            self.latch[2]=(self.latch[2]&~mask)|(value&mask)
            return
        if port==0 and (self.mode_a==2 or (self.mode_a==1 and not self.dir_a)):
            self.latch[0]=value;self.obf_a=True;self._pending_ao=False;self._refresh_intr();return
        if port==1 and self.mode_b==1 and not self.dir_b:
            self.latch[1]=value;self.obf_b=True;self._pending_bo=False;self._refresh_intr();return
        if not self.input_mask(port):self.latch[port]=value
    def set_input(self,port,bit,on):
        if not 0<=bit<8 or not 0<=port<3:raise ValueError('Invalid pin')
        mask=1<<bit
        if on:self.inputs[port]|=mask
        else:self.inputs[port]&=~mask
        if port==2:self._handshake_pin(bit,bool(on))
    def set_port_input(self,port,value):
        if port not in (0,1,2):raise ValueError('Invalid port')
        for bit in range(8):self.set_input(port,bit,bool(value&(1<<bit)))
    def _handshake_pin(self,bit,level):
        if self.mode_a==2 or self.mode_a==1:
            if bit==4 and (self.mode_a==2 or self.dir_a):
                prev=self.stb_a;self.stb_a=int(level)
                if prev==0 and level:
                    self.input_a=self.inputs[0];self.ibf_a=True;self._pending_ai=True
            if bit==6 and (self.mode_a==2 or not self.dir_a):
                prev=self.ack_a;self.ack_a=int(level)
                if prev==1 and not level:self.obf_a=False
                if prev==0 and level:self._pending_ao=True
        if self.mode_b==1 and bit==2:
            if self.dir_b:
                prev=self.stb_b;self.stb_b=int(level)
                if prev==0 and level:
                    self.input_b=self.inputs[1];self.ibf_b=True;self._pending_bi=True
            else:
                prev=self.ack_b;self.ack_b=int(level)
                if prev==1 and not level:self.obf_b=False
                if prev==0 and level:self._pending_bo=True
        self._refresh_intr()
    def pin_summary(self):
        return (f'MODE A={self.mode_a}  MODE B={self.mode_b}  INTE(A-IN/A-OUT/B)='
                f'{int(self.inte_ai)}/{int(self.inte_ao)}/{int(self.inte_b)}\n'
                f'IBF A/B={int(self.ibf_a)}/{int(self.ibf_b)}  '
                f'OBF A/B (pending)={int(self.obf_a)}/{int(self.obf_b)}  '
                f'INTR A/B={int(self.intr_a)}/{int(self.intr_b)}')
