import unittest
from pyasm.x86tokenizer import *

class x86tokenizer_test(unittest.TestCase):
    def test_res(self):
        """
        Just make sure that our re's don't throw an error while being parsed
        by the engine
        """
        re.compile(opcodeRe)
        re.compile(operandRe)
        re.compile(commaRe)
        re.compile(defRegRe)
        re.compile(basicRegisterRe)
        re.compile(lbracketRe)
        re.compile(rbracketRe)
        re.compile(numberRe)
        re.compile(symbolRe)
        re.compile(instRegRe)

    def test_tokenizeInst(self):
        """
        Test various inputs to this function
        """
        self.assertEquals(tokenizeInst('PUSH hw_string'),
                          ((OPCODE, 'PUSH'), (SYMBOL, 'hw_string')))
        self.assertEquals(tokenizeInst('CALL _printf'),
                          ((OPCODE, 'CALL'), (SYMBOL, '_printf')))
        self.assertEquals(tokenizeInst('ADD ESP,4'),
                          ((OPCODE, 'ADD'), (REGISTER, 'ESP'),
                           (COMMA, ','), (NUMBER, '4')))
        self.assertEquals(tokenizeInst('XOR EAX,EAX'),
                          ((OPCODE, 'XOR'), (REGISTER, 'EAX'),
                           (COMMA, ','), (REGISTER, 'EAX')))
        self.assertEquals(tokenizeInst('MOV [EAX],12'),
                          ((OPCODE, 'MOV'), (LBRACKET, '['), (REGISTER, 'EAX'),
                           (RBRACKET, ']'), (COMMA, ','), (NUMBER, '12')))
        self.assertEquals(tokenizeInst('MOV [EAX+0xCC],12'),
                          ((OPCODE, 'MOV'), (LBRACKET, '['), (REGISTER, 'EAX'),
                           (NUMBER, '+0xCC'),(RBRACKET, ']'), (COMMA, ','),
                           (NUMBER, '12')))
        self.assertEquals(tokenizeInst('MOV [EAX+12],12'),
                          ((OPCODE, 'MOV'), (LBRACKET, '['), (REGISTER, 'EAX'),
                           (NUMBER, '+12'), (RBRACKET, ']'), (COMMA, ','),
                           (NUMBER, '12')))
        self.assertEquals(tokenizeInst('RET'),((OPCODE, 'RET'),))

if __name__ == '__main__':
    unittest.main()

    