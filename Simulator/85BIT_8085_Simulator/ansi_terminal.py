"""VT100-style 80x25 character terminal for the simulated 8251 TX stream.
Supports cursor movement, erase, SGR colour, CR/LF/BS and scroll.
"""
class AnsiTerminal:
    def __init__(self, widget, columns=80, rows=25):
        self.widget=widget
        self.cols=columns; self.rows=rows
        self.widget.configure(wrap='none', state='disabled')
        self.reset()
        self.widget.tag_configure('ansi_bold', font=('Consolas',12,'bold'))
        palette=['#111827','#d55b65','#00ff66','#e9cb78','#78aaf2','#c79bf1','#6dd7db','#e4eaf0']
        for i,color in enumerate(palette):self.widget.tag_configure(f'fg{i}',foreground=color)
        self.render()

    def reset(self):
        self.cells=[[' ']*self.cols for _ in range(self.rows)]
        self.styles=[[()]*self.cols for _ in range(self.rows)]
        self.history=[]
        self.row=0;self.col=0;self.state='normal';self.params='';self.fg=2;self.bold=False

    def scroll(self):
        self.history.append((self.cells[0],self.styles[0]))
        if len(self.history)>2000:self.history.pop(0)
        self.cells.pop(0);self.cells.append([' ']*self.cols)
        self.styles.pop(0);self.styles.append([()]*self.cols)
        self.row=self.rows-1

    def put(self,c):
        if self.col>=self.cols:self.col=0;self.row+=1
        if self.row>=self.rows:self.scroll()
        self.cells[self.row][self.col]=c
        self.styles[self.row][self.col]=(f'fg{self.fg}',)+(('ansi_bold',) if self.bold else ())
        self.col+=1

    def csi(self,final):
        parts=self.params.split(';')
        def num(i,default):
            try:return int(parts[i]) if i<len(parts) and parts[i] else default
            except ValueError:return default
        if final in ('H','f'):
            self.row=max(0,min(self.rows-1,num(0,1)-1));self.col=max(0,min(self.cols-1,num(1,1)-1))
        elif final=='A':self.row=max(0,self.row-max(1,num(0,1)))
        elif final=='B':self.row=min(self.rows-1,self.row+max(1,num(0,1)))
        elif final=='C':self.col=min(self.cols-1,self.col+max(1,num(0,1)))
        elif final=='D':self.col=max(0,self.col-max(1,num(0,1)))
        elif final=='J':
            mode=num(0,0)
            if mode==2:
                self.history.clear()
                self.cells=[[' ']*self.cols for _ in range(self.rows)]
                self.styles=[[()]*self.cols for _ in range(self.rows)]
            elif mode in (0,1):
                for r in range(self.rows):
                    for c in range(self.cols):
                        if (r>self.row or (r==self.row and c>=self.col)) if mode==0 else (r<self.row or (r==self.row and c<=self.col)):
                            self.cells[r][c]=' ';self.styles[r][c]=()
        elif final=='K':
            mode=num(0,0)
            a,b=(0,self.cols) if mode==2 else ((0,self.col+1) if mode==1 else (self.col,self.cols))
            for c in range(a,b):self.cells[self.row][c]=' ';self.styles[self.row][c]=()
        elif final=='m':
            for part in parts:
                try:n=int(part) if part else 0
                except ValueError:continue
                if n==0:self.fg=2;self.bold=False
                elif n==1:self.bold=True
                elif n==22:self.bold=False
                elif n==39:self.fg=2
                elif 30<=n<=37:self.fg=n-30
                elif 90<=n<=97:self.fg=n-90

    def feed(self,data):
        for b in data:
            if isinstance(b,int):c=chr(b)
            else:c=b
            if self.state=='esc':
                if c=='[':self.state='csi';self.params=''
                else:self.state='normal'
                continue
            if self.state=='csi':
                if c.isdigit() or c in ';?':
                    if len(self.params)<64:self.params+=c
                else:
                    if c.isalpha():self.csi(c)
                    self.state='normal'
                continue
            if c=='\x1b':self.state='esc'
            elif c=='\r':self.col=0
            elif c=='\n':
                self.row+=1
                if self.row>=self.rows:self.scroll()
            elif c=='\b':self.col=max(0,self.col-1)
            elif c=='\t':
                for _ in range(8-self.col%8):self.put(' ')
            elif ' '<=c<='~' or ord(c)>=160:self.put(c)
        self.render()

    def render(self):
        w=self.widget
        w.configure(state='normal')
        w.delete('1.0','end')
        last=max([self.row]+[r for r in range(self.rows) if any(c!=' ' for c in self.cells[r])])
        lines=self.history+list(zip(self.cells[:last+1],self.styles[:last+1]))
        for r,(cells,styles) in enumerate(lines):
            line=''.join(cells).rstrip()
            if r:w.insert('end','\n')
            start=0
            while start<len(line):
                tags=styles[start];end=start+1
                while end<len(line) and styles[end]==tags:end+=1
                w.insert('end',line[start:end],tags)
                start=end
        cursor=f'{len(self.history)+self.row+1}.{min(self.col,self.cols-1)}'
        w.mark_set('insert',cursor)
        w.configure(state='disabled')
        w.xview_moveto(0.0)
        # Anchor the viewport at the bottom of actual output, not the
        # centre of the cursor line or unused virtual screen rows.
        w.yview_moveto(1.0 if self.row or self.history else 0.0)
