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

from x86inst import mnemonicDict, rb, rw, rd, instructionInstance

import types

class x86asmError(Exception): pass

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
        raise x86asmError("Invalid Register name '%s'" % regName)

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
            raise x86asmError("Invalid Register name '%s'" % regName)
    
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

def findBestMatchTokens(toks):
    retVal = None
    for x in possibleDefault(*toks):
        y = tuple(x)
        if mnemonicDict.has_key(y):
            retVal = mnemonicDict[y]
            break
    if retVal:
        return retVal
    else:
        raise x86asmError("Unable to find match for " + `toks`)
    
def findBestMatch(s):
    toks = tokenizeInst(s)
    try:
        return findBestMatchTokens(toks)
    except x86asmError:
        raise x86asmError("Unable to find match for '%s'" % s)

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
        self.Address = 0x0
        
        self.Args = []
        self.ArgOffset = 4
        self.Locals = []
        self.LocalOffset = 4
        self.Frozen = 0
        
    def AddArg(self,name,bytes=4):
        if self.Frozen:
            raise x86asmError("Cannot add arg %s to procedure %s." \
                              "This must happen before instrutions are" \
                              "added." % (self.Name, name))
        self.Args.append( (name, self.ArgOffset, bytes) )
        self.ArgOffset += bytes

    def AddLocal(self,name,bytes=4):
        if self.Frozen:
            raise x86asmError("Cannot add arg %s to procedure %s." \
                              "This must happen before instrutions are" \
                              "added." % (self.Name, name))
        self.Locals.append( (name, self.LocalOffset, bytes) )
        self.LocalOffset += bytes

    def LookupArg(self,name):
        for x in self.Args:
            if x[0] == name:
                return ( (LBRACKET, '['), (REGISTER,'EBP'),(NUMBER, str(x[1])),
                         (RBRACKET,']') )
        return None

    def LookupLocal(self,name):
        for x in self.Locals:
            if x[0] == name:
                return ( (LBRACKET, '['), (REGISTER,'EBP'),(NUMBER, str(-x[1])),
                         (RBRACKET,']') )
        return None
       
    def LookupVar(self, name):
        retVal = self.LookupArg(name)
        if retVal is None:
            retVal = self.LookupLocal(name)
        return retVal

    def EmitProcStartCode(self, a):
        """
        Save EBP
        Copy ESP so we can use it to reference params and locals
        Subtrack 
        """
        a.AI("PUSH EBP")
        a.AI("MOV EBP, ESP")
        a.AI("SUB ESP, %s" % self.LocalOffset)

    def EmitProcEndCode(self, a):
        """
        Restore settings and RETurn
        TODO: Do we need to handle a Return value here?
        """
        a.AI("ADD ESP, %s" % self.LocalOffset)
        a.AI("MOV ESP, EBP")
        a.AI("POP EBP")
        a.AI("RET")
        
class assembler:
    def __init__(self):
        self.Instructions = []
        self.Data = []
        self.Labels = {}
        self.CurrentProcedure = None
        self.StartAddress = 0x04000000

    def registerLabel(self,lbl):
        if self.Labels.has_key(lbl.Name):
            raise x86asmError("Duplicate Label Registration [%s]" % lbl.Name)
        self.Labels[lbl.Name] = lbl
        self.Instructions.append(lbl)

    #
    # Write assmebly code
    #
    def AddInstruction(self,inst):
        instToks = tokenizeInst(inst)
        instToksMinusLocals = ()
        if self.CurrentProcedure: # may have locals
            for tok in instToks:
                if tok[0] != SYMBOL: # do nothing
                    instToksMinusLocals += ( tok,)
                else: #look for local match
                    local = self.CurrentProcedure.LookupVar(tok[1])
                    if local: #found match
                        instToksMinusLocals += local
                    else: # defer resolution to second pass
                        instToksMinusLocals += (tok,)
        else: # no locals, don't try to substitute
            instToksMinusLocals = instToks
        self.Instructions.append(instToksMinusLocals)

    def AI(self,inst):
        if self.CurrentProcedure and not self.CurrentProcedure.Frozen:
            #initialize proc
            self.CurrentProcedure.Frozen = 1
            self.CurrentProcedure.EmitProcStartCode(self)
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
        if self.CurrentProcedure: # didn't emit procedure cleanup code
            raise x86asmError("Must end procedure '%s' before starting proc " \
                              " '%s'" % (self.CurrentProcedure.Name, name))
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

    def EndProc(self):
        if self.CurrentProcedure:
            self.CurrentProcedure.EmitProcEndCode(self)
            self.CurrentProcedure = None

    def EP(self):
        self.EndProc()
            
    #
    # end write assembly code
    #

    #
    # start actual compilation code
    #
    def pass1(self):
        newInsts = []
        currentAddress = self.StartAddress
        for i in self.Instructions:
            if type(i) == types.TupleType: # and instruction to lookup
                inst = findBestMatchTokens(i).GetInstance()
                inst.LoadConcreteValues(i)
                inst.Address = currentAddress
                currentAddress += inst.GetInstructionSize()
                newInsts.append(inst)
            else: # a label
                i.Address = currentAddress
                newInsts.append(i)
        for i in newInsts:
            if isinstance(i, instructionInstance):
                #print "%08X: %s " % (i.Address, i.Instruction.InstructionString)
                print i.OpText()
            else:
                print "%08X: %s" % (i.Address, i.Name)
            
    def Compile(self):
        self.pass1()

if __name__ == '__main__':
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

    a.Compile()    