from x86tokens import *# how to add /0?

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

i = instruction #shorthand


MOV = token()
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
