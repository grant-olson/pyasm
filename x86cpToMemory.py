# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

from x86inst import RELATIVE,DIRECT
from x86PackUnpack import ulongToString

import logging

import win32api
python24Handle = win32api.GetModuleHandle("python24")

def WindowsRuntimeResolve(funcName):
    return win32api.GetProcAddress(python24Handle,funcName)

#we'll eventually have linux logic here as well
runtimeResolve = WindowsRuntimeResolve

class CpToMemory:
    def __init__(self,cp,memAccess):
        self.cp = cp
        self.memAccess = memAccess
        self.symbols = {}
        self.resolvedCode = ''
        
    def LookupAddress(self,sym):
        if self.symbols.has_key(sym):
            return self.symbols[sym]
        else: #try runtime resolution, currently windows specific
            funcaddress = runtimeResolve(sym)
            self.symbols[sym] = funcaddress
            return funcaddress

    def BindPythonFunctions(self,glb=None):
        if glb is None:
            glb = globals()
        for proc in self.cp.CodeSymbols:
            glb[proc[0]] = self.memAccess.BindFunctionAddress(proc[1] + self.codeAddr)
            
    def MakeMemory(self,glb=None):
        if not glb:
            glb = globals()
            
        self.codeAddr = self.memAccess.AllocateExecutableMemory(len(self.cp.Code))
        self.dataAddr = self.memAccess.AllocateExecutableMemory(len(self.cp.Data))

        self.symbols = {}        
        for sym in self.cp.CodeSymbols:
            self.symbols[sym[0]] = sym[1] + self.codeAddr
        for sym in self.cp.DataSymbols:
            self.symbols[sym[0]] = sym[1] + self.dataAddr

        self.resolvedCode = self.cp.Code # nondestructive on cp

        for patch in self.cp.CodePatchins:
            if patch[2] == DIRECT:
                resolvedAddr = self.LookupAddress(patch[0])
            elif patch[2] == RELATIVE:
                #XXX
                # I'm just assuming that the pathin is at the end of a function
                # and the next instrution address is that +4
                # Is this valid or do I need to calculate?
                resolvedAddr = self.LookupAddress(patch[0]) - (self.codeAddr + patch[1] + 4)
            else:
                raise RuntimeError("Invalid patchin information")
            self.resolvedCode = self.resolvedCode[:patch[1]] + ulongToString(resolvedAddr) \
                           + self.resolvedCode[patch[1]+4:]
            
        assert len(self.resolvedCode) == len(self.cp.Code)
        
        self.memAccess.LoadExecutableMemoryString(self.codeAddr,self.resolvedCode)
        self.memAccess.LoadExecutableMemoryString(self.dataAddr,self.cp.Data)

        
            