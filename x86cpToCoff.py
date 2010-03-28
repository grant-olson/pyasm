# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

from pyasm.coff import (coffError, coffFile, coffSection, coffRelocationEntry,
                        coffSymbolEntry, coffLineNumberEntry)
from pyasm.coffConst import *
from pyasm.coffSymbolEntries import (coffSymbolFile, coffSectionDef, coffFunctionDef,
                                     coffBf, coffLf, coffEf)
import logging, time
from binascii import crc32
from x86inst import RELATIVE, DIRECT

class CpToCoff:
    def __init__(self,cp,directives="-defaultlib:LIBCMT -defaultlib:OLDNAMES "):
        self.cp = cp
        self.directives=directives

        self.lastFunction = None
        self.lastBf = None
        self.lastEf = None
        self.lastEfPos = 0
        
        c = coffFile()
        c.MachineType = coffFile.I386MAGIC

        self.coff = c        
        
    def linkDirectiveSection(self):
        sect = coffSection()
        sect.Name = '.drectve'
        sect.Flags = (SectionFlags.LNK_REMOVE |
                    SectionFlags.LNK_INFO |
                    SectionFlags.ALIGN_1BYTES)
        sect.RawData = self.directives

        sym = self.coff.Symbols.GetSymbol('.drectve')
        sym.RebuildAuxiliaries(len(sect.RawData),0,0,crc32(sect.RawData),0,0)
        
        return sect

    def textSection(self):
        sect = coffSection()
        sect.Name = '.text\x00\x00\x00'
        sect.Flags = (SectionFlags.CNT_CODE |
                    SectionFlags.LNK_COMDAT |
                    SectionFlags.MEM_EXECUTE |
                    SectionFlags.MEM_READ |
                    SectionFlags.ALIGN_16BYTES)
        sect.RawData = self.cp.Code

        for patchin in self.cp.CodePatchins:
            # How do I tell what type it is?
            addr = patchin[1]
            if patchin[2] == DIRECT:
                patchinType = RelocationTypes.I386_DIR32
            elif patchin[2] == RELATIVE:
                patchinType = RelocationTypes.I386_REL32
            else:
                raise RuntimeError("Invalid patchin type")
            
            try:
                loc = self.coff.Symbols.GetLocation(patchin[0])
                r = coffRelocationEntry(addr,loc,typ=patchinType)
            except coffError:
                r = coffRelocationEntry(addr,0x0,typ=patchinType)
            
            sect.RelocationData.append(r)

        sym = self.coff.Symbols.GetSymbol('.text\x00\x00\x00')
        sym.RebuildAuxiliaries(len(sect.RawData),len(self.cp.CodePatchins),0,
                               crc32(sect.RawData),0,0)

        # attempt to add line numbers
        for sym in self.cp.CodeSymbols:
            symLoc = self.coff.Symbols.GetLocation(sym[0])
            sect.LineNumberData.append(coffLineNumberEntry(symLoc,0x0))
            
        return sect        

    def dataSection(self):
        sect = coffSection()
        sect.Name = '.data\x00\x00\x00'
        sect.Flags = (SectionFlags.LNK_COMDAT |
                    SectionFlags.CNT_INITIALIZED_DATA |
                    SectionFlags.MEM_WRITE |
                    SectionFlags.MEM_READ |
                    SectionFlags.ALIGN_4BYTES)
        sect.RawData = self.cp.Data

        sym = self.coff.Symbols.GetSymbol('.data\x00\x00\x00')
        sym.RebuildAuxiliaries(len(sect.RawData),0,0,crc32(sect.RawData),0,0)
        
        return sect

    def rdataSection(self):
        sect = coffSection()
        sect.Name = '.rdata\x00\x00'
        sect.Flags = (SectionFlags.LNK_COMDAT |
                    SectionFlags.CNT_INITIALIZED_DATA |
                    SectionFlags.MEM_READ |
                    SectionFlags.ALIGN_4BYTES)
        sect.RawData = self.cp.Data

        sym = self.coff.Symbols.GetSymbol('.rdata\x00\x00')
        sym.RebuildAuxiliaries(len(sect.RawData),0,0,crc32(sect.RawData),0,0)
        
        return sect
        
    def debugF_Section(self):
        "What the hell is this?"
        pass
##        s4=coffSection()
##        s4.Name = '.debug$F'
##        s4.Flags = (SectionFlags.LNK_COMDAT |
##                    SectionFlags.TYPE_NO_PAD |
##                    SectionFlags.CNT_INITIALIZED_DATA |
##                    SectionFlags.MEM_DISCARDABLE |
##                    SectionFlags.MEM_READ |
##                    SectionFlags.ALIGN_1BYTES)
##        s4.RawData = '\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00'
##
##        r = coffRelocationEntry(addr=0x0,sym=0x8,typ=RelocationTypes.I386_DIR32NB)
##        s4.RelocationData.append(r)
##
##        c.Sections.append(s4)

    def addSymbol(self,name,val,sec,typ,cls,aux=''):
        self.coff.AddSymbol(name,val,sec,typ,cls,aux)

    def addFunctionSymbols(self,sym,section):
        """
        A function actually has 4 symbol entries:
            + the function entry
            + the BeginFunction(.bf) entry
            + the LinesInFunction(.lf) entry
            + the EndFunction(.ef) entry
        """
        
        fun = coffFunctionDef(sym[0],sym[1],2)
        self.coff.AddExistingSymbol(fun)
        if self.lastFunction:
            self.lastFunction.PointerToNextFunction = fun.Location
            self.lastFunction.TotalSize = fun.Value - self.lastFunction.Value
            self.lastFunction.BuildAuxiliaries()
        self.lastFunction = fun
        
        bf = coffBf(2)
        self.coff.AddExistingSymbol(bf)
        if self.lastBf:
            self.lastBf.PointerToNextFunction = bf
            self.lastBf.BuildAuxiliaries()
        self.lastBf = bf

        fun.TagIndex = bf.Location
        fun.BuildAuxiliaries()
        
        lf = coffLf(2)
        self.coff.AddExistingSymbol(lf)

        ef = coffEf(2)
        self.coff.AddExistingSymbol(ef)
        if self.lastEf:
            self.lastEf.Value = sym[1] - self.lastEfPos
        self.lastEf = ef
        self.lastEfPos = sym[1]
        
    def addSymbols(self):
        self.coff.AddExistingSymbol(coffSymbolFile('C:\\objtest\\objtest\\objtest.cpp'))
        
        self.addSymbol('@comp.id',0xB2306, -1, SymbolTypes.NULL, SymbolClass.STATIC)

        self.coff.AddExistingSymbol(coffSectionDef('.drectve',1))
        self.coff.AddExistingSymbol(coffSectionDef('.text\x00\x00\x00',2))
        self.coff.AddExistingSymbol(coffSectionDef('.data\x00\x00\x00',3))

        for sym in self.cp.CodeSymbols:
            self.addFunctionSymbols(sym,2)

        #sizes for last function
        totalSize = len(self.cp.Code)
        self.lastFunction.TotalSize = totalSize - self.lastFunction.Value
        self.lastFunction.BuildAuxiliaries()
        self.lastEf.Value = totalSize - self.lastEfPos

        for sym in self.cp.DataSymbols:
            self.addSymbol(sym[0], sym[1],3,0x20,SymbolClass.EXTERNAL)

        #resolve external label references here
        for patchin in self.cp.CodePatchins:
            try:
                self.coff.Symbols.GetLocation(patchin[0])
            except coffError:
                # no symble entry, add ref
                self.addSymbol(patchin[0], SymbolValues.SYM_UNDEFINED, 0, 0x20,
                               SymbolClass.EXTERNAL)

        self.coff.Symbols.SetLocations()

        
    def makeReleaseCoff(self):
        """
        converts a generic codePackage to a coff object
        """
        self.addSymbols()
        
        self.coff.Sections.append(self.linkDirectiveSection())
        self.coff.Sections.append(self.textSection())
        self.coff.Sections.append(self.dataSection())
        #c.Sections.append(self.DebugF_Section())

        self.coff.SetSizes()
        self.coff.SetOffsets()

        return self.coff

