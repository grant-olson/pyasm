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
        self.failUnlessRaises(RuntimeError,printBestMatch,"MOV [EAX],[EBX]")
        
        
    def test_invalid_combos(self):
        "Can't move different sized registers back and forth"
        self.failUnlessRaises(RuntimeError,printBestMatch,"MOV AX,AL")
        self.failUnlessRaises(RuntimeError,printBestMatch,"MOV AL,EAX")
        self.failUnlessRaises(RuntimeError,printBestMatch,"MOV [EAX],AX")
        self.failUnlessRaises(RuntimeError,printBestMatch,"MOV EAX,[AX]")

    def test_symbol_resolution(self):
        printBestMatch('PUSH hw_string')
        printBestMatch('CALL _printf')
        
if __name__ == '__main__':
    unittest.main()