import unittest
from pyasm.x86asm import *

class test_instruction_lookups(unittest.TestCase):
    
    def test_simple_matches(self):
        printBestMatch("MOV EAX, 12")
        printBestMatch("MOV EAX,EBX")
        printBestMatch("MOV [EAX],12")
        printBestMatch("MOV [EAX-4],12")

    def test_byte_word_matches(self):
        printBestMatch("MOV AL,3")
        printBestMatch("MOV AX,BX")

    def test_register_memory(self):
        printBestMatch("MOV [EAX],EBX")
        printBestMatch("MOV EAX,[EBX]")
        printBestMatch("MOV EAX, EBX")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV [EAX],[EBX]")
        printBestMatch("MOV [0x1234],EAX")
        printBestMatch("MOV [foo],EAX")
        
        
    def test_invalid_combos(self):
        "Can't move different sized registers back and forth"
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV AX,AL")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV AL,EAX")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV [EAX],AX")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV EAX,[AX]")

    def test_symbol_resolution(self):
        printBestMatch('PUSH hw_string')
        printBestMatch('CALL _printf')

class assemblerTests(unittest.TestCase):
    def test_basic_assembler(self):
        a = assembler()
        a.AD('hw_string','Hello, World!\n\0')
        a.AIL('_main')
        a.AI('PUSH hw_string')
        a.AI('CALL _printf')
        a.AI('ADD ESP,4')
        a.AI('XOR EAX,EAX')
        a.AI('RET')
        
        a.AIL('_main2')
        a.AI('PUSH hw_string')
        a.AI('CALL _printf')
        a.AI('ADD ESP,4')
        a.AI('XOR EAX,EAX')
        a.AI('RET')

    def test_proc_locals(self):
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

    def test_proc_end(self):
        a = assembler()
        a.AP('foo')
        a.AI('XOR EAX,EAX')
        self.failUnlessRaises(x86asmError, a.AP, 'bar')

    def test_no_args_after_code(self):
        a = assembler()
        a.AP("foo")
        a.AA("bar")
        a.AI("MOV bar, 4")
        self.failUnlessRaises(x86asmError,a.AA,"baz")
        a.EP()

    def test_no_locals_after_code(self):
        a = assembler()
        a.AP("foo")
        a.AddLocal("bar")
        a.AI("MOV bar, 4")
        self.failUnlessRaises(x86asmError,a.AddLocal,"baz")
        a.EP()
        
if __name__ == '__main__':
    unittest.main()