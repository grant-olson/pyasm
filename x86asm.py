"""
x86asm.py
---------

Ultimately create a two-pass assembler so we can assemble raw machine code.
We will also want to come up with some way to load code straight into memory
at runtime instead of just generating coff files.

I need to get the instruction tokenizer working for this to take off.
"""
from x86tokenizer import (tokenizeInst,
                          REGISTER,OPCODE,COMMA,OPERAND,
                          LBRACKET,RBRACKET,NUMBER,SYMBOL)

from x86inst import mnemonicDict, rb, rw, rd

###########################################################
## Find right instruction def based on concrete instruction
###########################################################

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
    regName = toks[0][1]
    registerVals = [(REGISTER, '%s' % regName)]
    if regName in rb:
        registerVals.append((OPERAND,'r8'))
        registerVals.append((OPERAND, 'r/m8'))
    elif regName in rw:
        registerVals.append((OPERAND, 'r16'))
        registerVals.append((OPERAND,'r/m16'))
    elif regName in rd:
        registerVals.append((OPERAND,'r32'))
        registerVals.append((OPERAND,'r/m32'))
    else:
        raise RuntimeError("Invalid Register name '%s'" % regName)

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
    registerVals = []
    lbracket,register,rest = toks[0],toks[1],toks[2:]
    regName = register[1]
    
    if regName in rb:
        registerVals.append((OPERAND, 'r/m8'))
    elif regName in rw:
        registerVals.append((OPERAND,'r/m16'))
    elif regName in rd:
        registerVals.append((OPERAND,'r/m32'))
    else:
        raise RuntimeError("Invalid Register name '%s'" % regName)
    
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
    SYMBOL:possibleImmediate,}

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

def printBestMatch(s):
    print "Best match for '%s' => '%s'" % (s,findBestMatch(s).InstructionString)

##################################################################
## END OF Find right instruction def based on concrete instruction
##################################################################

class labelRef:
    def __init__(self, name):
        self.Name = name
        
class label:
    def __init__(self, name):
        self.Name = name
        self.Address = 0x0
        
class data:
    def __init__(self, dat):
        self.Data = dat
        self.Address = 0x0


class assembler:
    def __init__(self):
        self.Instructions = []
        self.Data = []
        self.Labels = {}

    def registerLabel(self,lbl):
        if self.Labels.has_key(lbl.Name):
            raise RuntimeError("Duplicate Label Registration [%s]" % lbl.Name)
        self.Labels[lbl.Name] = lbl
        
    def AddInstruction(self,inst):
        printBestMatch(inst)
        self.Instructions.append(inst)

    def AI(self,inst):
        self.AddInstruction(inst)

    def AddInstructionLabel(self,name):
        lbl = label(name)
        self.registerLabel(lbl)
        self.Instructions.append(lbl)

    def AIL(self,name):
        self.AddInstructionLabel(name)

    def AddData(self,name,dat):
        lbl = label(name)
        self.registerLabel(lbl)
        self.Data.append(lbl)
        self.Data.append(data(dat))

    def AD(self,name,dat):
        self.AddData(name,dat)


if __name__ == '__main__':
    a = assembler()
    a.AD('hw_string','Hello, World!\n\0')
    a.AIL('_main')
    a.AI('PUSH hw_string')
    a.AI('CALL _printf')
    a.AI('ADD ESP,4')
    a.AI('XOR EAX,EAX')
    a.AI('RET')

    