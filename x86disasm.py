from x86tokens import *
from x86inst import *
import struct

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
    def __init__(self,code):
        self.Code = code

    def disasm(self):
        while self.Code.Data[self.Code.Location:]:
            op = []
            op.append(self.Code.GetUnsignedByte())
            try:
                try:
                    inst = opcodeDict.GetOp(tuple(op))
                except OpcodeNeedsModRM,x:
                    modRM = struct.unpack("<B", self.Code.Data[self.Code.Location])[0]
                    inst = opcodeDict.GetOp(tuple(op),
                                            modRM=modRM)
            except KeyError,x:
                raise RuntimeError("Unsupported Opcode '%s'" % op)
            print inst.InstructionString,
            print repr(self.Code.GetString(inst.GetSuffixSize()))
            

if __name__ == '__main__':
    code = x86Block('h\x00\x00\x00\x00\xe8\x00\x00\x00\x00\x83\xc4\x043\xc0\xc3')
    dis = x86Disassembler(code)    
    dis.disasm()
