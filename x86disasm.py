from x86tokens import *
from x86inst import *
from x86PackUnpack import *

class x86Block:
    """
    Arbitrary block of x86 data
    """
    def __init__(self,data='',location=0x0):
        self.Data = data
        self.Location = location
        self.Labels = []
        self.LabelRefs = []

    def unpackFromString(self,f,s):
        ret = struct.unpack(f, self.Data[self.Location:self.Location+s])[0]
        self.Location += s
        return ret
    
    def GetUnsignedByte(self):
        return self.unpackFromString("<B",1)

    def GetUnsignedWord(self):
        return self.unpackFromString("<H",2)

    def GetWord(self):
        return self.unpackFromString("<h",2)

    def GetUnsignedDword(self):
        return self.unpackFromString("<L",4)

    def GetString(self, length):
        return self.unpackFromString("<%ds" % length, length)        
        
class x86Disassembler:
    def __init__(self,code,addr=0x40000000):
        self.Code = code
        self.Address = addr

    def disasm(self):
        while self.Code.Data[self.Code.Location:]:
            op = []
            op.append(self.Code.GetUnsignedByte())
            try:
                while 1:
                    try:
                        inst = opcodeDict.GetOp(tuple(op))
                        break
                    except OpcodeNeedsModRM,x:
                        modRM = struct.unpack("<B", self.Code.Data[self.Code.Location])[0]
                        inst = opcodeDict.GetOp(tuple(op),
                                                modRM=modRM)
                        break
                    except OpcodeTooShort,x:
                        op.append(self.Code.GetUnsignedByte())
            except KeyError,x:
                raise RuntimeError("Unsupported Opcode '%s'" % op)
            instInst = inst.GetInstance()
            #print instInst.Instruction.InstructionString
            try:
                suffixSize = instInst.GetSuffixSize()
            except OpcodeNeedsModRM,x:
                modRM = struct.unpack("<B", self.Code.Data[self.Code.Location])[0]
                suffixSize = instInst.GetSuffixSize(modRM)
            instInst.LoadData(self.Code.GetString(suffixSize))
            instInst.Address = self.Address
            print instInst.OpText()
            self.Address += instInst.GetInstructionSize()
            

