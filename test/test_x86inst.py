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


if __name__ == "__main__":
    unittest.main()
    