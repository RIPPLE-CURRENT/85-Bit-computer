import unittest
from ppi8255 import PPI8255
class Test8255(unittest.TestCase):
 def test_mode0(self):
  p=PPI8255();p.write(3,0x80);p.write(0,0xA5);self.assertEqual(p.read(0),0xA5)
 def test_bsr(self):
  p=PPI8255();p.write(3,0x80);p.write(3,0x01);self.assertEqual(p.read(2)&1,1)
 def test_mode1_input(self):
  p=PPI8255();p.write(3,0xBB);p.write(3,0x09);p.set_port_input(0,0xA5);p.set_input(2,4,0);p.set_input(2,4,1)
  self.assertTrue(p.ibf_a);self.assertTrue(p.intr_a);self.assertEqual(p.peek(0),0xA5)
  self.assertEqual(p.read(0),0xA5);self.assertFalse(p.intr_a)
 def test_mode1_output(self):
  p=PPI8255();p.write(3,0xA0);p.write(3,0x0D);p.write(0,0x42)
  self.assertTrue(p.obf_a);p.set_input(2,6,0);self.assertFalse(p.obf_a)
  p.set_input(2,6,1);self.assertTrue(p.intr_a)
 def test_mode2(self):
  p=PPI8255();p.write(3,0xC0);p.write(3,0x09);p.write(3,0x0D)
  p.write(0,0x32);p.set_input(2,6,0);p.set_input(2,6,1);self.assertTrue(p.intr_a)
  p.set_port_input(0,0x7F);p.set_input(2,4,0);p.set_input(2,4,1)
  self.assertEqual(p.read(0),0x7F)
if __name__=='__main__':unittest.main()
