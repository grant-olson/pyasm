"""
x86tokenizer.py
---------------

This provides the framework to tokenize x86 instructions from strings.  There
are two major functions:

tokenizeInstDef()
    This tokenizes an instruction definition so we can build the appropriate
    tables to lookup at a later date.

tokenizeInst()
    This tokenizes an actual instruction, in code, to help build an instruction
    instance.

Much of the stuff going on here is the same, but an actual instruction may (and
will) contain info that is invalid for a definition.  i.e.::

    # an instance can have concrete values, but a def can't
    tokenizeInst("MOV EAX,0xF000")
    tokenizeInst("MOV [EBP+8],0x10")

Of course I still need to implement the tokenizeInst function.    
"""    

import re

opcodeRe = '(?P<opcode>[A-Z]+)'
operandRe = '(?P<operand>[a-z/:0-9]+)'
commaRe = '(?P<comma>[,]+)'
regRe = '(?P<register>AL|CL|DL|BL|AH|CH|DH|BH|AX|CX|DX|BX|SP|BP|SI|DI|'\
        'EAX|ECX|EDX|EBX|ESP|EBP|ESI|EDI|'\
        '\[AL\]|\[CL\]|\[DL\]|\[BL\]|\[AH\]|\[CH\]|\[DH\]|\[BH\]|'\
        '\[AX\]|\[CX\]|\[DX\]|\[BX\]|\[SP\]|\[BP\]|\[SI\]|\[DI\]|'\
        '\[EAX\]|\[ECX\]|\[EDX\]|\[EBX\]|\[ESP\]|\[EBP\]|\[ESI\]|\[EDI\])'
instructionRe = re.compile("(?:\s*(?:%s|%s|%s|%s)(?P<rest>.*))" % \
                           (regRe,opcodeRe,commaRe,operandRe))
REGISTER,OPCODE,COMMA,OPERAND = range(1,5)

def tokenizeInstDef(instString):
    lst = []
    rest = instString
    while rest:
        instDict = instructionRe.match(rest).groupdict()
        if instDict['register']: lst.append((REGISTER,instDict['register']))
        if instDict['operand']: lst.append((OPERAND,instDict['operand']))
        if instDict['opcode']: lst.append((OPCODE,instDict['opcode']))
        if instDict['comma']: lst.append((COMMA,instDict['comma']))
        rest = instDict['rest']
    return tuple(lst)

