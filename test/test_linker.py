# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

"""
Test various variables, parameters and constants in procedures
"""

from pyasm.x86asm import assembler, CDECL
from pyasm.x86cpToCoff import CpToCoff
import unittest
import os,sys

"""
Hopefully this will fix itself when I get all the proper coff entries in place
"""

linkCmd = "cd output && link /DEBUG %s"

class test_linker(unittest.TestCase):
    def test_linker(self):
        """
        Make sure params get refrennced correctly
        """
        a = assembler()

        a.ADStr('hello_planets','3h + 12h + 12h = %xh\n\0')
        
        a.AP("_main")
        a.AI("PUSH EBX")
        a.AI("MOV EBX,0x12")
        a.AI("PUSH EBX")
        a.AI("MOV EBX,0x3")
        a.AI("PUSH EBX")
        a.AI("CALL get_x_plus_two_y")
        a.AI("PUSH EAX")
        a.AI("PUSH hello_planets")
        a.AI("CALL _printf")
        a.AI("ADD ESP,0x8") #printf is _cdecl
        #a.AI("XOR EAX,EAX")
        a.AI("POP EBX")
        a.EP()

        #get_planets proc
        a.AP("get_x_plus_two_y")
        a.AA("x")
        a.AA("y")
        a.AI("XOR EAX,EAX")
        a.AI("MOV EAX,x")
        a.AI("ADD EAX,y")
        a.AI("ADD EAX,y")
        a.EP()

        cp = a.Compile()
        
        coff = CpToCoff(cp,"-defaultlib:LIBC -defaultlib:OLDNAMES ").makeReleaseCoff()
        f = file("output/testLinker.obj","wb")
        coff.WriteToFile(f)
        f.close()

        if sys.platform == "win32":
            self.assertEquals(os.system(linkCmd % "testLinker.obj"), 0)
            self.assertEquals(os.popen("cd output && testLinker.exe").read(),
                              "3h + 12h + 12h = 27h\n")
        else:
            print "Skipping linker test, coff files are only valid on win32 platforms"

        
if __name__ == '__main__':
    unittest.main()
    
