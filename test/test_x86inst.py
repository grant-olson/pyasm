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

class test_text_generation(unittest.TestCase):
    def test_ModRM_calculation(self):
        "wasn't calculating this properly.  Added an extra 00 to some text output"
        m = findBestMatch("CALL foo")
        i = m.GetInstance()
        i.LoadConcreteValues("CALL foo")
        self.assertEqual(i.OpText(),
                         '  00000000: E8 00 00 00 00          CALL      0x5       ')
    def test_other_bad_string(self):
        m = findBestMatch("MOV EAX,0xCCCCCCCC")
        i = m.GetInstance()
        i.LoadConcreteValues("MOV EAX,0xCCCCCCCC")
        print i.OpText()
        self.assertEqual(i.OpText(),
                         '  00000000: E8 00 00 00 00          CALL      0x5       ')
    
if __name__ == "__main__":
    unittest.main()
    