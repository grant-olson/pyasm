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

def possibleImmediateOrRelative(*toks):
    # TODO: can we narrow down which one this should be?
    immediateVals = ['imm32','imm16','imm8','rel32','rel16','rel8']
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
    This is pretty much an r/m value
        i.e. it doesn't make sense to move an r/m8 into an r32
    """    
    possibleVals = []
    lbracket,operand,rest = toks[0],toks[1],toks[2:]

    if operand[0] in (NUMBER,SYMBOL):
        # TODO: CAN WE OPTIMIZE THIS?
        possibleVals.append((OPERAND,'r/m32'))
        possibleVals.append((OPERAND,'r/m16'))
        possibleVals.append((OPERAND,'r/m8'))
    elif operand[0] == REGISTER:        
        regName = operand[1]
        
        if regName in rb:
            possibleVals.append((OPERAND, 'r/m8'))
        elif regName in rw:
            possibleVals.append((OPERAND,'r/m16'))
        elif regName in rd:
            possibleVals.append((OPERAND,'r/m32'))
        else:
            raise RuntimeError("Invalid Register name '%s'" % regName)
    
    while rest[0] != (RBRACKET, ']'):
        rest = rest[1:]
    rest = rest[1:]
    if not rest:
        for val in possibleVals:
            yield [val]
    else:
        possibleLookup = getProperLookup(*rest)
        for val in possibleVals:
            for restMatches in possibleLookup(*rest):
                yldVal = [val]
                yldVal.extend(restMatches)
                yield yldVal

possibleLookups = {
    REGISTER:possibleRegister,
    OPCODE:possibleDefault,
    COMMA:possibleDefault,
    LBRACKET:possibleIndirect,
    NUMBER:possibleImmediateOrRelative,
    SYMBOL:possibleImmediateOrRelative,}

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

class labelDict(dict):
    def __setitem__(self,key,val):
        if self.has_key(key):
            raise x86asmError("Duplicate Label Declaration '%s'" % key)
        else:
            dict.__setitem__(self,key,val)

class data:
    def __init__(self, dat):
        self.Data = dat
        self.Address = 0x0

class procedure:
    def __init__(self,name):
        self.Name = name
        self.Args = []
        self.ArgOffset = 4
        self.Locals = []
        self.LocalOffset = 4
        
    def AddArg(self,name,bytes=4):
        self.Args.append( (name, self.ArgOffset, bytes) )
        self.ArgOffset += bytes

    def AddLocal(self,name,bytes=4):
        self.Locals.append( (name, self.LocalOffset, bytes) )
        self.LocalOffset += bytes

    def LookupArg(self,name):
        for x in self.Args:
            if x[0] == name:
                return ( (LBRACKET, '['), (REGISTER,'EBP'),(NUMBER, -x[1]), (RBRACKET,']') )
        return None

    def LookupLocal(self,name):
        for x in self.Locals:
            if x[0] == name:
                return ( (LBRACKET, '['), (REGISTER,'EBP'),(NUMBER, x[1]), (RBRACKET,']') )
        return None
       
    def LookupVar(self, name):
        retVal = self.LookupArg(name)
        if retVal is None:
            retVal = self.LookupLocal(name)
        return retVal
    
class assembler:
    def __init__(self):
        self.Instructions = []
        self.Data = []
        self.Labels = {}
        self.CurrentProcedure = None

    def registerLabel(self,lbl):
        if self.Labels.has_key(lbl.Name):
            raise RuntimeError("Duplicate Label Registration [%s]" % lbl.Name)
        self.Labels[lbl.Name] = lbl
        
    def AddInstruction(self,inst):
        instToks = tokenizeInst(inst)
        instToksMinusLocals = ()
        for tok in instToks:
            if tok[0] != SYMBOL: # do nothing
                instToksMinusLocals += ( tok,)
            else: #look for local match
                local = self.CurrentProcedure.LookupVar(tok[1])
                if local: #found match
                    instToksMinusLocals += local
                else: # defer resolution to second pass
                    instToksMinusLocals += (tok,)
        print(instToksMinusLocals)
        self.Instructions.append(instToksMinusLocals)

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

    def AddProcedure(self,name):
        proc = procedure(name)
        self.registerLabel(proc)
        self.CurrentProcedure = proc

    def AP(self,name):
        self.AddProcedure(name)

    def AddArgument(self,name):
        self.CurrentProcedure.AddArg(name)

    def AA(self,name):
        self.AddArgument(name)

    def AddLocal(self,name):
        self.CurrentProcedure.AddLocal(name)

import unittest

class assemblerTests(unittest.TestCase):
    def test_basic_assembler(self):
        a = assembler()
        a.AD('hw_string','Hello, World!\n\0')
        a.AP('_main')
        a.AI('PUSH hw_string')
        a.AI('CALL _printf')
        a.AI('ADD ESP,4')
        a.AI('XOR EAX,EAX')
        a.AI('RET')
        
        a.AP('_main2')
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
        
if __name__ == '__main__':
    unittest.main()
    