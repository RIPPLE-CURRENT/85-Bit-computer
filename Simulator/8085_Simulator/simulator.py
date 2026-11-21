import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re, ast, pathlib


REG={'B':0,'C':1,'D':2,'E':3,'H':4,'L':5,'M':6,'A':7}
RP={'B':0,'D':1,'H':2,'SP':3}; RP2={'B':0,'D':1,'H':2,'PSW':3}
CONDS={'NZ':0,'Z':1,'NC':2,'C':3,'PO':4,'PE':5,'P':6,'M':7}
ALU={'ADD':0x80,'ADC':0x88,'SUB':0x90,'SBB':0x98,'ANA':0xA0,'XRA':0xA8,'ORA':0xB0,'CMP':0xB8}
IMM={'ADI':0xC6,'ACI':0xCE,'SUI':0xD6,'SBI':0xDE,'ANI':0xE6,'XRI':0xEE,'ORI':0xF6,'CPI':0xFE}
SINGLE={'NOP':0,'HLT':0x76,'RLC':7,'RRC':15,'RAL':23,'RAR':31,'DAA':39,'CMA':47,'STC':55,'CMC':63,'RET':0xC9,'PCHL':0xE9,'XTHL':0xE3,'SPHL':0xF9,'XCHG':0xEB,'DI':0xF3,'EI':0xFB,'RIM':0x20,'SIM':0x30}
DIRECT={'JMP':0xC3,'CALL':0xCD,'LDA':0x3A,'STA':0x32,'LHLD':0x2A,'SHLD':0x22}
PORT={'IN':0xDB,'OUT':0xD3}

def argsplit(s):
    out=[]; buf=''; quote=None
    for c in s:
        if c in "'\"":
            if quote is None: quote=c
            elif quote==c: quote=None
        if c==',' and quote is None: out.append(buf.strip());buf=''
        else: buf+=c
    if buf.strip():out.append(buf.strip())
    return out

def stripcomment(s):
    q=None
    for i,c in enumerate(s):
        if c in "'\"":
            if q is None:q=c
            elif q==c:q=None
        if c==';' and q is None:return s[:i]
    return s

def expression(src, symbols, pc, unresolved=False):
    src=src.strip()
    if not src:raise ValueError('missing expression')
    src=re.sub(r"(?<![\w])([0-9A-F]+)H\b",lambda m:str(int(m[1],16)),src,flags=re.I)
    src=re.sub(r'\b([01]+)B\b',lambda m:str(int(m[1],2)),src,flags=re.I)
    src=re.sub(r'\b([0-7]+)[OQ]\b',lambda m:str(int(m[1],8)),src,flags=re.I)
    src=re.sub(r'(?<![\w])\$(?![\w])',str(pc),src)
    tree=ast.parse(src,mode='eval')
    def ev(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,int):return n.value
        if isinstance(n,ast.Constant) and isinstance(n.value,str) and len(n.value)==1:return ord(n.value)
        if isinstance(n,ast.Name):
            if n.id.upper() in symbols:return symbols[n.id.upper()]
            if unresolved:return 0
            raise ValueError('undefined symbol '+n.id)
        if isinstance(n,ast.UnaryOp):
            v=ev(n.operand)
            if isinstance(n.op,ast.USub):return -v
            if isinstance(n.op,ast.UAdd):return v
            if isinstance(n.op,ast.Invert):return ~v
        if isinstance(n,ast.BinOp):
            a,b=ev(n.left),ev(n.right)
            ops={ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,ast.FloorDiv:lambda:a//b,ast.Div:lambda:a//b,ast.Mod:lambda:a%b,ast.LShift:lambda:a<<b,ast.RShift:lambda:a>>b,ast.BitOr:lambda:a|b,ast.BitAnd:lambda:a&b,ast.BitXor:lambda:a^b}
            if type(n.op) in ops:return ops[type(n.op)]()
        raise ValueError('invalid expression '+src)
    return ev(tree.body)

def assemble(source):
    symbols={}; lines=[]
    for num,raw in enumerate(source.splitlines(),1):
        s=stripcomment(raw).strip()
        if not s:continue
        label=None
        m=re.match(r'^([A-Za-z_][\w]*):\s*(.*)$',s)
        if m:label=m[1].upper();s=m[2].strip()
        m=re.match(r'^([A-Za-z_]\w*)\s+EQU\s+(.+)$',s,re.I)
        if m:label=m[1].upper();s='EQU '+m[2]
        if not s:lines.append((num,label,'',[]));continue
        parts=s.split(None,1);op=parts[0].upper().lstrip('.');a=argsplit(parts[1] if len(parts)>1 else '')
        lines.append((num,label,op,a))
    sizes={}; start=0
    for phase in (1,2):
        pc=0; memory={}; listing=[]; entry=None
        for num,label,op,a in lines:
            try:
                if label and op!='EQU':
                    if phase==1 and label in symbols:raise ValueError('duplicate label '+label)
                    if phase==1:symbols[label]=pc
                def val(i):return expression(a[i],symbols,pc,phase==1)
                if op=='EQU':
                    if not label or len(a)!=1:raise ValueError('EQU needs label and value')
                    if phase==1:symbols[label]=val(0)
                    continue
                if op=='ORG':pc=val(0)&65535;continue
                if op=='END':
                    if a:entry=val(0)&65535
                    break
                data=[]
                if not op:continue
                if op in ('DB','DEFB','BYTE'):
                    for item in a:
                        if len(item)>=2 and item[0] in "'\"" and item[-1]==item[0] and len(item)>3:
                            data.extend(item[1:-1].encode('latin-1'))
                        else:data.append(expression(item,symbols,pc+len(data),phase==1)&255)
                elif op in ('DW','DEFW','WORD'):
                    for item in a:
                        v=expression(item,symbols,pc+len(data),phase==1)&65535;data.extend((v&255,v>>8))
                elif op in ('DS','DEFS','BLOCK'):
                    n=val(0)
                    if n<0 or n>65536:raise ValueError('invalid reserve size')
                    data=[0]*n
                else:data=instruction(op,a,val)
                if pc+len(data)>65536:raise ValueError('address beyond FFFF')
                if phase==2:
                    for offset,b in enumerate(data):
                        addr=pc+offset
                        if 0x4000<=addr<0x8000:raise ValueError('unmapped memory %04X'%addr)
                        memory[addr]=b
                    if data:listing.append(f'{pc:04X}  '+''.join(f'{x:02X} ' for x in data[:6]).ljust(20)+f'[{num}]')
                pc+=len(data)
            except (ValueError,IndexError,KeyError,SyntaxError,ZeroDivisionError) as e:raise ValueError(f'Line {num}: {e} ({op} {", ".join(a)})') from e
    return memory,symbols,entry if entry is not None else 0,'\n'.join(listing)

def instruction(op,a,val):
    def check(n):
        if len(a)!=n:raise ValueError(f'{op} requires {n} operands')
    def reg(x):
        if x.upper() not in REG:raise ValueError('invalid register '+x)
        return REG[x.upper()]
    def pair(x,table=RP):
        if x.upper() not in table:raise ValueError('invalid pair '+x)
        return table[x.upper()]
    def byte(v):
        if not -128<=v<=255:raise ValueError('8-bit value out of range')
        return v&255
    def word(v):
        if not -32768<=v<=65535:raise ValueError('16-bit value out of range')
        return [v&255,(v>>8)&255]
    if op in SINGLE:check(0);return [SINGLE[op]]
    if op=='MOV':check(2);return [0x40+8*reg(a[0])+reg(a[1])]
    if op=='MVI':check(2);return [6+8*reg(a[0]),byte(val(1))]
    if op=='LXI':check(2);return [1+16*pair(a[0])]+word(val(1))
    if op in ('INX','DCX','DAD'):check(1);return [{'INX':3,'DCX':11,'DAD':9}[op]+16*pair(a[0])]
    if op in ('INR','DCR'):check(1);return [{'INR':4,'DCR':5}[op]+8*reg(a[0])]
    if op in ('LDAX','STAX'):
        check(1);r=pair(a[0]);
        if r>1:raise ValueError('LDAX/STAX only B or D')
        return [({'LDAX':10,'STAX':2}[op])+16*r]
    if op in ('PUSH','POP'):check(1);return [{'PUSH':0xC5,'POP':0xC1}[op]+16*pair(a[0],RP2)]
    if op in ALU:check(1);return [ALU[op]+reg(a[0])]
    if op in IMM:check(1);return [IMM[op],byte(val(0))]
    if op in DIRECT:check(1);return [DIRECT[op]]+word(val(0))
    if op in PORT:check(1);return [PORT[op],byte(val(0))]
    if op=='RST':check(1);v=val(0);return [0xC7+8*v] if 0<=v<=7 else (_ for _ in ()).throw(ValueError('RST 0-7'))
    for prefix,base in [('J',0xC2),('C',0xC4),('R',0xC0)]:
        suffix=op[len(prefix):]
        if op.startswith(prefix) and suffix in CONDS:
            check(0 if prefix=='R' else 1)
            b=base+8*CONDS[suffix]
            return [b] if prefix=='R' else [b]+word(val(0))
    raise ValueError('unknown instruction '+op)



def make_rom_image(assembled_rom):
    """Make the exact 16 KiB EEPROM image, with unprogrammed bytes FF."""
    rom = bytearray([0xFF] * 0x4000)
    for address, value in assembled_rom.items():
        if not 0 <= address < 0x4000:
            raise ValueError(f'ROM address out of range: {address:04X}')
        rom[address] = value
    return bytes(rom)


def srec_record(record_type, address, data=b''):
    """Motorola S-record with big-endian address and ones-complement checksum."""
    address_size = {'0': 2, '1': 2, '5': 2, '9': 2}[record_type]
    if not 0 <= address < (1 << (8 * address_size)):
        raise ValueError('S-record address out of range')
    data = bytes(data)
    count = address_size + len(data) + 1
    if count > 255:
        raise ValueError('S-record payload too large')
    payload = bytes([count]) + address.to_bytes(address_size, 'big') + data
    checksum = (~sum(payload)) & 0xFF
    return 'S' + record_type + payload.hex().upper() + f'{checksum:02X}'


def rom_to_s19(rom, entry=0, bytes_per_record=16):
    """Export full 16 KiB 8085 ROM as S0, S1, S5, S9 records."""
    if len(rom) != 0x4000:
        raise ValueError('ROM must be exactly 16,384 bytes')
    if not 1 <= bytes_per_record <= 32:
        raise ValueError('S1 data length must be 1..32 bytes')
    if not 0 <= entry <= 0xFFFF:
        raise ValueError('Invalid entry point')
    lines = [srec_record('0', 0, b'85BIT 8085 ROM')]
    for addr in range(0, len(rom), bytes_per_record):
        lines.append(srec_record('1', addr, rom[addr:addr + bytes_per_record]))
    lines.append(srec_record('5', (len(rom) + bytes_per_record - 1) // bytes_per_record))
    lines.append(srec_record('9', entry))
    return '\r\n'.join(lines) + '\r\n'

from ppi8255 import PPI8255

class CPU:
    def __init__(self):self.mem=bytearray(65536);self.ppi=PPI8255();self.reset()
    def reset(self):
        self.r=[0]*8;self.sp=0xFFFF;self.pc=0;self.f=2;self.halted=False;self.ie=False;self.rx=[];self.tx=[];self.mode=False;self.command=0;self.cycles=0;self.ppi.reset()
    def read(self,a):return self.mem[a&65535] if (a&65535)<0x4000 or (a&65535)>=0x8000 else 255
    def write(self,a,v):
        if (a&65535)>=0x8000:self.mem[a&65535]=v&255
    def fetch(self):v=self.read(self.pc);self.pc=(self.pc+1)&65535;return v
    def fw(self):lo=self.fetch();return lo|(self.fetch()<<8)
    def rw(self,a):return self.read(a)|(self.read(a+1)<<8)
    def ww(self,a,v):self.write(a,v);self.write(a+1,v>>8)
    def hl(self):return self.r[4]*256+self.r[5]
    def get(self,i):return self.read(self.hl()) if i==6 else self.r[i]
    def put(self,i,v):
        if i==6:self.write(self.hl(),v)
        else:self.r[i]=v&255
    def pair(self,i):return ((self.r[i*2]<<8)|self.r[i*2+1]) if i<3 else self.sp
    def setpair(self,i,v):
        v&=65535
        if i==3:self.sp=v
        else:self.r[i*2]=v>>8;self.r[i*2+1]=v&255
    def flag(self,bit):return bool(self.f&bit)
    def szp(self,v):
        v&=255;self.f=(self.f&0x11)|(0x80 if v&128 else 0)|(0x40 if v==0 else 0)|(4 if v.bit_count()%2==0 else 0)|2
    def arith(self,kind,v):
        a=self.r[7];c=1 if self.flag(1) else 0
        if kind in (0,1,2,3,7):
            subtract=kind in (2,3,7);carry=c if kind in (1,3) else 0
            result=a+(-v-carry if subtract else v+carry);z=result&255
            self.szp(z)
            if subtract:
                if a<(v+carry):self.f|=1
                if (a&15)<((v&15)+carry):self.f|=16
            else:
                if result>255:self.f|=1
                if ((a&15)+(v&15)+carry)>15:self.f|=16
            if kind!=7:self.r[7]=z
        else:
            z=[a&v,a^v,a|v][kind-4];self.szp(z);self.f=(self.f&~0x11)|(16 if kind==4 else 0);self.r[7]=z
    def cond(self,i):
        v=[not self.flag(0x40),self.flag(0x40),not self.flag(1),self.flag(1),not self.flag(4),self.flag(4),not self.flag(0x80),self.flag(0x80)]
        return v[i]
    def push(self,v):self.sp=(self.sp-1)&65535;self.write(self.sp,v>>8);self.sp=(self.sp-1)&65535;self.write(self.sp,v)
    def pop(self):v=self.rw(self.sp);self.sp=(self.sp+2)&65535;return v
    def io_in(self,p):
        if 0x10<=p<=0x13:return self.ppi.read(p-0x10)
        if p==0:return self.rx.pop(0) if self.rx else 0
        if p==1:return 0x05|(2 if self.rx else 0) # TxRDY, TxEMPTY, RxRDY
        return 255
    def io_out(self,p,v):
        if 0x10<=p<=0x13:self.ppi.write(p-0x10,v);return
        if p==0:self.tx.append(v)
        elif p==1:
            if not self.mode:self.mode=True
            else:
                self.command=v
                if v&0x40:self.mode=False;self.command=0
    def step(self):
        if self.halted:return
        op=self.fetch();self.cycles+=1
        if op==0:return
        if op==0x76:self.halted=True;return
        if 0x40<=op<=0x7f:self.put((op>>3)&7,self.get(op&7));return
        if 0x80<=op<=0xbf:self.arith((op>>3)&7,self.get(op&7));return
        if op&0xC7==0x06:self.put((op>>3)&7,self.fetch());return
        if op&0xC7==0x04:
            i=(op>>3)&7;a=self.get(i);v=(a+1)&255;c=self.f&1;self.szp(v);self.f=(self.f&~0x11)|c|(16 if (a&15)==15 else 0);self.put(i,v);return
        if op&0xC7==0x05:
            i=(op>>3)&7;a=self.get(i);v=(a-1)&255;c=self.f&1;self.szp(v);self.f=(self.f&~0x11)|c|(16 if (a&15)==0 else 0);self.put(i,v);return
        if op&0xCF==0x01:self.setpair((op>>4)&3,self.fw());return
        if op&0xCF==0x03:self.setpair((op>>4)&3,self.pair((op>>4)&3)+1);return
        if op&0xCF==0x0B:self.setpair((op>>4)&3,self.pair((op>>4)&3)-1);return
        if op&0xCF==0x09:
            v=self.hl()+self.pair((op>>4)&3);self.setpair(2,v);self.f=(self.f&~1)|(1 if v>65535 else 0);return
        if op in (0x02,0x12,0x0A,0x1A):
            addr=self.pair((op>>4)&1)
            if op&8:self.r[7]=self.read(addr)
            else:self.write(addr,self.r[7])
            return
        if op in (0x22,0x2A,0x32,0x3A):
            addr=self.fw()
            if op==0x22:self.ww(addr,self.hl())
            if op==0x2A:self.setpair(2,self.rw(addr))
            if op==0x32:self.write(addr,self.r[7])
            if op==0x3A:self.r[7]=self.read(addr)
            return
        if op in (7,15,23,31):
            a=self.r[7];old=self.f&1
            if op==7:c=a>>7;v=((a<<1)|c)&255
            elif op==15:c=a&1;v=(a>>1)|(c<<7)
            elif op==23:c=a>>7;v=((a<<1)|old)&255
            else:c=a&1;v=(a>>1)|(old<<7)
            self.r[7]=v;self.f=(self.f&~1)|c;return
        if op==0x27:
            a=self.r[7];adjust=(6 if (a&15)>9 or self.flag(16) else 0)+(0x60 if a>0x99 or self.flag(1) else 0)
            self.arith(0,adjust);return
        if op==0x2f:self.r[7]^=255;return
        if op==0x37:self.f|=1;return
        if op==0x3f:self.f^=1;return
        if op in IMM.values():self.arith((op>>3)&7,self.fetch());return
        if op in (0xC3,0xCD):
            addr=self.fw()
            if op==0xCD:self.push(self.pc)
            self.pc=addr;return
        if op==0xC9:self.pc=self.pop();return
        if op&0xC7==0xC2:
            addr=self.fw()
            if self.cond((op>>3)&7):self.pc=addr
            return
        if op&0xC7==0xC4:
            addr=self.fw()
            if self.cond((op>>3)&7):self.push(self.pc);self.pc=addr
            return
        if op&0xC7==0xC0:
            if self.cond((op>>3)&7):self.pc=self.pop()
            return
        if op&0xC7==0xC7:self.push(self.pc);self.pc=op&0x38;return
        if op&0xCF==0xC5:
            i=(op>>4)&3;self.push(self.pair(i) if i<3 else (self.r[7]<<8)|self.f);return
        if op&0xCF==0xC1:
            i=(op>>4)&3;v=self.pop()
            if i==3:self.r[7]=v>>8;self.f=(v&0xD5)|2
            else:self.setpair(i,v)
            return
        if op==0xDB:self.r[7]=self.io_in(self.fetch());return
        if op==0xD3:self.io_out(self.fetch(),self.r[7]);return
        if op==0xE3:
            v=self.rw(self.sp);self.ww(self.sp,self.hl());self.setpair(2,v);return
        if op==0xEB:self.r[2:4],self.r[4:6]=self.r[4:6],self.r[2:4];return
        if op==0xE9:self.pc=self.hl();return
        if op==0xF9:self.sp=self.hl();return
        if op==0xF3:self.ie=False;return
        if op==0xFB:self.ie=True;return
        if op==0x20:self.r[7]=0;return
        if op==0x30:return
        raise ValueError(f'Unsupported opcode {op:02X} at {(self.pc-1)&65535:04X}')

SAMPLE=pathlib.Path(__file__).with_name('example.asm').read_text() if pathlib.Path(__file__).with_name('example.asm').exists() else 'ORG 0000H\nHLT\n'

BG='#101622';PANEL='#1a2434';FG='#e5edf7';ACCENT='#00bce8';MUTED='#98abc2'
class GUI:
    def __init__(self,root):
        self.root=root;root.title('85-BIT  |  Intel 8085 Development Studio');root.geometry('1450x900');root.minsize(1050,700)
        root.configure(bg=BG);self.cpu=CPU();self.running=False;self.breakpoints=set();self.symbols={};self.built=False;self.rom_entry=0
        st=ttk.Style(root);st.theme_use('clam')
        st.configure('.',background=BG,foreground=FG,font=('Segoe UI',10))
        st.configure('TFrame',background=BG);st.configure('TLabel',background=BG,foreground=FG)
        st.configure('TButton',background=PANEL,foreground=FG,padding=(11,7),borderwidth=0)
        st.map('TButton',background=[('active','#29405b')])
        st.configure('TNotebook',background=BG,borderwidth=0);st.configure('TNotebook.Tab',background=PANEL,foreground=FG,padding=(16,8))
        st.map('TNotebook.Tab',background=[('selected','#28506c')])
        st.configure('TEntry',fieldbackground='#eaf0f6',foreground='#172030')
        header=tk.Frame(root,bg=BG);header.pack(fill='x',padx=12,pady=(9,4))
        logo=pathlib.Path(__file__).with_name('85bit-logo.png')
        if logo.exists():
            try:
                self.logo=tk.PhotoImage(file=str(logo));factor=max(1,(self.logo.width()+274)//275,(self.logo.height()+109)//110);self.logo=self.logo.subsample(factor,factor)
                tk.Label(header,image=self.logo,bg=BG).pack(side='left',padx=(0,18))
            except Exception:pass
        h=tk.Frame(header,bg=BG);h.pack(side='left')
        tk.Label(h,text='INTEL 8085 DEVELOPMENT STUDIO',font=('Segoe UI',18,'bold'),fg=FG,bg=BG).pack(anchor='w')
        tk.Label(h,text='16 KB ROM  •  32 KB RAM  •  8251 USART  •  8255 PPI  •  EEPROM EXPORT',font=('Segoe UI',10),fg=ACCENT,bg=BG).pack(anchor='w')
        # Compact live CPU dashboard in the upper-right corner.
        dashboard=tk.Frame(header,bg=BG)
        dashboard.pack(side='right',anchor='ne',padx=(15,0))
        self.cpu_cells={}
        cpu_groups=[('PC','SP','FLAGS','HL'),('A','B','C','D','E','H','L'),('S','Z','AC','P','CY','IE','HALT')]
        for group in cpu_groups:
            line=tk.Frame(dashboard,bg=BG);line.pack(anchor='e',pady=2)
            for key in group:
                tile=tk.Frame(line,bg=PANEL,highlightbackground='#34485c',highlightthickness=1)
                tile.pack(side='left',padx=2)
                tk.Label(tile,text=key,bg=PANEL,fg=MUTED,font=('Segoe UI',8,'bold'),padx=8).pack()
                value=tk.Label(tile,text='--',bg=PANEL,fg=ACCENT,font=('Consolas',12,'bold'),padx=8,pady=2)
                value.pack()
                self.cpu_cells[key]=value
        self.cpu_extra=tk.Label(dashboard,text='',bg=BG,fg=MUTED,font=('Consolas',9))
        self.cpu_extra.pack(anchor='e',pady=(3,0))
        toolbar=ttk.Frame(root);toolbar.pack(fill='x',padx=12,pady=5)
        for name,fn in [('Open ASM',self.open),('Save ASM',self.save),('Assemble',self.build),('Export ROM BIN',self.export_bin),('Export ROM S19',self.export_s19),('Reset',self.reset),('Step',self.step),('Run',self.run),('Stop',self.stop),('Toggle Breakpoint',self.breakpoint)]:
            ttk.Button(toolbar,text=name,command=fn).pack(side='left',padx=3)
        self.bp=tk.StringVar(value='0000');ttk.Entry(toolbar,textvariable=self.bp,width=8).pack(side='left',padx=4)
        split=ttk.Panedwindow(root,orient='horizontal');split.pack(fill='both',expand=True,padx=12,pady=5)
        left=ttk.Frame(split);right=ttk.Frame(split);split.add(left,weight=3);split.add(right,weight=2)
        ttk.Label(left,text='ASSEMBLY SOURCE').pack(anchor='w',pady=(0,4))
        self.source=tk.Text(left,font=('Consolas',11),undo=True,wrap='none',bg=PANEL,fg=FG,insertbackground=ACCENT,selectbackground='#31577a',relief='flat',padx=12,pady=10)
        self.source.pack(fill='both',expand=True);self.source.insert('1.0',SAMPLE)
        self._highlight_job=None
        self._setup_syntax()
        self.source.bind('<<Modified>>',self._source_modified,add='+')
        self.highlight_asm()

        ttk.Label(left,text='ASSEMBLER OUTPUT / SYMBOLS').pack(anchor='w',pady=(8,4))
        self.log=tk.Text(left,height=10,font=('Consolas',9),bg=PANEL,fg=MUTED,relief='flat',padx=8,pady=6);self.log.pack(fill='x')
        tabs=ttk.Notebook(right);tabs.pack(fill='both',expand=True)
        debug=ttk.Frame(tabs);io=ttk.Frame(tabs);tabs.add(debug,text='CPU / UART');tabs.add(io,text='8255 PPI')
        ttk.Label(debug,text='8251 SERIAL TERMINAL  •  I/O 00H / 01H').pack(anchor='w')
        self.terminal=tk.Text(debug,height=12,bg='#07131b',fg='#9ff6c2',insertbackground='white',font=('Consolas',12),relief='flat',padx=10,pady=10);self.terminal.pack(fill='both',expand=True)
        send=ttk.Frame(debug);send.pack(fill='x',pady=5)
        self.inp=ttk.Entry(send);self.inp.pack(side='left',fill='x',expand=True);self.inp.bind('<Return>',lambda e:self.send())
        ttk.Button(send,text='Send + CR',command=self.send).pack(side='left',padx=4)
        ttk.Label(debug,text='MEMORY VIEWER  •  HEX ADDRESS').pack(anchor='w',pady=(7,3))
        m=ttk.Frame(debug);m.pack(fill='x');self.addr=tk.StringVar(value='0000');ttk.Entry(m,textvariable=self.addr,width=10).pack(side='left');ttk.Button(m,text='Refresh',command=self.refresh).pack(side='left',padx=5)
        self.memory=tk.Text(debug,height=12,font=('Consolas',10),bg=PANEL,fg=FG,relief='flat',padx=8,pady=6);self.memory.pack(fill='both',expand=True,pady=5)
        ttk.Label(io,text='8255 PROGRAMMABLE PERIPHERAL INTERFACE',font=('Segoe UI',12,'bold')).pack(anchor='w',padx=12,pady=12)
        ttk.Label(io,text='10H = Port A    11H = Port B    12H = Port C    13H = Control').pack(anchor='w',padx=12)
        ttk.Label(io,text='Click switches to set external pins. PC handshake pins are active-low (0=asserted).').pack(anchor='w',padx=12,pady=(5,15))
        self.ppi_vars=[];self.ppi_leds=[];self.ppi_modes=[]
        for port in range(3):
            frame=tk.Frame(io,bg=PANEL,padx=12,pady=12);frame.pack(fill='x',padx=12,pady=7)
            title=tk.Frame(frame,bg=PANEL);title.pack(fill='x')
            tk.Label(title,text=f'PORT {"ABC"[port]}  •  {0x10+port:02X}H',font=('Segoe UI',11,'bold'),bg=PANEL,fg=ACCENT).pack(side='left')
            mode=tk.Label(title,text='INPUT',font=('Segoe UI',9),bg=PANEL,fg=MUTED);mode.pack(side='right');self.ppi_modes.append(mode)
            row=tk.Frame(frame,bg=PANEL);row.pack(fill='x',pady=(10,0))
            vs=[];ls=[]
            for bit in range(7,-1,-1):
                cell=tk.Frame(row,bg=PANEL);cell.pack(side='left',expand=True)
                tk.Label(cell,text=str(bit),bg=PANEL,fg=MUTED,font=('Consolas',9)).pack()
                v=tk.IntVar(value=0);vs.append((bit,v))
                cb=tk.Checkbutton(cell,variable=v,command=lambda p=port,b=bit,x=v:self.toggle_input(p,b,x.get()),bg=PANEL,activebackground=PANEL,selectcolor='#24374e',fg=FG,activeforeground=FG)
                cb.pack()
                led=tk.Label(cell,text='●',bg=PANEL,fg='#394a5d',font=('Segoe UI',17));led.pack();ls.append((bit,led))
            self.ppi_vars.append(vs);self.ppi_leds.append(ls)
        self.ppi_status=tk.StringVar();tk.Label(io,textvariable=self.ppi_status,justify='left',font=('Consolas',11),bg=BG,fg=FG).pack(anchor='w',padx=15,pady=15)
        ttk.Button(io,text='Refresh PPI',command=self.refresh_ppi).pack(anchor='w',padx=12)
        self.status=tk.StringVar(value='Ready');tk.Label(root,textvariable=self.status,anchor='w',bg=PANEL,fg=ACCENT,padx=12,pady=6).pack(fill='x',side='bottom')
        self.refresh()
    def _setup_syntax(self):
        t=self.source
        colors={'comment':'#74889a','string':'#e6bc78','label':'#76d8ff',
                'mnemonic':'#7fb9ff','directive':'#c7a3ff','number':'#f6ad73',
                'register':'#9fe3c0'}
        for name,color in colors.items():t.tag_configure(name,foreground=color)
        t.tag_configure('label',font=('Consolas',11,'bold'))
        t.tag_raise('sel')

    def _source_modified(self,event=None):
        self.source.edit_modified(False)
        if self._highlight_job is not None:self.root.after_cancel(self._highlight_job)
        self._highlight_job=self.root.after(180,self.highlight_asm)

    def highlight_asm(self):
        self._highlight_job=None
        t=self.source
        for tag in ('comment','string','label','mnemonic','directive','number','register'):
            t.tag_remove(tag,'1.0','end')
        opcodes=set(SINGLE)|set(DIRECT)|set(PORT)|set(ALU)|set(IMM)
        opcodes.update(('MOV','MVI','LXI','INX','DCX','DAD','INR','DCR','STAX','LDAX',
                        'PUSH','POP','RST','JMP','CALL','RET'))
        opcodes.update(('J'+x for x in CONDS))
        opcodes.update(('C'+x for x in CONDS))
        opcodes.update(('R'+x for x in CONDS))
        directives={'ORG','DB','DW','DS','EQU','END','SET','BYTE','WORD'}
        pattern=re.compile(r"""(?P<comment>;[^\n]*)|(?P<string>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(?P<label>\b[A-Za-z_.$?][\w.$?]*:)|(?P<word>\b[A-Za-z_.$?][\w.$?]*\b)|(?P<number>\b(?:0[xX][0-9a-fA-F]+|[0-9][0-9a-fA-F]*[Hh]|[01]+[Bb]|\d+)\b)""")
        source=t.get('1.0','end-1c')
        for match in pattern.finditer(source):
            kind=match.lastgroup
            if kind=='word':
                word=match.group().upper()
                kind=('mnemonic' if word in opcodes else 'directive' if word in directives
                      else 'register' if word in set(REG)|set(RP)|{'PSW','SP'} else None)
            if kind:
                start=f'1.0+{match.start()}c';end=f'1.0+{match.end()}c'
                t.tag_add(kind,start,end)

    def open(self):
        p=filedialog.askopenfilename(filetypes=[('Assembly','*.asm *.a85 *.txt'),('All files','*.*')])
        if p:self.source.delete('1.0','end');self.source.insert('1.0',pathlib.Path(p).read_text());self.built=False
    def save(self):
        p=filedialog.asksaveasfilename(defaultextension='.asm',filetypes=[('Assembly','*.asm')])
        if p:pathlib.Path(p).write_text(self.source.get('1.0','end'))
    def build(self):
        self.stop();self.built=False
        try:
            memory,self.symbols,entry,listing=assemble(self.source.get('1.0','end'))
            self.cpu.mem[:]=b'\x00'*65536
            for a,v in memory.items():self.cpu.mem[a]=v
            self.cpu.reset();self.cpu.pc=entry;self.rom_image={a:b for a,b in memory.items() if a<0x4000};self.rom_entry=entry;self.built=True
            self.log.delete('1.0','end');self.log.insert('end',f'Assembled {len(memory)} bytes. Entry {entry:04X}\nSymbols: '+', '.join(f'{k}={v:04X}' for k,v in self.symbols.items())+'\n'+listing)
            self.status.set(f'Assembled {len(memory)} bytes; PC={entry:04X}')
        except Exception as e:messagebox.showerror('Assembly error',str(e));self.status.set(str(e))
        self.refresh()
    def export_bin(self):
        if not self.built:
            messagebox.showwarning('EEPROM export','Assemble your source first.');return
        path=filedialog.asksaveasfilename(title='Export 16 KB ROM image',defaultextension='.bin',initialfile='85bit_rom_16k.bin',filetypes=[('Binary ROM image','*.bin'),('All files','*.*')])
        if not path:return
        try:
            # A complete 16 KB image, with unused addresses set to FF (erased EEPROM).
            # The assembled bytes are captured separately so CPU runtime cannot alter ROM.
            rom=make_rom_image(self.rom_image)
            pathlib.Path(path).write_bytes(rom)
            self.status.set(f'Exported 16,384 bytes to {path}')
            messagebox.showinfo('EEPROM image exported',f'16,384-byte raw binary saved:\n{path}\n\nBurn at EEPROM offset 0000H.\nUnused bytes are FFH.')
        except Exception as e:messagebox.showerror('Export error',str(e))
    def export_s19(self):
        if not self.built:
            messagebox.showwarning('EEPROM export', 'Assemble your source first.')
            return
        path = filedialog.asksaveasfilename(
            title='Export Motorola S-record (16 KB ROM)',
            defaultextension='.s19', initialfile='85bit_rom_16k.s19',
            filetypes=[('Motorola S19 / S-record', '*.s19 *.srec *.mot'), ('All files', '*.*')])
        if not path:
            return
        try:
            rom = make_rom_image(self.rom_image)
            text = rom_to_s19(rom, self.rom_entry)
            pathlib.Path(path).write_bytes(text.encode('ascii'))
            self.status.set(f'Exported Motorola S19 (16 KB ROM) to {path}')
            messagebox.showinfo('EEPROM image exported',
                f'Motorola S19 file saved:\n{path}\n\n'
                '16,384 ROM bytes at 0000H-3FFFH; unused bytes FFH.\n'
                'S1 records: 16 bytes each; S0 header, S5 count, S9 entry.\n'
                'Load as Motorola S-record in your EEPROM programmer.')
        except Exception as e:
            messagebox.showerror('Export error', str(e))
    def reset(self):self.stop();self.cpu.reset();self.terminal.delete('1.0','end');self.refresh()
    def step(self):
        try:self.cpu.step();self.flush()
        except Exception as e:self.stop();messagebox.showerror('CPU error',str(e))
        self.refresh()
    def flush(self):
        if self.cpu.tx:self.terminal.insert('end',bytes(self.cpu.tx).decode('latin-1'));self.terminal.see('end');self.cpu.tx.clear()
    def run(self):self.running=True;self.tick()
    def stop(self):self.running=False
    def tick(self):
        if not self.running:return
        try:
            for _ in range(2500):
                if self.cpu.halted or self.cpu.pc in self.breakpoints:self.running=False;break
                self.cpu.step()
            self.flush();self.refresh()
        except Exception as e:self.stop();messagebox.showerror('CPU error',str(e));return
        if self.running:self.root.after(10,self.tick)
    def breakpoint(self):
        try:
            a=int(self.bp.get().replace('$',''),16)&65535
            if a in self.breakpoints:self.breakpoints.remove(a)
            else:self.breakpoints.add(a)
            self.status.set('Breakpoints: '+', '.join(f'{x:04X}' for x in sorted(self.breakpoints)))
        except ValueError:messagebox.showerror('Breakpoint','Enter a hexadecimal address')
    def send(self):
        s=self.inp.get();self.cpu.rx.extend((s+'\r').encode('latin-1',errors='replace'));self.inp.delete(0,'end');self.status.set(f'{len(self.cpu.rx)} input byte(s) queued')
    def toggle_input(self,port,bit,value):self.cpu.ppi.set_input(port,bit,bool(value));self.refresh_ppi()
    def refresh_ppi(self):
        p=self.cpu.ppi
        for port in range(3):
            mask=p.input_mask(port)
            self.ppi_modes[port].config(text=f'INPUT MASK {mask:02X}H  /  OUTPUT MASK {255^mask:02X}H')
            for bit,led in self.ppi_leds[port]:
                is_input=bool(mask&(1<<bit));value=bool(p.peek(port)&(1<<bit))
                led.config(fg=('#19d3a0' if value else '#42566a') if not is_input else ('#ffbe59' if value else '#42566a'))
        self.ppi_status.set('CONTROL=%02XH   A=%02XH   B=%02XH   C=%02XH\n%s\nGREEN = output high   AMBER = external input high'%(p.control,p.peek(0),p.peek(1),p.peek(2),p.pin_summary()))
    def refresh(self):
        c=self.cpu
        values={'PC':f'{c.pc:04X}','SP':f'{c.sp:04X}','FLAGS':f'{c.f:02X}','HL':f'{c.hl():04X}',
                'A':f'{c.r[7]:02X}','B':f'{c.r[0]:02X}','C':f'{c.r[1]:02X}',
                'D':f'{c.r[2]:02X}','E':f'{c.r[3]:02X}','H':f'{c.r[4]:02X}','L':f'{c.r[5]:02X}',
                'S':str(int(bool(c.f&128))),'Z':str(int(bool(c.f&64))),
                'AC':str(int(bool(c.f&16))),'P':str(int(bool(c.f&4))),
                'CY':str(int(bool(c.f&1))),'IE':str(int(bool(c.ie))),
                'HALT':str(int(bool(c.halted)))}
        for key,value in values.items():
            label=self.cpu_cells[key];label.configure(text=value)
            if key in ('S','Z','AC','P','CY','IE','HALT'):
                label.configure(fg='#68e2a0' if value=='1' else MUTED)
        self.cpu_extra.configure(text=f'INSTRUCTIONS: {c.cycles:,}')
        try:a=int(self.addr.get().replace('$',''),16)&65535
        except ValueError:a=0
        self.memory.delete('1.0','end')
        for off in range(0,256,16):
            q=(a+off)&65535;self.memory.insert('end',f'{q:04X}: '+' '.join(f'{c.read(q+i):02X}' for i in range(16))+'\n')
        self.refresh_ppi()
if __name__=='__main__':
    root=tk.Tk();GUI(root);root.mainloop()
