from x86inst import RELATIVE,DIRECT
from x86PackUnpack import ulongToString

import win32api

class CpToMemory:
    def __init__(self,cp,memAccess):
        self.cp = cp
        self.memAccess = memAccess
        self.symbols = {}
        self.resolvedCode = ''
        
    def LookupAddress(self,sym):
        if self.symbols.has_key(sym):
            return self.symbols[sym]
        else: #try runtime resolution, windows specific
            python24 = win32api.GetModuleHandle("python24")
            funcaddress = win32api.GetProcAddress(python24, sym)
            self.symbols[sym] = funcaddress
            return funcaddress
            
    def MakeMemory(self,glb=None):
        if not glb:
            glb = globals()
            
        codeAddr = self.memAccess.AllocateExecutableMemory(len(self.cp.Code))
        dataAddr = self.memAccess.AllocateExecutableMemory(len(self.cp.Data))

        self.symbols = {}        
        for sym in self.cp.CodeSymbols:
            self.symbols[sym[0]] = sym[1] + codeAddr
        for sym in self.cp.DataSymbols:
            self.symbols[sym[0]] = sym[1] + dataAddr

        self.resolvedCode = self.cp.Code # nondestructive on cp

        for patch in self.cp.CodePatchins:
            if patch[2] == DIRECT:
                resolvedAddr = self.LookupAddress(patch[0])
            elif patch[2] == RELATIVE:
                resolvedAddr = self.LookupAddress(patch[0]) + 4 - (codeAddr + patch[1])
            else:
                raise RuntimeError("Invalid patchin information")
            self.cp.Code = self.resolvedCode[:patch[1]] + ulongToString(resolvedAddr) \
                           + self.resolvedCode[patch[1]+4:]
        
        self.memAccess.LoadExecutableMemoryString(codeAddr,self.resolvedCode)
        self.memAccess.LoadExecutableMemoryString(dataAddr,self.cp.Data)

        print glb

        for proc in self.cp.CodeSymbols:
            glb[proc[0]] = self.memAccess.BindFunctionAddress(proc[1] + codeAddr)
            