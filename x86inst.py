"""
x86inst.py
----------

This contains the core functionality to handle x86 instructions.  We need to
build definition tables, so that instructions can be converted to/from
mneumonics durring assembly/disassembly phases.

At some point we'll need to deal with forward references and symbols, but
not today.
"""

import struct
from pickle import decode_long, encode_long
from x86tokenizer import (tokenizeInstDef,REGISTER,OPCODE,COMMA,OPERAND,
                          LBRACKET, RBRACKET,NUMBER,SYMBOL)

class OpcodeTooShort(Exception):pass
class OpcodeNeedsModRM(Exception):pass # for /d info and SIB calculation
class x86instError(Exception):pass

opcodeFlags = ['/0','/1','/2','/3','/4','/5','/6','/7',
               '/r',
               'cb','cw','cd','cp',
               'ib','iw','id',
               '+rb','+rw','+rd',
               '+i'
               ]

instModRM = ['r/m8','r/m16','r/m32','r8','r16','r32']

immediate = ['imm8','imm16','imm32']
displacement = ['rel8','rel16','rel32']

rb =['AL','CL','DL','BL','AH','CH','DH','BH']
rw = ['AX','CX','DX','BX','SP','BP','SI','DI']
rd = ['EAX','ECX','EDX','EBX','ESP','EBP','ESI','EDI']

regOpcode = {
    'r8':['AL','CL','DL','BL','AH','CH','DH','BH'],
    'r16':['AX','CX','DX','BX','SP','BP','SI','DI'],
    'r32':['EAX','ECX','EDX','EBX','ESP','EBP','ESI','EDI'],
    'mm':['MM0','MM1','MM2','MM3','MM4','MM5','MM6','MM7'],
    'xmm':['XMM0','XMM1','XMM2','XMM3','XMM4','XMM5','XMM6','XMM7'],
    '/digit':[0,1,2,3,4,5,6,7],
    'REG':[0,1,2,3,4,5,6,7],
    }

mode1 = ['[EAX]','[ECX]','[EDX]','[EBX]','[--][--]','disp32','[ESI]','[EDI]']
mode2 = ['[EAX+disp8]','[ECX+disp8]','[EDX+disp8]','[EBX+disp8]',
         '[--][--]+disp8','[EBP+disp8]','[ESI+disp8]','[EDI+disp8]']
mode3 = ['[EAX+disp32]','[ECX+disp32]','[EDX+disp32]','[EBX+disp32]',
         '[--][--]+disp32','[EBP+disp8]','[ESI+disp8]','[EDI+disp8]']     



#
# These could be 16, but that doesn't make since for windows
# They are overridden with opcode prefixes
#
DefaultOperandSize = 32

class OpcodeDict(dict):
    """
    Holds instructions by opcode for lookup.
    If you get an OpcodeTooShort exception, you need to keep on grabbing bytes
    until you get a good opcode.
    """
    def __getitem__(self,key):
        retVal = dict.__getitem__(self,key)
        if retVal == None:
            raise OpcodeTooShort()
        return retVal

    def __setitem__(self,key,value):
        if self.has_key(key):
            dict.__getitem__(self,key).append(value)
        else:
            dict.__setitem__(self,key,[value])
        # Sentinel for multi-byte opcodes
        if len(key) > 1:
            for i in range(1,len(key)):
                tmpKey = key[:i]
                dict.__setitem__(self,tmpKey,None)
                
    def GetOp(self,opcode,modRM=None):
        lst = self.__getitem__(opcode)
        
        if modRM is not None:
            mrm = ModRM(modRM)
            digit = "/%s" % mrm.RegOp
            lst = [item for item in lst if digit in item.OpcodeFlags]
            
        if DefaultOperandSize == 16:
            lst = [item for item in lst if item.InstructionString.find('r32') == -1]
            lst = [item for item in lst if item.InstructionString.find('r/m32') == -1]
            lst = [item for item in lst if item.InstructionString.find('imm32') == -1]
            lst = [item for item in lst if item.InstructionString.find('rel32') == -1]
            lst = [item for item in lst if item.InstructionString.find('m32') == -1]
            lst = [item for item in lst if 'rd' not in item.OpcodeFlags]
        elif DefaultOperandSize == 32:
            lst = [item for item in lst if item.InstructionString.find('r16') == -1]
            lst = [item for item in lst if item.InstructionString.find('r/m16') == -1]
            lst = [item for item in lst if item.InstructionString.find('imm16') == -1]
            lst = [item for item in lst if item.InstructionString.find('rel16') == -1]
            lst = [item for item in lst if item.InstructionString.find('m16') == -1]
            lst = [item for item in lst if 'rw' not in item.OpcodeFlags]
        else:
            raise RuntimeError("Invalid DefaultOperandSize")

                
        if len(lst) == 0:
            raise RuntimeError("Invalid/Unimplemented Opcode [%s]" % opcode)
        elif len(lst) > 1:
            # try to figure out what we need
            op = lst[0]
            for flag in op.OpcodeFlags:
                if flag in ('/0','/1','/2','/3','/4','/5','/6','/7'):
                    raise OpcodeNeedsModRM("Opcode %s" % op.Opcode)
            for x in lst:
                print x.Description
            raise RuntimeError("Shouldn't get here")
        else:
            return lst[0]

class MnemonicDict(dict):
    def __setitem__(self,key,val):
        if self.has_key(key):
            raise RuntimeError("Duplicate mnemonic def %s" % `key`)
        dict.__setitem__(self,key,val)

opcodeDict = OpcodeDict()
mnemonicDict = MnemonicDict()
                
def longToBytes(long, bytes=4):
    retVal = [ord(x) for x in encode_long(long)]
    while len(retVal) < bytes:
        retVal.append(0)
    return tuple(retVal)

def longToBytesRepr(long,bytes=4):
    retVal = ""
    for x in longToBytes(long,bytes):
        retVal += "%02X " % x
    return retVal
        
class ModRM:
    def __init__(self,byte=None):
        self.Mode = 0x0
        self.RegOp = 0x0
        self.RM = 0x0
        if byte:
            self.LoadFromByte(byte)

    def LoadFromByte(self,byte):
            self.RegOp = byte & 0x38
            self.RegOp = self.RegOp >> 3
            self.RM = byte & 0x7
            self.Mode = byte & 192
            self.Mode = self.Mode >> 6

    def SaveToByte(self):
        return (self.Mode << 6) + (self.RegOp << 3) + self.RM

    def HasSIB(self):
        if self.Mode in (0,1,2) and self.RM == 4:
            return True
        else:
            return False

    def RegOpString(self,typ):
        return regOpcode[typ][self.RegOp]

    def RMString(self,typ=None):
        retVal = ""
        if self.Mode == 0:
            retVal = mode1[self.RM]
        elif self.Mode == 1:
            retVal = mode2[self.RM]
        elif self.Mode == 2:
            retVal = mode3[self.RM]
        elif self.Mode == 3:
            if typ == 'r/m8':
                retVal = regOpcode['r8'][self.RM]
            elif typ == 'r/m16':
                retVal = regOpcode['r16'][self.RM]
            elif typ == 'r/m32':
                retVal = regOpcode['r32'][self.RM]
            else:
                raise RuntimeError("Invalid r/m type")
        else:
            raise RuntimeError("Invalid Mode")
        return retVal

    def GetDisplacementSize(self):
        "We only know this at runtime with real values"
        if self.Mode == 0 and self.RM == 5:
            return 4
        elif self.Mode == 1:
            return 1
        elif self.Mode == 2:
            return 4
        else:
            return 0
        
class instruction:
    def __init__(self,opstr,inststr,desc):
        self.OpcodeString = opstr
        self.InstructionString = inststr
        self.Description = desc

        self.Opcode = []
        self.OpcodeSize = 0
        self.OpcodeFlags = []

        self.InstructionDef = tokenizeInstDef(self.InstructionString)
        
        self.HasImmediate = False
        self.ImmediateSize = 0 # no of bytes

        self.HasModRM = False        
        self.ModRM = None

        self.HasPrefixes = False        
        self.Prefixes = None

        self.HasDisplacement = False
        self.DisplacementSize = 0

        self.setOpcodeAndFlags()
        self.setHasFlags()

        if '+rb' in self.OpcodeFlags:
            self.loadRBWD('+rb','r8')
        elif '+rw' in self.OpcodeFlags:
            self.loadRBWD('+rw','r16')
        elif '+rd' in self.OpcodeFlags:
            self.loadRBWD('+rd','r32')
        else:
            opcodeDict[self.Opcode] = self
            mnemonicDict[self.InstructionDef] = self

    def loadRBWD(self,plus,reg):
        for i in range(8):
            OS = self.OpcodeString
            IS = self.InstructionString
            ID = self.Description
            OS = OS.replace(plus,plus[1:])
            OS = OS.replace("%X" % self.Opcode[0], '%X' % (self.Opcode[0] + i))
            IS = IS.replace(reg, regOpcode[reg][i])
            instruction(OS,IS,ID)
            
    def setOpcodeAndFlags(self):
        parts = self.OpcodeString.split()
        for part in parts:
            if len(part) == 2 and part[0] in "ABCDEF0123456789" \
               and part[1] in "ABCDEF0123456789":
                # suppose I could use a regex above
                self.Opcode.append(eval("0x%s" % part))
            else:
                self.OpcodeFlags.append(part)

        self.Opcode = tuple(self.Opcode)
        self.OpcodeSize = len(self.Opcode)
                
    def setHasFlags(self):
        for i in instModRM:
            if i in self.InstructionString:
                if "+rb" in self.OpcodeFlags: break
                if "+rw" in self.OpcodeFlags: break
                if "+rd" in self.OpcodeFlags: break
                self.HasModRM = True
                break
        for i in immediate:
            if i in self.InstructionString:
                #hack fix, how do we do this right?
                #if i.startswith('m') and 'imm' in self.InstructionString:
                #    continue
                self.HasImmediate = True
                if i.endswith('8') or i == 'mo':
                    self.ImmediateSize = 1
                elif i.endswith('16'):
                    self.ImmediateSize = 2
                elif i.endswith('32'):
                    self.ImmediateSize = 4
                else:
                    raise RuntimeError("Invalid Immediate Value")
                break

        for i in displacement:
            if i in self.InstructionString:
                self.HasDisplacement = True
                if i.endswith('8'):
                    self.DisplacementSize = 1
                elif i.endswith('16'):
                    self.DisplacementSize = 2
                elif i.endswith('32'):
                    self.DisplacementSize = 4
                else:
                    raise RuntimeError("Invalid Displacement Value")
                break
        #%TODO: figure out logic for SIB, and prefixes        

    def GetInstance(self):
        return instructionInstance(self)
    
    def __str__(self):
        retVal = ""
        retVal += self.OpcodeString + "\n"
        retVal += self.InstructionString + "\n"
        retVal += self.Description + "\n"
        retVal += "OP: %s, OP flag: %s\n" % (self.Opcode,self.OpcodeFlags)
        return retVal
    
i = instruction

class instructionInstance:
    """
    An instructionInstance is an instruction + the data for an instance's
    prefixes and suffixes
    """
    def __init__(self,inst):
        self.Address = 0x0
        self.Instruction = inst
        self.Prefixes = []
        self.ModRM = None
        self.SIB = None
        self.Displacement = None
        self.Immediate = None

    def GetSuffixSize(self,modrm=None):
        "Size for everything after Opcode"
        size = 0
        if self.Instruction.HasModRM:
            size += 1
            if self.ModRM:
                mrm = self.ModRM
            elif modrm == None:
                raise OpcodeNeedsModRM()
            else:
                mrm = ModRM(modrm)
            if mrm.HasSIB():
                size += 1
            if mrm.GetDisplacementSize():
                size += mrm.GetDisplacementSize()
        if self.Instruction.HasDisplacement:
            size += self.Instruction.DisplacementSize
        if self.Instruction.HasImmediate:
            size += self.Instruction.ImmediateSize
        return size

    def GetInstructionSize(self):
        return len(self.Instruction.Opcode) + self.GetSuffixSize()

    def NextInstructionLoc(self):
            return self.GetInstructionSize() + self.Address
        
    def LoadData(self, data):
        first,rest = '',data
        if self.Instruction.HasModRM:
            first,rest = rest[0],rest[1:]
            self.ModRM = ModRM(struct.unpack("<b",first)[0])
            if self.ModRM.HasSIB():
                first,rest = rest[0],rest[1:]
                self.SIB = struct.unpack("<b",first)[0]
                
        if self.Instruction.HasDisplacement:
            if self.Instruction.DisplacementSize == 1:
                first,rest = rest[0],rest[1:]
                self.Displacement = struct.unpack("<b",first)[0]
            elif self.Instruction.DisplacementSize == 2:
                first,rest = rest[:2],rest[2:]
                self.Displacement = struct.unpack("<s",first)[0]
            elif self.Instruction.DisplacementSize == 4:
                first,rest = rest[:4],rest[4:]
                self.Displacement = struct.unpack('<l',first)[0]
            else:
                raise RuntimeError("Invalid Displacement size")

        if self.Instruction.HasModRM:
            dispSize = self.ModRM.GetDisplacementSize()
            if dispSize == 0:
                pass
            elif dispSize == 1:
                first,rest = rest[0],rest[1:]
                self.Displacement = struct.unpack("<b",first)[0]
            elif dispSize == 4:
                first,rest = rest[:4],rest[4:]
                self.Displacement = struct.unpack('<l',first)[0]
            else:
                raise RuntimeError("Invalid Displacement size")

        if self.Instruction.HasImmediate:
            if self.Instruction.ImmediateSize == 1:
                first,rest = rest[0],rest[1:]
                self.Immediate = struct.unpack("<b",first)[0]
            elif self.Instruction.ImmediateSize == 2:
                first,rest = rest[:2],rest[2:]
                self.Immediate = struct.unpack("<s",first)[0]
            elif self.Instruction.ImmediateSize == 4:
                first,rest = rest[:4],rest[4:]
                self.Immediate = struct.unpack('<l',first)[0]
            else:
                raise RuntimeError("Invalid Immdediate size [%s]" % \
                                   self.InstructionImmediateSize)

        if rest:
            raise RuntimeError("Couldn't unpack all data")

    def DataText(self,data,size,skip=False):
        retVal = ''
        if skip:
            return retVal
        if size >= 1:
            retVal += "%02X " % (data % 0xFF)
        return retVal

    def LoadConcreteValues(self, toks):
        print "%s => %s" % (self.Instruction.InstructionString, toks)
        tmpModRM = ModRM()
        firstDef, restDef = (self.Instruction.InstructionDef[0],self.Instruction.InstructionDef[1:])
        firstTok, restTok = toks[0],toks[1:]
        while 1:
            print "TOK COMPARES: %s => %s" % (firstDef, firstTok)
            if firstDef[0] in (OPCODE, COMMA, REGISTER):
                if firstDef[0] != firstTok[0]:
                    raise x86instError("These should be equal '%s' '%s'" % \
                                       (firstDef, firstTok))
            elif firstDef[0] == OPERAND:
                if firstDef[1] in ('r/m32','r/m16','r/m8'):
                    #figure out r/m val
                    if firstTok[0] == REGISTER:
                        #figure out r val
                        registerName = firstTok[1]
                        registerType = firstDef[1][0] + firstDef[1][3:]
                        registerVal = regOpcode[registerType].index(registerName)
                        if registerVal < 0:
                            raise x86instError("Couldn't resolve register '%s'" % registerName)
                        else:
                            tmpModRM.Mode = 3
                            tmpModRM.RM = registerVal
                    elif firstTok[0] == LBRACKET:
                        while firstTok[0] != RBRACKET:
                            firstTok, restTok = restTok[0],restTok[1:]
                    else:
                        raise x86instError("Invalid r/m token '%s'" % firstTok[0])
                            
                elif firstDef[1] in ('r32','r16','r8'):
                    #figure out r val
                    registerName = firstTok[1]
                    registerVal = regOpcode[firstDef[1]].index(registerName)
                    if registerVal < 0:
                        raise x86instError("Couldn't resolve register '%s'" % registerName)
                    else:
                        tmpModRM.RegOp = registerVal
                elif firstDef[1] in ('imm32','imm16','imm8'):
                    pass
                else:
                    #there will really be more cases here.
                    raise x86instError("Invalid Operand type '%s'" % firstDef[1])
            else:
                raise x86instError("Invalid token" , firstDef)
                                       
            if not restDef:
                break
            firstDef, restDef = restDef[0],restDef[1:]
            firstTok, restTok = restTok[0],restTok[1:]
        self.ModRM = tmpModRM
        
    def OpText(self):
        size = 0
        retVal = ''
        
        retVal += "  %08X: " % self.Address
        for i in self.Instruction.Opcode:
            retVal += "%02X " % i
            size += 1
        if self.ModRM:
            retVal += "%02X " % self.ModRM.SaveToByte()
            size += 1
            if self.ModRM.HasSIB():
                retVal += "%02X " % self.SIB
                size += 1
            disp = self.ModRM.GetDisplacementSize()
            if disp == 1:
                retVal += longToBytesRepr(self.Displacement,1)
                size += 1
            elif disp == 4:
                retVal += longToBytesRepr(self.Displacement,4)
                size += 4
        if self.Instruction.HasDisplacement:
            retVal += longToBytesRepr(self.Displacement,self.Instruction.DisplacementSize)
            size += self.Instruction.DisplacementSize
        if self.Instruction.HasImmediate:
            retVal += longToBytesRepr(self.Immediate,self.Instruction.ImmediateSize)
            size += self.Instruction.ImmediateSize
            
        retVal += "   " * (8-size)

        opcodeStr, operandStr = "",""        
        for typ,val in self.Instruction.InstructionDef:
            if typ == OPCODE:
                opcodeStr += val + " "
            elif typ == COMMA:
                operandStr += val
            elif typ == REGISTER:
                operandStr += val
            elif typ == OPERAND:
                #TODO: Cleanup here, remove strings in if statements
                if val in immediate:
                    operandStr += "%X" % self.Immediate
                elif val in displacement:
                    operandStr += "%X" % (self.Displacement +
                                          self.NextInstructionLoc())
                elif val in ('r8','r16','r32','mm','xmm','/digit','REG'):
                    operandStr += self.ModRM.RegOpString(val)
                elif val in ('r/m8','r/m16','r/m32'):
                    operandStr += self.ModRM.RMString(val)
                elif val in ('m','m8','m16','m32'):
                    tmpVal = self.ModRM.RMString(val)
                    tmpVal = tmpVal.replace("+disp8", "%+X" % self.Displacement)
                    tmpVal = tmpVal.replace("+disp32", "%+X" % self.Displacement)
                    operandStr += tmpVal
                else:
                    # should check for other types
                    operandStr += val
                
            else:
                raise RuntimeError("Invalid op type[%s %s]" % (typ,val))
            
        retVal += "%-10s%-10s" % (opcodeStr, operandStr)
        return retVal
    
i("04 ib", "ADD AL,imm8", "Add imm8 to AL")
i("05 iw", "ADD AX,imm16", "Add imm16 to AX")
i("05 id", "ADD EAX,imm32", "Add imm32 to EAX")
i("80 /0 ib", "ADD r/m8,imm8", "Add imm6 to r/m8")
i("81 /0 iw", "ADD r/m16,imm16", "Add imm16 to r/m16")
i("81 /0 id", "ADD r/m32,imm32", "Add imm32 to r/m32")
i("83 /0 ib", "ADD r/m16, imm8", "Add sign extended imm8 to r/m16")
i("83 /0 iw", "ADD r/m32,imm8", "Add sign extended imm8 to r/m32")
i("00 /r", "ADD r/m8,r8", "Add r8 to r/m8")
i("01 /r", "ADD r/m16,r16", "Add r16 to r/m16")
i("01 /r", "ADD r/m32,r32", "Add r32 to r/m32")
i("02 /r", "ADD r8,r/m8", "Add r/m8 to r/8")
i("03 /r", "ADD r16,r/m16", "Add r/m16 to r16")
i("03 /r", "ADD r32,r/m32", "Add r/m32 to r32")

i("E8 cw", "CALL rel16", "Call near, relative, displacement relative to next instruction")
i("E8 cd", "CALL rel32", "Call near, relative, displacement relative to next instruction")
i("FF /2", "CALL r/m16", "Call near, absolute indirect, address given in r/m16")
i("FF /2", "CALL r/m32", "Call near, absolute indirect, address given in r/m32")
i("9A cd", "CALL ptr16:16", "Call far, absolute, address given in operand")
i("9A cp", "CALL ptr32:32", "Call far, absolute, address given in operand")
i("FF /3", "CALL m16:16", "Call far, absolute indirect, address given in m16:16")
i("FF /3", "CALL m32:32", "Call far, absolute indirect, address given in m32:32")

i("3C ib", "CMP AL,imm8", "Compare imm8 with AL.")
i("3D iw", "CMP AX,imm16", "Compare imm16 with AX.")
i("3D id", "CMP EAX,imm32", "Compare imm32 with EAX.")
i("80 /7 ib", "CMP r/m8,imm8", "Compare imm8 with r/m8.")
i("81 /7 iw", "CMP r/m16,imm16", "Compare imm16 with r/m16.")
i("81 /7 id", "CMP r/m32,imm32", "Compare imm32 with r/m32.")
i("83 /7 ib", "CMP r/m16,imm8", "Compare imm8 with r/m16.")
i("83 /7 ib", "CMP r/m32,imm8", "Compare imm8 with r/m32.")
i("38 /r", "CMP r/m8,r8", "Compare r8 with r/m8.")
i("39 /r", "CMP r/m16,r16", "Compare r16 with r/m16.")
i("39 /r", "CMP r/m32,r32", "Compare r32 with r/m32.")
i("3A /r", "CMP r8,r/m8", "Compare r/m8 with r8.")
i("3B /r", "CMP r16,r/m16", "Compare r/m16 with r16.")
i("3B /r", "CMP r32,r/m32", "Compare r/m32 with r32.")

i("77 cb", "JA rel8", "Jump short if above (CF=0 and ZF=0).")
i("73 cb", "JAE rel8", "Jump short if above or equal (CF=0).")
i("72 cb", "JB rel8", "Jump short if below (CF=1).")
i("76 cb", "JBE rel8", "Jump short if below or equal (CF=1 or ZF=1).")
i("72 cb", "JC rel8", "Jump short if carry (CF=1).")
i("E3 cb", "JCXZ rel8", "Jump short if CX register is 0.")
i("E3 cb", "JECXZ rel8", "Jump short if ECX register is 0.")
i("74 cb", "JE rel8", "Jump short if equal (ZF=1).")
i("7F cb", "JG rel8", "Jump short if greater (ZF=0 and SF=OF).")
i("7D cb", "JGE rel8", "Jump short if greater or equal (SF=OF).")
i("7C cb", "JL rel8", "Jump short if less (SF<>OF).")
i("7E cb", "JLE rel8", "Jump short if less or equal (ZF=1 or SF<>OF).")
i("76 cb", "JNA rel8", "Jump short if not above (CF=1 or ZF=1).")
i("72 cb", "JNAE rel8", "Jump short if not above or equal (CF=1).")
i("73 cb", "JNB rel8", "Jump short if not below (CF=0).")
i("77 cb", "JNBE rel8", "Jump short if not below or equal (CF=0 and ZF=0).")
i("73 cb", "JNC rel8", "Jump short if not carry (CF=0).")
i("75 cb", "JNE rel8", "Jump short if not equal (ZF=0).")
i("7E cb", "JNG rel8", "Jump short if not greater (ZF=1 or SF<>OF).")
i("7C cb", "JNGE rel8", "Jump short if not greater or equal (SF<>OF).")
i("7D cb", "JNL rel8", "Jump short if not less (SF=OF).")
i("7F cb", "JNLE rel8", "Jump short if not less or equal (ZF=0 and SF=OF).")
i("71 cb", "JNO rel8", "Jump short if not overflow (OF=0).")
i("7B cb", "JNP rel8", "Jump short if not parity (PF=0).")
i("79 cb", "JNS rel8", "Jump short if not sign (SF=0).")
i("75 cb", "JNZ rel8", "Jump short if not zero (ZF=0).")
i("70 cb", "JO rel8", "Jump short if overflow (OF=1).")
i("7A cb", "JP rel8", "Jump short if parity (PF=1).")
i("7A cb", "JPE rel8", "Jump short if parity even (PF=1).")
i("7B cb", "JPO rel8", "Jump short if parity odd (PF=0).")
i("78 cb", "JS rel8", "Jump short if sign (SF=1).")
i("74 cb", "JZ rel8", "Jump short if zero (ZF = 1).")

i("0F 87 cw", "JA rel16", "Jump near if above (CF=0 and ZF=0).")
i("0F 87 cd", "JA rel32", "Jump near if above (CF=0 and ZF=0).")
i("0F 83 cw", "JAE rel16", "Jump near if above or equal (CF=0).")
i("0F 83 cd", "JAE rel32", "Jump near if above or equal (CF=0).")
i("0F 82 cw", "JB rel16", "Jump near if below (CF=1).")
i("0F 82 cd", "JB rel32", "Jump near if below (CF=1).")
i("0F 86 cw", "JBE rel16", "Jump near if below or equal (CF=1 or ZF=1).")
i("0F 86 cd", "JBE rel32", "Jump near if below or equal (CF=1 or ZF=1).")
i("0F 82 cw", "JC rel16", "Jump near if carry (CF=1).")
i("0F 82 cd", "JC rel32", "Jump near if carry (CF=1).")
i("0F 84 cw", "JE rel16", "Jump near if equal (ZF=1).")
i("0F 84 cd", "JE rel32", "Jump near if equal (ZF=1).")
i("0F 84 cw", "JZ rel16", "Jump near if 0 (ZF=1).")
i("0F 84 cd", "JZ rel32", "Jump near if 0 (ZF=1).")
i("0F 8F cw", "JG rel16", "Jump near if greater (ZF=0 and SF=OF).")
i("0F 8F cd", "JG rel32", "Jump near if greater (ZF=0 and SF=OF).")
i("0F 8D cw", "JGE rel16", "Jump near if greater or equal (SF=OF).")
i("0F 8D cd", "JGE rel32", "Jump near if greater or equal (SF=OF).")
i("0F 8C cw", "JL rel16", "Jump near if less (SF<>OF).")
i("0F 8C cd", "JL rel32", "Jump near if less (SF<>OF).")
i("0F 8E cw", "JLE rel16", "Jump near if less or equal (ZF=1 or SF<>OF).")
i("0F 8E cd", "JLE rel32", "Jump near if less or equal (ZF=1 or SF<>OF).")
i("0F 86 cw", "JNA rel16", "Jump near if not above (CF=1 or ZF=1).")
i("0F 86 cd", "JNA rel32", "Jump near if not above (CF=1 or ZF=1).")
i("0F 82 cw", "JNAE rel16", "Jump near if not above or equal (CF=1).")
i("0F 82 cd", "JNAE rel32", "Jump near if not above or equal (CF=1).")
i("0F 83 cw", "JNB rel16", "Jump near if not below (CF=0).")
i("0F 83 cd", "JNB rel32", "Jump near if not below (CF=0).")
i("0F 87 cw", "JNBE rel16", "Jump near if not below or equal (CF=0 and ZF=0)")
i("0F 87 cd", "JNBE rel32", "Jump near if not below or equal (CF=0 and ZF=0)")
i("0F 83 cw", "JNC rel16", "Jump near if not carry (CF=0).")
i("0F 83 cd", "JNC rel32", "Jump near if not carry (CF=0).")
i("0F 85 cw", "JNE rel16", "Jump near if not equal (ZF=0).")
i("0F 85 cd", "JNE rel32", "Jump near if not equal (ZF=0).")
i("0F 8E cw", "JNG rel16", "Jump near if not greater (ZF=1 or SF<>OF).")
i("0F 8E cd", "JNG rel32", "Jump near if not greater (ZF=1 or SF<>OF).")
i("0F 8C cw", "JNGE rel16", "Jump near if not greater or equal (SF<>OF).")
i("0F 8C cd", "JNGE rel32", "Jump near if not greater or equal (SF<>OF).")
i("0F 8D cw", "JNL rel16", "Jump near if not less (SF=OF).")
i("0F 8D cd", "JNL rel32", "Jump near if not less (SF=OF).")
i("0F 8F cw", "JNLE rel16", "Jump near if not less or equal (ZF=0 and SF=OF).")
i("0F 8F cd", "JNLE rel32", "Jump near if not less or equal (ZF=0 and SF=OF).")
i("0F 81 cw", "JNO rel16", "Jump near if not overflow (OF=0).")
i("0F 81 cd", "JNO rel32", "Jump near if not overflow (OF=0).")
i("0F 8B cw", "JNP rel16", "Jump near if not parity (PF=0).")
i("0F 8B cd", "JNP rel32", "Jump near if not parity (PF=0).")
i("0F 89 cw", "JNS rel16", "Jump near if not sign (SF=0).")
i("0F 89 cd", "JNS rel32", "Jump near if not sign (SF=0).")
i("0F 85 cw", "JNZ rel16", "Jump near if not zero (ZF=0).")
i("0F 85 cd", "JNZ rel32", "Jump near if not zero (ZF=0).")
i("0F 80 cw", "JO rel16", "Jump near if overflow (OF=1).")
i("0F 80 cd", "JO rel32", "Jump near if overflow (OF=1).")
i("0F 8A cw", "JP rel16", "Jump near if parity (PF=1).")
i("0F 8A cd", "JP rel32", "Jump near if parity (PF=1).")
i("0F 8A cw", "JPE rel16", "Jump near if parity even (PF=1).")
i("0F 8A cd", "JPE rel32", "Jump near if parity even (PF=1).")
i("0F 8B cw", "JPO rel16", "Jump near if parity odd (PF=0).")
i("0F 8B cd", "JPO rel32", "Jump near if parity odd (PF=0).")
i("0F 88 cw", "JS rel16", "Jump near if sign (SF=1).")
i("0F 88 cd", "JS rel32", "Jump near if sign (SF=1).")

i("EB cb", "JMP rel8", "Jump short, relative, displacement relative to next instruction.")
i("E9 cw", "JMP rel16", "Jump near, relative, displacement relative to next instruction.")
i("E9 cd", "JMP rel32", "Jump near, relative, displacement relative to next instruction.")
i("FF /4", "JMP r/m16", "Jump near, absolute indirect, address given in r/m16.")
i("FF /4", "JMP r/m32", "Jump near, absolute indirect, address given in r/m32.")
#i("EA cd", "JMP ptr16:16", "Jump far, absolute, address given in operand.")
#i("EA cp", "JMP ptr16:32", "Jump far, absolute, address given in operand.")
#i("FF /5", "JMP m16:16", "Jump far, absolute indirect, address given in m16:16.")
#i("FF /5", "JMP m16:32", "Jump far, absolute indirect, address given in m16:32.")


i("8D /r", "LEA r16,m", "Store effective address for m in register r16.")
i("8D /r", "LEA r32,m", "Store effective address for m in register r32")

i("88 /r","MOV r/m8,r8","Move r8 to r/m8.")
i("89 /r","MOV r/m16,r16","Move r16 to r/m16.")
i("89 /r", "MOV r/m32,r32", "Move r32 to r/m32")
i("8A /r","MOV r8,r/m8","Move r/m8 to r8")
i("8B /r", "MOV r16,r/m16","Move r/m16 to r16")
i("8B /r","MOV r32,r/m32", "Move r/m32 to r32")
i("8C /r", "MOV r/m16,Sreg", "Move Segment register to r/m16")
i("8E /r", "MOV Sreg,r/m16", "Move r/m16 to Segment Register")
i("A0", "MOV AL,moffs8", "Move byte at (sef:offset) to AL.")
i("A1", "MOV AX,moffs16", "Move word at (seg:offset) to AX.")
i("A1", "MOV EAX,moffs32","Move doubleword at (seg:offset) to EAX.")
i("A2","MOV moffs8,AL","Move AL to (seg:offset)")
i("A3", "MOV moffs16,AX", "Move AX to (seg:offset)")
i("B0 +rb","MOV r8,imm8", "Move imm8 to r8")
i("B8 +rw", "MOV r16,imm16","Move imm16 to r16")
i("B8 +rd", "MOV r32,imm32", "Move imm32 to r32")
i("C6 /0", "MOV r/m8,imm8", "Move imm8 to r/m8")
i("C7 /0", "MOV r/m16,imm16", "Move imm16 to r/m16")
i("C7 /0", "MOV r/m32,imm32", "Move imm32 to r/m32")

i("8F /0", "POP r/m16", "Pop top of stack into m16; increment stack pointer.")
i("8F /0", "POP r/m32", "Pop top of stack into m32; increment stack pointer.")
i("58 +rw", "POP r16", "Pop top of stack into r16; increment stack pointer.")
i("58 +rd", "POP r32", "Pop top of stack into r32; increment stack pointer.")
i("1F", "POP DS", "Pop top of stack into DS; increment stack pointer.")
i("07", "POP ES", "Pop top of stack into ES; increment stack pointer.")
i("17", "POP SS", "Pop top of stack into SS; increment stack pointer.")
i("0F A1", "POP FS", "Pop top of stack into FS; increment stack pointer.")
i("0F A9", "POP GS", "Pop top of stack into GS; increment stack pointer.")

i("FF /6", "PUSH r/m16", "Push r/m16.")
i("FF /6", "PUSH r/m32", "PUSH r/m32.")
i("50 +rw", "PUSH r16", "Push r16.")
i("50 +rd", "PUSH r32", "Push r32.")
i("6A", "PUSH imm8", "Push imm8.")
i("68", "PUSH imm16", "push imm16.")
i("68", "PUSH imm32", "Push imm32.")
i("0E", "PUSH CS", 'Push CS')
i("16", "PUSH SS", "Push SS")
i("1E", "PUSH DS", "Push DS")
i("06", "PUSH ES", "PUsh ES")
i("0F A0", "PUSH FS", "Push FS.")
i("0F A8", "PUSH GS", "Push GS.")

i("F3 6C", "REP INS m8,DX" ,"Input (E)CX bytes from port DX into ES:[(E)DI].")
i("F3 6D", "REP INS m16,DX", "Input (E)CX words from port DX into ES:[(E)DI].")
i("F3 6D", "REP INS m32,DX", "Input (E)CX doublewords from port DX into ES:[(E)DI].")
i("F3 A4", "REP MOVS m8,m8", "Move (E)CX bytes from DS:[(E)SI] to ES:[(E)DI].")
i("F3 A5", "REP MOVS m16,m16","Move (E)CX words from DS:[(E)SI] to ES:[(E)DI].")
i("F3 A5", "REP MOVS m32,m32", "Move (E)CX doublewords from DS:[(E)SI] to ES:[(E)DI].")
i("F3 6E", "REP OUTS DX,r/m8","Output (E)CX bytes from DS:[(E)SI] to port DX.")
i("F3 6F", "REP OUTS DX,r/m16","Output (E)CX words from DS:[(E)SI] to port DX.")
i("F3 6F", "REP OUTS DX,r/m32", "Output (E)CX doublewords from DS:[(E)SI] to port DX.")
i("F3 AC", "REP LODS AL" ,"Load (E)CX bytes from DS:[(E)SI] to AL.")
i("F3 AD",  "REP LODS AX", "Load (E)CX words from DS:[(E)SI] to AX.")
i("F3 AD", "REP LODS EAX", "Load (E)CX doublewords from DS:[(E)SI] to EAX.")
i("F3 AA", "REP STOS m8", "Fill (E)CX bytes at ES:[(E)DI] with AL.")
i("F3 AB", "REP STOS m16", "Fill (E)CX words at ES:[(E)DI] with AX.")
i("F3 AB", "REP STOS [EDI]" ,"Fill (E)CX doublewords at ES:[(E)DI] with EAX.")
i("F3 A6", "REPE CMPS m8,m8", "Find nonmatching bytes in ES:[(E)DI] and DS:[(E)SI].")
i("F3 A7", "REPE CMPS m16,m16", "Find nonmatching words in ES:[(E)DI] and DS:[(E)SI].")
i("F3 A7", "REPE CMPS m32,m32","Find nonmatching doublewords in ES:[(E)DI] and DS:[(E)SI].")
i("F3 AE", "REPE SCAS m8",  "Find non-AL byte starting at ES:[(E)DI].")
i("F3 AF", "REPE SCAS m16", "Find non-AX word starting at ES:[(E)DI].")
i("F3 AF", "REPE SCAS m32", "Find non-EAX doubleword starting at ES:[(E)DI].")
i("F2 A6", "REPNE CMPS m8,m8", "Find matching bytes in ES:[(E)DI] and DS:[(E)SI].")
i("F2 A7", "REPNE CMPS m16,m16", "Find matching words in ES:[(E)DI] and DS:[(E)SI].")
i("F2 A7", "REPNE CMPS m32,m32", "Find matching doublewords in ES:[(E)DI] and DS:[(E)SI].")
i("F2 AE", "REPNE SCAS m8", "Find AL, starting at ES:[(E)DI].")
i("F2 AF", "REPNE SCAS m16", "Find AX, starting at ES:[(E)DI].")
i("F2 AF", "REPNE SCAS m32", "Find EAX, starting at ES:[(E)DI].")

i("C3", "RET", "Near return to calling procedure")
#i("CB", "RET", "Far Return to calling procedure")
i("C2 iw", "RET imm16", "Near return to calling procedure and pop imm16 bytes from stack")
#i("CA iw", "RET imm32", "Far Return to calling procedure and pop imm16 bytes from the stack")

i("2C ib", "SUB AL,imm8", "Subtract imm8 from AL.")
i("2D iw", "SUB AX,imm16", "Subtract imm16 from AX.")
i("2D id", "SUB EAX,imm32", "Subtract imm32 from EAX.")
i("80 /5 ib", "SUB r/m8,imm8", "Subtract imm8 from r/m8")
i("81 /5 iw", "SUB r/m16,imm16", "Subrtact imm16 from r/m16")
i("81 /5 id", "SUB r/m32,imm32", "Subrtract imm32 from r/m32")
i("83 /5 ib", "SUB r/m16,imm8", "Subtract imm8 from r/m16")
i("83 /5 id", "SUB r/m32,imm8", "Subtract imm8 from r/m32")
i("28 /r", "SUB r/m8,r8", "Subtract r8 from r/m8")
i("29 /r", "SUB r/m16,r16", "Subtract r16 from r/m16")
i("29 /r", "SUB r/m32,r32", "Subtract r32 from r/m32")
i("2A /r", "SUB r8,r/m8", "Subtract r/m8 from r8")
i("2B /r", "SUB r16,r/m16","Subtract r/m16 from r16")
i("2B /r", "SUB r32,r/m32", "Subtract r/m32 from r32")

i("34 ib", "XOR AL, imm8", "AL XOR imm8.")
i("35 iw", "XOR AX,imm16", "AX XOR imm16.")
i("35 id", "XOR EAX,imm32", "EAX XOR imm32.")
i("80 /6 ib", "XOR r/m8,imm8", "r/m8 XOR imm8.")
i("81 /6 iw", "XOR r/m16,imm16", "r/m16 xor imm16")
i("81 /6 iw", "XOR r/m32,imm32", "r/m32 xor imm32")
i("83 /6 ib", "XOR r/m16,imm8", "r/m16 XOR imm8 (sign-extended)")
i("83 /6 iw", "XOR r/m32,imm8", "r/m32 XOR imm8 (sign-extended)")
i("30 /r", "XOR r/m8,r8", "r/m8 XOR r8.")
i("31 /r", "XOR r/m16,r16", "r/m16 XOR r16")
i("31 /r", "XOR r/m32,r32", "r/m32 XOR r32")
i("32 /r", "XOR r8,r/m8", "r8 XOR r/m8")
i("33 /r", "XOR r16,r/m16", "r16 XOR r/m16")
i("33 /r", "XOR r32,r/m32", "r32 XOR r/m32")

