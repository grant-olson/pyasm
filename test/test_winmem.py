import unittest
import pyasm.winmem
from pyasm.x86asm import assembler
from pyasm.x86cpToMemory import CpToMemory

class test_winmem(unittest.TestCase):
    def test_winmem(self):
        cp = pyasm.winmem.GetCurrentExecutablePosition()
        self.assertEquals(cp, pyasm.winmem.AllocateExecutableMemory(4))
        self.assertEquals(cp + 4, pyasm.winmem.GetCurrentExecutablePosition())
        pyasm.winmem.LoadExecutableMemoryString(cp,"aaaa")
        self.assertEquals(cp + 4, pyasm.winmem.GetCurrentExecutablePosition())

    def test_simple_function(self):
        a = assembler()
        a.ADStr("hello_world", "Hello world!")
        a.AP("test_print")
        a.AddLocal("self")
        a.AddLocal("args")
        a.AI("PUSH hello_world")
        a.AI("CALL PySys_WriteStdout")

        mem = CpToMemory(a.Compile(),pyasm.winmem)
        mem.MakeMemory(globals())

        print globals()
        test_print("Foo")
        
if __name__ == "__main__":
    unittest.main()
    