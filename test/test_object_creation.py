# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

"""
Test the whole chain to a .obj file for a simple 'hello world'
assembly app.

Selected output from dumpbin against the app build in visual studio:

_main:
  00000000: 55                 push        ebp
  00000001: 8B EC              mov         ebp,esp
  00000003: 83 EC 40           sub         esp,40h
  00000006: 53                 push        ebx
  00000007: 56                 push        esi
  00000008: 57                 push        edi
  00000009: 8D 7D C0           lea         edi,[ebp-40h]
  0000000C: B9 10 00 00 00     mov         ecx,10h
  00000011: B8 CC CC CC CC     mov         eax,0CCCCCCCCh
  00000016: F3 AB              rep stos    dword ptr [edi]
  00000018: 68 00 00 00 00     push        offset _main
  0000001D: E8 00 00 00 00     call        00000022
  00000022: 83 C4 04           add         esp,4
  00000025: 33 C0              xor         eax,eax
  00000027: 5F                 pop         edi
  00000028: 5E                 pop         esi
  00000029: 5B                 pop         ebx
  0000002A: 83 C4 40           add         esp,40h
  0000002D: 3B EC              cmp         ebp,esp
  0000002F: E8 00 00 00 00     call        00000034
  00000034: 8B E5              mov         esp,ebp
  00000036: 5D                 pop         ebp
  00000037: C3                 ret

"""

from pyasm.x86asm import assembler
from pyasm.x86cpToCoff import CpToCoff
import unittest
import os, logging

linkCmd = "cd output && link /DEBUG /OPT:REF /OPT:ICF %s"

class test_object_creation(unittest.TestCase):     
        
    def test_hello_world(self):
        a = assembler()

        a.ADStr('hello_world','Hello, World\n\0')
        a.AIL("_main")
        a.AI("PUSH        EBP")
        a.AI("MOV         EBP,ESP")
        a.AI("SUB         ESP,0x40")
        a.AI("PUSH        EBX")
        a.AI("PUSH        ESI")
        a.AI("PUSH        EDI")
        a.AI("LEA         EDI,[EBP-0x40]")
        a.AI("MOV         ECX,0x10")
        a.AI("MOV         EAX,0x0CCCCCCCC")
        a.AI("REP STOS   [EDI]")
        a.AI("PUSH        hello_world")
        a.AI("CALL        _printf")
        a.AI("ADD         ESP,4")
        a.AI("XOR         EAX,EAX")
        a.AI("POP         EDI")
        a.AI("POP         ESI")
        a.AI("POP         EBX")
        a.AI("ADD         ESP,0x40")
        a.AI("CMP         EBP,ESP")
        a.AI("CALL        __chkesp")
        a.AI("MOV         ESP,EBP")
        a.AI("POP         EBP")
        a.AI("RET")
        a.ADStr("goodbye_world", "GOODBYE WORLD!\n\0")

        cp = a.Compile()
       
        self.assertEquals(cp.Code,'U\x8b\xec\x83\xec@SVW\x8d}\xc0\xb9\x10\x00\x00\x00\xb8\xcc\xcc\xcc\xcc\xf3\xabh\x00\x00\x00\x00\xe8\x00\x00\x00\x00\x83\xc4\x043\xc0_^[\x83\xc4@;\xec\xe8\x00\x00\x00\x00\x8b\xe5]\xc3')
        self.assertEquals(cp.CodePatchins,[('hello_world', 25, 2), ('_printf', 30, 1), ('__chkesp', 48, 1)])
        self.assertEquals(cp.CodeSymbols,[('_main', 0, 0)])
        self.assertEquals(cp.Data,'Hello, World\n\x00GOODBYE WORLD!\n\x00')
        self.assertEquals(cp.DataSymbols,[('hello_world', 0), ('goodbye_world', 14)])

        coff = CpToCoff(cp,"-defaultlib:LIBCPD -defaultlib:LIBCD -defaultlib:OLDNAMES ").makeReleaseCoff()

        f = file("output/testHelloWorld.obj","wb")
        coff.WriteToFile(f)
        f.close()

        self.assertEquals(os.system(linkCmd % "testHelloWorld.obj"),0)
        self.assertEquals(os.popen("cd output && testHelloWorld.exe").read(),"Hello, World\n")       

    def test_proc(self):
        a = assembler()

        a.ADStr('hello_world','Hello, World\n\0')
        a.AP("_main")
        a.AI("PUSH hello_world")
        a.AI("CALL _printf")
        a.AI("ADD ESP,0x4") # _cdecl cleanup
        a.AI("XOR EAX,EAX")
        a.EP()

        cp = a.Compile()
        coff = CpToCoff(cp,"-defaultlib:LIBCPD -defaultlib:LIBCD -defaultlib:OLDNAMES ").makeReleaseCoff()
        f = file("output/testProc.obj","wb")
        coff.WriteToFile(f)
        f.close()

        self.assertEquals(os.system(linkCmd % "testProc.obj"), 0)
        self.assertEquals(os.popen("cd output && testProc.exe").read(), "Hello, World\n")

    def test_goodbye_world(self):
        """
        Make sure we see the second param instead of defaulting to the first
        """
        a = assembler()

        a.ADStr('hello_world','Hello, World\n\0')
        a.ADStr('Goodbye_World','Goodbye, World\n\0')
        a.AP("_main")
        a.AI("PUSH Goodbye_World")
        a.AI("CALL _printf")
        a.AI("ADD ESP,0x4") # _cdecl
        a.AI("XOR EAX,EAX")
        a.EP()

        cp = a.Compile()
        coff = CpToCoff(cp,"-defaultlib:LIBCPD -defaultlib:LIBCD -defaultlib:OLDNAMES ").makeReleaseCoff()
        f = file("output/testGoodbyeWorld.obj","wb")
        coff.WriteToFile(f)
        f.close()

        self.assertEquals(os.system(linkCmd % "testGoodbyeWorld.obj"), 0) 
        self.assertEquals(os.popen("cd output &&testGoodbyeWorld.exe").read(), "Goodbye, World\n")

    def test_two_procs(self):
        """
        Make sure second proc gets called correctly
        """
        a = assembler()

        a.ADStr('hello_planets','Hello, all %i planets!\n\0')

        a.AP("_main")
        a.AI("CALL get_planets")
        a.AI("PUSH EAX")
        a.AI("PUSH hello_planets")
        a.AI("CALL _printf")
        a.AI("ADD ESP,0x8") #printf is _cdecl
        a.AI("XOR EAX,EAX")
        a.EP()

        #get_planets proc
        a.AP("get_planets")
        a.AI("MOV EAX,0x12")
        a.EP()

        cp = a.Compile()
        
        coff = CpToCoff(cp,"-defaultlib:LIBCPD -defaultlib:LIBCD -defaultlib:OLDNAMES ").makeReleaseCoff()
        f = file("output/testTwoProcs.obj","wb")
        coff.WriteToFile(f)
        f.close()

        self.assertEquals(os.system(linkCmd % "testTwoProcs.obj"), 0)
        self.assertEquals(os.popen("cd output && testTwoProcs.exe").read(),
                          "Hello, all 18 planets!\n")
                
if __name__ == '__main__':
    unittest.main()
    
