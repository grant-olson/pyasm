# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

import unittest
from pyasm.x86inst import longToString
from pyasm.x86asm import assembler, x86asmError

class test_long_to_string(unittest.TestCase):
    def test_positive(self):
        self.assertEquals(longToString(0x40),'\x40\x00\x00\x00')
        self.assertEquals(longToString(0x40,1),'\x40')

    def test_negative(self):
        self.assertEquals(longToString(-0x40),'\xc0\xff\xff\xff')
        self.assertEquals(longToString(-0x40,1),'\xc0')

    def test_no_endproc(self):
        a = assembler()
        a("!PROC foo")
        a("NOP")
        self.failUnlessRaises(x86asmError, a.Compile)
        
if __name__ == "__main__":
    unittest.main()
    