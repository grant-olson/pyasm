import re

class OpcodeTooShort(Exception):pass
class OpcodeNeedsModRM(Exception):pass # for /d info
class OpcodeNeedsPreferredSize(Exception):pass # for 16/32 byte dupes

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
            for i in range(len(key)-1):
                tmpKey = key[:i]
                dict.__setitem__(self,tmpKey,None)
                
    def GetOp(self,opcode,modRM=None,preferredSize=None):
        lst = self.__getitem__(opcode)
        
        if modRM is not None:
            digit = modRM & 0x38
            digit = digit >> 3
            digit = "/%s" % digit
            lst = [item for item in lst if digit in item.OpcodeFlags]
        if preferredSize is not None:
            if preferredSize == 16:
                lst = [item for item in lst if item.InstructionString.find('r32') == -1]
                lst = [item for item in lst if item.InstructionString.find('r/m32') == -1]
                lst = [item for item in lst if item.InstructionString.find('imm32') == -1]
                lst = [item for item in lst if item.InstructionString.find('rel32') == -1]
            elif preferredSize == 32:
                lst = [item for item in lst if item.InstructionString.find('r16') == -1]
                lst = [item for item in lst if item.InstructionString.find('r/m16') == -1]
                lst = [item for item in lst if item.InstructionString.find('imm16') == -1]
                lst = [item for item in lst if item.InstructionString.find('rel16') == -1]
            else:
                raise RuntimeError("Invalid Preferred size")
                
        if len(lst) == 0:
            raise RuntimeError("Invalid/Unimplemented Opcode [%s]" % opcode)
        elif len(lst) > 1:
            # try to figure out what we need
            op = lst[0]
            for flag in op.OpcodeFlags:
                if flag in ('/0','/1','/2','/3','/4','/5','/6','/7'):
                    raise OpcodeNeedsModRM("Opcode %s" % op.Opcode)
            raise OpcodeNeedsPreferredSize()
        else:
            return lst[0]
        

opcodeDict = OpcodeDict()
                
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

class instruction:
    def __init__(self,opstr,inststr,desc):
        self.OpcodeString = opstr
        self.InstructionString = inststr
        self.Description = desc

        self.Opcode = []
        self.OpcodeSize = 0
        self.OpcodeFlags = []
        
        self.HasImmediate = False
        self.ImmediateSize = 0 # no of bytes
        self.Immediate = None

        self.HasModRM = False        
        self.ModRM = None

        self.HasSIB = False
        self.SIB = None

        self.HasPrefixes = False        
        self.Prefixes = None

        self.HasDisplacement = False
        self.DisplacementSize = 0
        self.Displacement = None

        self.setOpcodeAndFlags()
        self.setHasFlags()

        if '+rb' in self.OpcodeFlags:
            for i in range(8):
                oplist = list(self.Opcode)
                oplist[0] += i
                opcodeDict[tuple(oplist)] = self
        elif '+rw' in self.OpcodeFlags:
            for i in range(8):
                oplist = list(self.Opcode)
                oplist[0] += i
                opcodeDict[tuple(oplist)] = self
        elif '+rd' in self.OpcodeFlags:
            for i in range(8):
                oplist = list(self.Opcode)
                oplist[0] += i
                opcodeDict[tuple(oplist)] = self
        else:
            opcodeDict[self.Opcode] = self        

    def setOpcodeAndFlags(self):
        parts = self.OpcodeString.split()
        for part in parts:
            if len(part) == 2 and part[0] in "ABCDEF0123456789" and part[1] in "ABCDEF0123456789":
                # suppose I could use a regex above
                self.Opcode.append(eval("0x%s" % part))
            else:
                self.OpcodeFlags.append(part)

        self.Opcode = tuple(self.Opcode)
        self.OpcodeSize = len(self.Opcode)
                
    def setHasFlags(self):
        for i in instModRM:
            if i in self.InstructionString:
                self.HasModRM = True
                break
        for i in immediate:
            if i in self.InstructionString:
                self.HasImmediate = True
                if i.endswith('8'):
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
        
    def GetSuffixSize(self):
        "Size for everything after Opcode"
        if '+rb' in self.OpcodeFlags or '+rw' in self.OpcodeFlags or '+rd' in self.OpcodeFlags:
            return 0
        size = 0
        if self.HasModRM: size += 1
        if self.HasSIB: size += 1
        if self.HasDisplacement: size += self.DisplacementSize
        if self.HasImmediate: size += self.ImmediateSize
        return size

    def __str__(self):
        retVal = ""
        retVal += self.OpcodeString + "\n"
        retVal += self.InstructionString + "\n"
        retVal += self.Description + "\n"
        retVal += "OP: %s, OP flag: %s\n" % (self.Opcode,self.OpcodeFlags)
        return retVal
    
i = instruction

i("04 ib", "ADD AL,imm8", "Add imm8 to AL")
i("05 iw", "ADD AX,imm16", "Add imm16 to AX")
i("05 id", "ADD EAX,imm32", "Add imm32 to EAX")
i("80 /0 ib", "ADD r/m8,imm8", "Add imm6 to r/m8")
i("81 /0 iw", "ADD r/m16,imm16", "Add imm16 to r/m16")
i("81 /0 id", "ADD r/m32,imm32", "Add imm32 to r/m32")
i("83 /0 ib", "ADD r/m16, imm8", "Add sign extended imm8 to r/m16")
i("83 /0 iw", "Add r/m32,imm8", "Add sign extended imm8 to r/m32")
i("00 /r", "Add r/m8,r8", "Add r8 to r/m8")
i("01 /r", "Add r/m16,r16", "Add r16 to r/m16")
i("01 /r", "Add r/m32,r32", "Add r32 to r/m32")
i("02 /r", "Add r8,r/m8", "Add r/m8 to r/8")
i("03 /r", "Add r16,r/m16", "Add r/m16 to r16")
i("03 /r", "Add r32,r/m32", "Add r/m32 to r32")

i("E8 cw", "CALL rel16", "Call near, relative, displacement relative to next instruction")
i("E8 cd", "CALL rel32", "Call near, relative, displacement relative to next instruction")
i("FF /2", "CALL r/m16", "Call near, absolute indirect, address given in r/m16")
i("FF /2", "CALL r/m32", "Call near, absolute indirect, address given in r/m32")
i("9A cd", "CALL ptr16:16", "Call far, absolute, address given in operand")
i("9A cp", "CALL ptr32:32", "Call far, absolute, address given in operand")
i("FF /3", "CALL m16:16", "Call far, absolute indirect, address given in m16:16")
i("FF /3", "CALL m32:32", "Call far, absolute indirect, address given in m32:32")

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

i("C3", "RET", "Near return to calling procedure")
i("CB", "RET", "Far Return to calling procedure")
i("C2 iw", "RET imm16", "Near return to calling procedure and pop imm16 bytes from stack")
i("CA iw", "RET imm16", "Far Return to calling procedure and pop imm16 bytes from the stack")

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
i("31 /r", "XOR r/m16,r16", "r/m16 XOR r16")
i("32 /r", "XOR r8,r/m8", "r8 XOR r/m8")
i("33 /r", "XOR r16,r/m16", "r16 XOR r/m16")
i("33 /r", "XOR r32,r/m32", "r32 XOR r/m32")