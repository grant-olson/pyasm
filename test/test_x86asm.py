# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

import unittest
from pyasm.x86asm import *

class test_instruction_lookups(unittest.TestCase):
    
    def test_simple_matches(self):
        self.assertEquals(findBestMatch("MOV EAX, 12").InstructionString,'MOV EAX,imm32')
        self.assertEquals(findBestMatch("MOV EAX,EBX").InstructionString,'MOV r32,r/m32')
        self.assertEquals(findBestMatch("MOV [EAX],12").InstructionString,'MOV r/m32,imm32')
        self.assertEquals(findBestMatch("MOV [EAX-4],12").InstructionString,'MOV r/m32,imm32')

    def test_byte_word_matches(self):
        self.assertEquals(findBestMatch("MOV AL,3").InstructionString,'MOV AL,imm8')
        self.assertEquals(findBestMatch("MOV AX,BX").InstructionString,'MOV r16,r/m16')

    def test_register_memory(self):
        self.assertEquals(findBestMatch("MOV [EAX],EBX").InstructionString,'MOV r/m32,r32')
        self.assertEquals(findBestMatch("MOV EAX,[EBX]").InstructionString,'MOV r32,r/m32')
        self.assertEquals(findBestMatch("MOV EAX, EBX").InstructionString,'MOV r32,r/m32')
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV [EAX],[EBX]")
        self.assertEquals(findBestMatch("MOV [0x1234],EAX").InstructionString,'MOV r/m32,r32')
        self.assertEquals(findBestMatch("MOV [foo],EAX").InstructionString,'MOV r/m32,r32')
        
        
    def test_invalid_combos(self):
        "Can't move different sized registers back and forth"
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV AX,AL")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV AL,EAX")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV [EAX],AX")
        self.failUnlessRaises(x86asmError,printBestMatch,"MOV EAX,[AX]")

    def test_symbol_resolution(self):
        self.assertEquals(findBestMatch('PUSH hw_string').InstructionString,'PUSH imm32')
        self.assertEquals(findBestMatch('CALL _printf').InstructionString,'CALL rel32')

class assemblerTests(unittest.TestCase):
    def test_basic_assembler(self):
        a = assembler()
        a.ADStr('hw_string','Hello, World!\n\0')
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

    def test_constants(self):
        a = assembler()
        a.AC("foo","0x4")
        a.AI("MOV EBX,[EAX+foo]")
        self.assertEquals(a.Instructions,[((2, 'MOV'), (1, 'EBX'), (3, ','),
                                            (5, '['), (1, 'EAX'), (7, '0x4'),
                                            (6, ']'))])
        
if __name__ == '__main__':
    unittest.main()