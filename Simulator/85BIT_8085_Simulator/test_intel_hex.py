import unittest
from simulator import intel_hex, validate_hex, CPU, assemble

class HexTests(unittest.TestCase):
    def test_program(self):
        memory, *_ = assemble('ORG 8000H\nMVI A,41H\nCALL 0100H\nRET\n')
        self.assertEqual(intel_hex(memory), ':068000003E41CD0001C964\r\n:00000001FF\r\n')
        self.assertEqual(validate_hex(intel_hex(memory)), b':068000003E41CD0001C964\r:00000001FF')
    def test_full_ram(self):
        memory={a:a&255 for a in range(0x8000,0xFE00)}
        result={}
        for line in validate_hex(intel_hex(memory)).decode().splitlines():
            raw=bytes.fromhex(line[1:]); addr=int.from_bytes(raw[1:3],'big')
            if raw[3]==0:result.update({addr+i:b for i,b in enumerate(raw[4:-1])})
        self.assertEqual(memory,result)
    def test_bad_records(self):
        for t in (':01800000413F', ':01FE000041C0', ':01FDFF0041C2', ':00000001FF\n:00000001FF'):
            with self.assertRaises(ValueError):validate_hex(t)
    def test_sparse(self):
        self.assertEqual(intel_hex({0x8000:1,0x9000:2}).count(':'),3)
    def test_fifo(self):
        c=CPU();c.rx.extend(b'abc');self.assertEqual([c.io_in(0) for _ in range(3)],list(b'abc'))

if __name__=='__main__':unittest.main()
