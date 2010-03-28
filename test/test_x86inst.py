# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

import unittest
from pyasm.x86inst import *
from pyasm.x86asm import *

class test_concrete_value_resolution(unittest.TestCase):
    def test_ModRMs(self):
        a = assembler()
        a.AP("foo")
        a.AA("bar")
        a.AA("baz")
        a.AddLocal("x")
        a.AddLocal("y")
        a.AI("MOV EAX,bar")
        a.AI("MOV EAX,baz")
        a.AI("MOV x,EAX")
        a.AI("MOV y,12")
        a.EP()

        a.Compile()   

class test_digit_flag(unittest.TestCase):
    def test_sub_flag(self):
        """
        Make sure we set the appropriate 'digit' flag for instructions that have it.
        I'm cheating a little in this test because we'll eventually optimize to find the
        imm8 version of the instruction, but I'm not doing that yet.
        """
        i = findBestMatch("SUB ESP,0x40")
        ii = i.GetInstance()
        ii.LoadConcreteValues(tokenizeInst("SUB ESP,0x40"))
        s = ii.OpDataAsString()
        self.assertEqual(s,"\x81\xec@\x00\x00\x00")

class test_text_generation(unittest.TestCase):
    def test_ModRM_calculation(self):
        "wasn't calculating this properly.  Added an extra 00 to some text output"
        m = findBestMatch("CALL foo")
        i = m.GetInstance()
        i.LoadConcreteValues("CALL foo")
        self.assertEqual(i.OpText(),
                         '  00000000: E8 00 00 00 00          CALL      foo       ')
    def test_other_bad_string(self):
        m = findBestMatch("MOV EAX,0xCCCCCCCC")
        i = m.GetInstance()
        i.LoadConcreteValues("MOV EAX,0xCCCCCCCC")
        self.assertEqual(i.OpText(),
                         '  00000000: B8 CC CC CC CC          MOV       EAX,0xCCCCCCCC')
    
if __name__ == "__main__":
    unittest.main()
    
