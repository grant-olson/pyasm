from x86tokens import *# how to add /0?

rDefs = {
    r8:{0:'AL',1:'CL',2:'DL',3:'BL',4:'AH',5:'CH',6:'DH',7:'BH'},
    r16:{0:'AX',1:'CX',2:'DX',3:'BX',4:'SP',5:'BP',6:'SI',7:'DI'},
    r32:{0:'EAX',1:'ECX',2:'EDX',3:'EBX',4:'ESP',5:'EBP',6:'ESI',7:'EDI'},
    mm:{0:'MM0',1:'MM1',2:'MM2',3:'MM3',4:'MM4',5:'MM5',6:'MM6',7:'MM7'},
    xmm:{0:'XMM0',1:'XMM1',2:'XMM2',3:'XMM3',4:'XMM4',5:'XMM5',6:'XMM6',7:'XMM7'},
    dx:{0:'/d0',1:'/d1',2:'/d2',3:'/d3',4:'/d4',5:'/d5',6:'/d6',7:'/d7'},
}

rmDefs = {
    0x0:{0:'[BX+SI]',1:'[BX+DI]',2:'[BP+SI]',3:'[BP+DI]',4:'[SI]',5:'[DI]',6:'disp16',7:'[BX]'},
    0x1:{0:'[BX+SI]+disp8',1:'[BX+DI]+disp8',2:'[BP+SI]+disp8',3:'[BP+DI]+disp8',4:'[SI]+disp8',
         5:'[DI]+disp8',6:'[BP]+disp8',7:'[BX]+disp8'},
    0x2:{0:'[BX+SI]+disp16',1:'[BX+DI]+disp16',2:'[BP+SI]+disp16',3:'[BP+DI]+disp16',4:'[SI]+disp16',
         5:'[DI]+disp16',6:'[BP]+disp16',7:'[BX]+disp16'},
    0x3:{}#TODO: Deal with special case
    }

class modRM:
    def __init__(self, mod=0x0,regOp=0x0,rm=0x0):
        self.Mod = mod
        self.RegOp= regOp
        self.RM = rm

#
# OKAY THE ACTUAL INSTRUCITONS HERE
#

instBySig = {}
instByOpcode = {}

class instruction:
    def __init__(self, sig, op, flags=None):
        self.Signature = sig
        self.Opcode = op
        self.Flags = flags
        if not self.Flags: self.Flags = []
        instBySig[self.Signature] = self
        instByOpcode[self.Opcode] = self
    def HasModRM(self):
        return False

i = instruction #shorthand

i(('CALL','cd'),0xE8)

MOV = 'MOV'
i((MOV,rm8,r8),0x88)
i((MOV,rm16,r16),0x89)
i((MOV,rm32,r32),0x89)
i((MOV,r8,rm8),0x8A)
i((MOV,r16,rm16),0x8B)
i((MOV,r32,rm32),0x8B)

            # don't care about segmends and moffs yet

#how to add rb,rw,rd?
i((MOV,r8,imm8),0xB0) 
i((MOV,r16,imm16),0xB8)
i((MOV,r32,imm32),0xB8)

# how to add /0?  
i((MOV,rm8,imm8),0xC6)
i((MOV,rm16,imm16),0xC7)
i((MOV,rm32,imm32),0xC7)

# TODO: HANDLE AUTOMATIC OPCODES
PUSH = 'PUSH'
i((PUSH,d6,rm16),0xFF)
i((PUSH,d6,rm32),0xFF)
i((PUSH,rw,r16),0x50)
i((PUSH,rd,r32),0x50)
i((PUSH,imm8),0x6A)
i((PUSH,imm16),0x68)
i((PUSH,'imm32'),0x68)
i((PUSH,),0x0E)


