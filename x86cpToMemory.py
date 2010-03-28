# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

from x86inst import RELATIVE,DIRECT
from x86PackUnpack import ulongToString
from x86asm import PYTHON
import pyasm.excmem as excmem

import logging, sys

if sys.platform == 'win32':
    import win32api, pywintypes
    from sys import dllhandle

    def runtimeResolve(funcName):
        try:
            addr = win32api.GetProcAddress(dllhandle,funcName)
        except pywintypes.error:
            raise RuntimeError("Unable to resolve external symbol '%s'" % funcName)
        return addr
elif sys.platform in ('linux2'):
    def runtimeResolve(funcName):
        return excmem.GetSymbolAddress(funcName)
else:
    raise RuntimeError("Don't know how to resolve external symbols for platform '%s'" % sys.platform)


class CpToMemory:
    def __init__(self,cp):
        self.cp = cp
        self.symbols = {}
        self.resolvedCode = ''
        
    def LookupAddress(self,sym):
        if self.symbols.has_key(sym):
            return self.symbols[sym]
        else: #try runtime resolution, currently windows specific
            funcaddress = runtimeResolve(sym)
            self.symbols[sym] = funcaddress
            return funcaddress

    def BindPythonFunctions(self,glb=None,bindFunction=excmem.BindFunctionAddress):
        if glb is None:
            glb = globals()
        for proc in self.cp.CodeSymbols:
            if proc[2] == PYTHON:
                glb[proc[0]] = bindFunction(proc[1] + self.codeAddr)
            
    def MakeMemory(self,glb=None):
        if not glb:
            glb = globals()
            
        self.codeAddr = excmem.AllocateExecutableMemory(len(self.cp.Code))
        self.dataAddr = excmem.AllocateExecutableMemory(len(self.cp.Data))

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
        
        excmem.LoadExecutableMemoryString(self.codeAddr,self.resolvedCode)
        excmem.LoadExecutableMemoryString(self.dataAddr,self.cp.Data)

        
            
