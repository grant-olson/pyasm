import unittest
from pyasm.x86disasm import x86Block,x86Disassembler

"""
We could probably write a more proper unittest, but at this point the output
isn't perfect.  I'm happy if it runs without crashing.

Here is the output for a release build of hello world from dumpbin:

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

class test_x86disasm(unittest.TestCase):
    def test_release_hello_world(self):
        code = x86Block('h\x00\x00\x00\x00\xe8\x00\x00\x00\x00\x83\xc4\x043\xc0\xc3')
        dis = x86Disassembler(code)    
        dis.disasm()

    def test_debug_hello_world(self):
        code = x86Block('U\x8b\xec\x83\xec@SVW\x8d}\xc0\xb9\x10\x00\x00\x00\xb8\xcc\xcc\xcc\xcc\xf3\xabh\x00\x00\x00\x00\xe8\x00\x00\x00\x00\x83\xc4\x043\xc0_^[\x83\xc4@;\xec\xe8\x00\x00\x00\x00\x8b\xe5]\xc3')
        dis = x86Disassembler(code)    
        dis.disasm()

if __name__ == '__main__':
    unittest.main()