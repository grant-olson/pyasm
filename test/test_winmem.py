import unittest
import pyasm.winmem

class test_winmem(unittest.TestCase):
    def test_winmem(self):
        cp = pyasm.winmem.GetCurrentExecutablePosition()
        self.assertEquals(cp, pyasm.winmem.AllocateExecutableMemory(4))
        self.assertEquals(cp + 4, pyasm.winmem.GetCurrentExecutablePosition())
        pyasm.winmem.LoadExecutableMemoryString(cp,"aaaa")
        self.assertEquals(cp + 4, pyasm.winmem.GetCurrentExecutablePosition())
        

if __name__ == "__main__":
    unittest.main()
    