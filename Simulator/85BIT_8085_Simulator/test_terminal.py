import tkinter as tk
import unittest
from ansi_terminal import AnsiTerminal

class TerminalTests(unittest.TestCase):
    def test_reset_home_and_follow(self):
        root=tk.Tk()
        try:
            w=tk.Text(root,height=8,width=80);w.pack();root.update()
            t=AnsiTerminal(w);root.update()
            self.assertEqual(w.yview()[0],0)
            t.feed(b'BOOT\r\nREADY');root.update()
            self.assertEqual(w.yview()[0],0)
            t.feed(b'\r\nLINE'*30);root.update()
            self.assertGreater(w.yview()[0],0)
            t.feed(b'\x1b[2J\x1b[HBOOT');root.update()
            self.assertEqual(w.yview()[0],0)
            t.feed(b'\r\nLINE'*30);root.update()
            t.reset();t.render();root.update()
            self.assertEqual(w.yview()[0],0)
        finally:root.destroy()
if __name__=='__main__':unittest.main()
