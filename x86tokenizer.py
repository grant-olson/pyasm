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

#
class tokenizeError(Exception):pass

#token IDs
REGISTER,OPCODE,COMMA,OPERAND,LBRACKET,RBRACKET,NUMBER,SYMBOL = range(1,9)

tokLookup = {'REGISTER':REGISTER,
             'OPCODE':OPCODE,
             'COMMA':COMMA,
             'OPERAND':OPERAND,
             'LBRACKET':LBRACKET,
             'RBRACKET':RBRACKET,
             'NUMBER':NUMBER,
             'SYMBOL':SYMBOL,
             }
#Re's

# Re's used by both tokeinizers
opcodeRe = '(?P<OPCODE>[A-Z]+)'
commaRe = '(?P<COMMA>,)'

# Instruction defs can have hard-coded indirect r/m's in them.
# An actual instruction will extract the LBRACKET and RBRACKET
# and include any appropriate offsets: 'MOV [EDP + 4], AX'
# This will never happen in an instruction def so we need to parse differently
basicRegisterRe = 'AL|CL|DL|BL|AH|CH|DH|BH|AX|CX|DX|BX|SP|BP|SI|DI|'\
        'EAX|ECX|EDX|EBX|ESP|EBP|ESI|EDI'
indirectRegisterRe = '\[AL\]|\[CL\]|\[DL\]|\[BL\]|\[AH\]|\[CH\]|\[DH\]|\[BH\]|'\
        '\[AX\]|\[CX\]|\[DX\]|\[BX\]|\[SP\]|\[BP\]|\[SI\]|\[DI\]|'\
        '\[EAX\]|\[ECX\]|\[EDX\]|\[EBX\]|\[ESP\]|\[EBP\]|\[ESI\]|\[EDI\]'
defRegRe = '(?P<REGISTER>%s|%s)' % (basicRegisterRe,indirectRegisterRe)
instRegRe= '(?P<REGISTER>%s)' % (basicRegisterRe)

# def specific stuff
#operandRe = '(?P<OPERAND>[a-z/:0-9]+)'
#TODO: fix this better
ptrRe = 'ptr16\:16|ptr32\:32'
memRe = 'm16\:16|m32\:32'
sregRe = 'Sreg'
moffsRe = 'moffs8|moffs16|moffs32'
immediateRe = 'imm8|imm16|imm32'
relativeRe = 'rel8|rel16|rel32'
rRe = 'r8|r16|r32'
mmRe = 'mm|xmm'
rmRe = 'r/m8|r/m16|r/m32|m8|m16|m32|m'
otherRe = '/digit|REG'
operandRe = '(?P<OPERAND>%s|%s|%s|%s|%s|%s|%s|%s|%s|%s)' % (ptrRe, memRe, sregRe,
                                                            moffsRe, immediateRe,
                                                            relativeRe, rRe, mmRe,
                                                            rmRe, otherRe)

#instructionRe specific stuff

lbracketRe = '(?P<LBRACKET>\[)'
rbracketRe = '(?P<RBRACKET>\])'
numberRe = '(?P<NUMBER>[\+\-]?(0x[0-9A-Fa-f]+|[0-9]+))'
symbolRe = '(?P<SYMBOL>[a-z_]+)'

#define final re's
instructionDefRe = re.compile("(?:\s*(?:%s|%s|%s|%s)(?P<rest>.*))" % \
                           (defRegRe,operandRe,opcodeRe,commaRe))

instructionRe = re.compile("(?:\s*(?:%s|%s|%s|%s|%s|%s|%s)(?P<rest>.*))" % \
                           (lbracketRe,rbracketRe,instRegRe,
                            opcodeRe,commaRe,numberRe,symbolRe))

def tokenizeString(s,reToProcess):
    lst = []
    rest = s
    while rest:
        instMatch = reToProcess.match(rest)
        if not instMatch:
            raise tokenizeError("Couldn't find match for string '%s' from '%s'" % (rest,s))
        
        instDict = instMatch.groupdict()
        if instDict['REGISTER']: lst.append((REGISTER,instDict['REGISTER']))
        elif instDict['OPCODE']: lst.append((OPCODE,instDict['OPCODE']))
        elif instDict['COMMA']: lst.append((COMMA,instDict['COMMA']))
        elif instDict.has_key('OPERAND') and instDict['OPERAND']:
            # only defs have operands.
            #only instructions have anything below here, but if it's a def
            #we've already (hopefully) found a match so we don't need to check
            #for key existance.
            lst.append((OPERAND,instDict['OPERAND']))
        elif instDict['LBRACKET']: lst.append((LBRACKET,instDict['LBRACKET']))
        elif instDict['RBRACKET']: lst.append((RBRACKET,instDict['RBRACKET']))
        elif instDict['NUMBER']: lst.append((NUMBER,instDict['NUMBER']))
        elif instDict['SYMBOL']: lst.append((SYMBOL,instDict['SYMBOL']))
        else:
            raise tokenizeError("Tokenization failed on string %s, match %s" \
                                  % (string,rest))
        rest = instDict['rest']
    return tuple(lst)

def tokenizeInstDef(s):
    toks = tokenizeString(s, instructionDefRe)
    index,length = 0,len(toks)
    if length == 0:
        raise tokenizeError("Invalid Instruction.  Cannot be blank")
    if toks[index][0] != OPCODE:
        raise tokenizeError("Invalid Instruction: '%s' " \
                            "Must start with an OPCODE" % s)
    
    while index < length and toks[index][0] == OPCODE:
        index += 1
        
    while index < length:
        if toks[index][0] not in (REGISTER,OPERAND):
            raise tokenizeError("Invalid Instruction Definition: '%s' " \
                                "Expected a REGISTER OR OPERAND ENTRY" % s)
        index += 1
        if index < length:
            if toks[index][0] != COMMA:
                raise tokenizeError("Invalid Instruction Def: '%s' Expected " \
                                    "a COMMA" % s)
            index += 1
    return toks
    

def tokenizeInst(s):
    toks = tokenizeString(s, instructionRe)
    index,length = 0,len(toks)
    if length == 0:
        raise tokenizeError("Invalid Instruction.  Cannot be blank")
    if toks[index][0] != OPCODE:
        raise tokenizeError("Invalid Instruction: '%s' " \
                            "Must start with an OPCODE" % s)
    
    while index < length and toks[index][0] == OPCODE:
        index += 1
        
    while index < length:
        if toks[index][0] in (REGISTER,NUMBER,SYMBOL):
            index += 1
        elif toks[index][0] == LBRACKET:
            index += 1
            if toks[index][0] != REGISTER:
                raise tokenizeError("Invalid Instruction: '%s'  Expected a " \
                                    "REGISTER inside the [brackets]" %s)
            else:
                index += 1
                if toks[index][0] == NUMBER:
                    index += 1
                if toks[index][0] != RBRACKET:
                    raise tokenizeError("Invalid Instruction: '%s' Expected an " \
                                        "ending BRACKET here." % s)
                else:
                    index += 1
        else:
            raise tokenizeError("Invalid Instruction: '%s' " \
                                "Expected a REGISTER,LBRACKET,NUMBER,or SYMBOL" % s)

        if index < length:
            if toks[index][0] != COMMA:
                raise tokenizeError("Invalid Instruction: '%s' Expected " \
                                    "a COMMA" % s)
            index += 1
    return toks