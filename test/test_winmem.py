# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

import unittest
import pyasm.excmem
from pyasm.x86asm import assembler, CDECL, STDCALL, PYTHON
from pyasm.x86cpToMemory import CpToMemory

class test_excmem(unittest.TestCase):
    def test_simple_function(self):
        a = assembler()
        a.ADStr("hello_world", "Hello world!\n\0")
        a.AP("test_print", PYTHON)
        a.AddLocal("self")
        a.AddLocal("args")
        #a.AI("INT 3")
        a.AI("PUSH hello_world")
        a.AI("CALL PySys_WriteStdout")
        a.AI("ADD ESP,0x4") #CDECL CLEANUP
        a.AI("MOV EAX,%s" % id(None))
        a.AI("ADD [EAX],0x1") #refcount
        a.EP()

        a.AP("test_print2", PYTHON)
        a.AddLocal("self")
        a.AddLocal("args")
        #a.AI("INT 3")
        a.AI("PUSH hello_world")
        a.AI("CALL PySys_WriteStdout")
        a.AI("ADD ESP,0x4") #cdecl cleanup
        a.AI("MOV EAX,%s" % id(None))
        a.AI("ADD [EAX],0x1") #refcount
        a.EP()
        
        mem = CpToMemory(a.Compile())
        mem.MakeMemory()
        mem.BindPythonFunctions(globals())
        
        test_print("Foo")
        test_print2('bar')
        
if __name__ == "__main__":
    unittest.main()
    
