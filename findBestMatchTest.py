"""
Tries to lookup a physical instruction based on the string.
Need to do a lot more here.

    + Better handling of r/m stuff.
    + Save values so we can actually build the instanciated instruction.
    + Figure out where we really want this in our file structure.
"""    

from x86tokenizer import (tokenizeInst,
                          REGISTER,OPCODE,COMMA,OPERAND,
                          LBRACKET,RBRACKET,NUMBER,SYMBOL)

from x86inst import mnemonicDict

def possibleDefault(*toks):
    "By default, a token will just yield itself."
    first,rest = toks[0],toks[1:]
    if not rest:
        yield [first]
    else:
        i = 1
        possibleLookup = getProperLookup(*rest)
        for restMatches in possibleLookup(*rest):
            i += 1
            yldVal = [first]
            yldVal.extend(restMatches)
            yield yldVal

def possibleImmediate(*toks):
    immediateVals = ['imm32','imm16','imm8']
    first,rest = toks[0],toks[1:]
    if not rest:
        for val in immediateVals:
            yield [(OPERAND, val)]
    else:
        possibleLookup = getProperLookup(*rest)
        for val in immediateVals:
            for restMatches in possibleLookup(*rest):
                yldVal = [(OPERAND,val)]
                yldVal.extend(restMatches)
                yield yldVal

def possibleRelative(*toks):
    relativeVals = ['rel32','rel16','rel8']
    first,rest = toks[0],toks[1:]
    if not rest:
        for val in relativeVals:
            yield [(OPERAND,val)]
    else:
        possibleLookup = getProperLookup(*rest)
        for val in relativeVals:
            for restMatches in possibleLookup(*rest):
                yldVal = [(OPERAND,val)]
                yldVal.extend(restMatches)
                yield yldVal

def possibleRegister(*toks):
    """
    Registers may be hardcoded for superfast lookups, or an r or r/m value.
    We could probably optimize better with a better understanding of the environment.
        i.e. it doesn't make sense to move an r/m8 into an r32
    """    
    registerVals = [(REGISTER, '%s' % toks[0][1]),
                    (OPERAND,'r32'),(OPERAND,'r16'),(OPERAND,'r8'),
                    (OPERAND,'r/m32'),(OPERAND,'r/m16'),(OPERAND,'r/m8')]
    first,rest = toks[0],toks[1:]
    if not rest:
        for val in registerVals:
            yield [val]
    else:
        possibleLookup = getProperLookup(*rest)
        for val in registerVals:
            for restMatches in possibleLookup(*rest):
                yldVal = [val]
                yldVal.extend(restMatches)
                yield yldVal

def possibleIndirect(*toks):
    """
    Registers may be hardcoded for superfast lookups, or an r or r/m value.
    We could probably optimize better with a better understanding of the environment.
        i.e. it doesn't make sense to move an r/m8 into an r32
    """    
    registerVals = [(OPERAND,'r/m32'),(OPERAND,'r/m16'),(OPERAND,'r/m8')]
    first,rest = toks[0],toks[1:]
    while rest[0] != (RBRACKET, ']'):
        rest = rest[1:]
    rest = rest[1:]
    if not rest:
        for val in registerVals:
            yield [val]
    else:
        possibleLookup = getProperLookup(*rest)
        for val in registerVals:
            for restMatches in possibleLookup(*rest):
                yldVal = [val]
                yldVal.extend(restMatches)
                yield yldVal

possibleLookups = {
    REGISTER:possibleRegister,
    OPCODE:possibleDefault,
    COMMA:possibleDefault,
    LBRACKET:possibleIndirect,
    NUMBER:possibleImmediate,
    SYMBOL:possibleDefault,}

def getProperLookup(*toks):
    return possibleLookups[toks[0][0]]

def findBestMatch(s):
    retVal = None
    toks = tokenizeInst(s)
    for x in possibleDefault(*toks):
        y = tuple(x)
        if mnemonicDict.has_key(y):
            retVal = mnemonicDict[y]
            break
    if retVal:
        return retVal
    else:
        raise RuntimeError("Unable to find match for '%s'" % s)

def testBestMatch(s):
    print "Best match for '%s' => '%s'" % (s,findBestMatch(s).InstructionString)

import unittest

class test_lookups(unittest.TestCase):
    def test_simple_matches(self):
        testBestMatch("MOV EAX, 12")
        testBestMatch("MOV EAX,EBX")
        testBestMatch("MOV [EAX],12")
        testBestMatch("MOV [EAX-4],12")

if __name__ == '__main__':
    unittest.main()