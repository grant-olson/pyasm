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

a = assembler()

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

a.Compile()