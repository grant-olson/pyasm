"""
coff.py
-------

Provides the framework to convert raw machine code to/from coff file formats.

So far I can build a standard coff file but still need an external linker to
make an exe.
"""

import logging, sys
from coffConst import *
from x86PackUnpack import *

class coffError(Exception):pass

def attemptNameLookup(const,id): return const.get(id, "UNDEF??[%0X]" % id)

def charsAsBinDump(chars, address = 0):
    head,tail = chars[:16], chars[16:]
    while head:
        print "%08X:  " % address ,
        address += 0x10
        for char in head:
            print "%02X" % ord(char) ,
        if len(head) < 16:
            for i in range(16-len(head)):
                print "  " ,
        print "   ",
        for char in head:
            if ord(char)<=32:
                sys.stdout.write(".")
            else:
                sys.stdout.write(char)
        print
        head,tail = tail[:16], tail[16:]

class coffSymbolEntry:
    def __init__(self,name="",value=0x0,sec=0x0,typ=0x0,cls=0x0,aux='',fullname=None):
        self.Name = name
        self.Value = value
        self.SectionNumber = sec
        self.Type = typ
        self.StorageClass = cls
        self.NumberAuxiliary = 0x0
        self.Auxiliaries = aux
        self.Location = 0
        if fullname:
            self.Fullname = fullname
        else:
            self.Fullname = name

    def InitFromFile(self,f):
        self.Name = stringFromFile(8,f)
        self.Value = ulongFromFile(f)
        self.SectionNumber = shortFromFile(f)
        self.Type = ushortFromFile(f)
        self.StorageClass = ucharFromFile(f)
        self.NumberAuxiliary = ucharFromFile(f)
        self.Auxiliaries = ''

        for i in range(self.NumberAuxiliary):
            aux = stringFromFile(18,f)
            self.Auxiliaries += aux


    def WriteToFile(self,f):
        stringToFile(f, 8, self.Name)
        ulongToFile(f, self.Value)
        shortToFile(f, self.SectionNumber)
        ushortToFile(f, self.Type)
        ucharToFile(f, self.StorageClass)
        ucharToFile(f, self.NumberAuxiliaries)
        stringToFile(f, len(self.Auxiliaries), self.Auxiliaries)

    def SetSizes(self):
        assert not len(self.Auxiliaries) % 18, "Invalid Aux length"
        self.NumberAuxiliaries =  (len(self.Auxiliaries) // 18)
        
    def Rows(self):
        self.SetSizes()
        return self.NumberAuxiliaries + 1

    def DumpInfo(self):
        print "%20s\t%10s\t%10s\t%10s\t%10s\t" % (repr(self.Name),
                    attemptNameLookup(SymbolValues.NAME,self.Value),
                    repr(self.SectionNumber),
                    attemptNameLookup(SymbolTypes.NAME,self.Type),
                    attemptNameLookup(SymbolClass.NAME,self.StorageClass))
        tail = repr(self.Auxiliaries)
        head,tail = tail[:70],tail[70:]
        while head:
            print "\t%s" % head
            head,tail = tail[:70],tail[70:]
        
class coffSymbolList(list):
    def DumpInfo(self):
        if self:
            print "Symbol Entry Table"
            print "=================="
            print "%20s\t%10s\t%10s\t%10s\t%10s\t" % ("Name",
                        'Value','SectionNumber','Type','StorageClass')
        for x in self:
            x.DumpInfo()
            
    def InitFromFile(self, f, count):
        x = 0
        while x < count:
            symbol = coffSymbolEntry()
            symbol.InitFromFile(f)
            x += 1 + symbol.NumberAuxiliary #account for aux stubs
            self.append(symbol)          

    def WriteToFile(self, f):
        for sym in self:
            sym.WriteToFile(f)

    def SetLocations(self):
        start = 0
        for sym in self:
            sym.Location = start
            start += sym.Rows()

    def GetLocation(self,symbolName):
        for sym in self:
            if sym.Fullname == symbolName:
                return sym.Location
        raise coffError("Couldn't find symbol '%s'" % symbolName)
            
            
class coffLineNumberEntry:
    def __init__(self,sym=0x0,num=0x0):
        self.Symbol = sym
        self.Number = num

    def InitFromFile(self,f):
        self.Symbol = ulongFromFile(f)
        self.Number = ushortFromFile(f)

    def WriteToFile(self,f):
        ulongToFile(f, self.Symbol)
        ushortToFile(f,self.Number)
        
    def DumpInfo(self):
        print "%s\t%s" % (self.Symbol, self.Number)

    def Sizeof(self):
        return 6
    
class coffLineNumberList(list):
    def DumpInfo(self):
        if self:
            print "LINE NUMBERS"
            print "============"
            print "Symbol\tLine Number"
        for x in self:
            x.DumpInfo()
            
class coffRelocationEntry:
    def __init__(self,addr=0x0,sym=0x0,typ=0x0):
        self.Address = addr
        self.Symbol = sym
        self.Type = typ

    def InitFromFile(self,f):
        self.Address = ulongFromFile(f)
        self.Symbol = ulongFromFile(f)
        self.Type = ushortFromFile(f)

    def WriteToFile(self,f):
        ulongToFile(f,self.Address)
        ulongToFile(f, self.Symbol)
        ushortToFile(f, self.Type)
        
    def Sizeof(self):
        return 10
    
    def DumpInfo(self):
        print "%02X\t%02X\t%10s" % (self.Address, self.Symbol,
                              attemptNameLookup(RelocationTypes.NAME, self.Type))

class coffRelocationList(list):
    def DumpInfo(self):
        if self:
            print "Relocation Data"
            print "==============="
            print "%08s\t%04s\t%10s" % ("Address","Symbol","Type")
        for x in self:
            x.DumpInfo()
            
class coffSection:
    def __init__(self):
        self.Name = ""
        self.PhysicalAddress = 0x0
        self.VirtualAddress = 0x0
        self.RawDataSize = 0x0
        self.RawDataLoc = 0x0
        self.RelocationLoc = 0x0
        self.LineNumberLoc = 0x0
        self.RelocationCount = 0x0
        self.LineNumberCount = 0x0
        self.Flags = 0x0
        self.RawData = ""
        self.LineNumberData = coffLineNumberList()
        self.RelocationData = coffRelocationList()

    def InitFromFilePass1(self, f):
        self.Name = stringFromFile(8,f)
        self.PhysicalAddress = ulongFromFile(f)
        self.VirtualAddress = ulongFromFile(f)
        self.RawDataSize = ulongFromFile(f)
        self.RawDataLoc = ulongFromFile(f)
        self.RelocationLoc = ulongFromFile(f)
        self.LineNumberLoc = ulongFromFile(f)
        self.RelocationCount = ushortFromFile(f)
        self.LineNumberCount = ushortFromFile(f)
        self.Flags = longFromFile(f)

    def WriteToFilePass1(self, f):
        stringToFile(f,8,self.Name)
        ulongToFile(f,self.PhysicalAddress)
        ulongToFile(f,self.VirtualAddress)
        ulongToFile(f,self.RawDataSize)
        ulongToFile(f,self.RawDataLoc)
        ulongToFile(f,self.RelocationLoc)
        ulongToFile(f,self.LineNumberLoc)
        ushortToFile(f,self.RelocationCount)
        ushortToFile(f,self.LineNumberCount)
        longToFile(f,self.Flags)
        
    def InitFromFilePass2(self, f):      
        if self.RawDataSize:
            assert self.RawDataLoc == f.tell(), "Out of Sync"
            self.RawData = stringFromFile(self.RawDataSize, f)
        if self.RelocationCount:
            assert self.RelocationLoc == f.tell(), "Out of Sync"
            for i in range(self.RelocationCount):
                relEnt = coffRelocationEntry()
                relEnt.InitFromFile(f)
                self.RelocationData.append(relEnt)
        if self.LineNumberCount:
            assert self.LineNumberLoc == f.tell(), "Out of Sync"
            for i in range(self.LineNumberCount):
                ln = coffLineNumberEntry()
                ln.InitFromFile(f)
                self.LineNumberData.append(ln)
                
    def WriteToFilePass2(self,f):
        if self.RawDataSize:
            stringToFile(f, self.RawDataSize,self.RawData)
        if self.RelocationCount:
            for rec in self.RelocationData:
                rec.WriteToFile(f)
        if self.LineNumberCount:
            for ln in self.LineNumberData:
                ln.WriteToFile(f)
    
    def Sizeof(self):
        "excluding data"
        return 40

    def SetSizes(self):
        self.RawDataSize = len(self.RawData)
        self.RelocationCount = len(self.RelocationData)
        self.LineNumberCount = len(self.LineNumberData)

    def SetOffsets(self, currentOffset):
        self.RawDataLoc = currentOffset
        currentOffset += self.RawDataSize
        if self.RelocationCount:
            self.RelocationLoc = currentOffset
            currentOffset += self.RelocationCount * 10
        else:
            self.RelocationLoc = 0x0
            
        if self.LineNumberCount:
            self.LineNumberLoc = currentOffset
            currentOffset += self.LineNumberCount * 6
        else:
            self.LineNumberLoc = 0x0
        return currentOffset
        
    def DumpInfo(self, showData=True):
        print
        print "SECTION"
        print "======="
        print
        print "Name %s\n" % self.Name
        print "PhysicalAddress %s" % self.PhysicalAddress
        print "VirtualAddress %s" % self.VirtualAddress
        print "RawDataSize %s" % self.RawDataSize
        print "RawDataLoc %s" % self.RawDataLoc
        print "RelocationTable %s" % self.RelocationLoc
        print "LineNumberTable %s" % self.LineNumberLoc
        print "RelocationCount %s" % self.RelocationCount
        print "LineNumberCount %s" % self.LineNumberCount
        print "Flags %s" % self.Flags
        for key in SectionFlags.NAME.keys():
            if self.Flags & key:
                print "\t%s" % SectionFlags.NAME[key]
        align = self.Flags & SectionFlags.ALIGN_MASK
        print "\t%s" % SectionFlags.ALIGN_NAME[align]
        print

        if showData:
            charsAsBinDump(self.RawData)
            self.RelocationData.DumpInfo()
            self.LineNumberData.DumpInfo()
            print
        
class coffFile:
    I386MAGIC = 0x14c

    NO_RELOC = 0x1
    EXECUTABLE = 0x2
    NO_LINENO = 0x4
    NO_SYMBOLS = 0x8
    LITTLEENDIAN = 0x100
    NO_DEBUG = 0x200
    SYSTEM = 0x1000
    DLL = 0x2000

    FLAG_NAMES = {NO_RELOC: 'NO_RELOC' ,
                  EXECUTABLE: 'EXECUTABLE',
                  NO_LINENO: 'NO_LINENO',
                  NO_SYMBOLS: 'NO_SYMBOLS',
                  LITTLEENDIAN: 'LITTLENDIAN',
                  NO_DEBUG: 'NO DEBUG',
                  SYSTEM: 'SYSTEM',
                  DLL: 'DLL'}
    
    def __init__(self):
        self.MachineType = 0x0
        self.NumberOfSections = 0x0
        self.Timestamp = 0x0
        self.SymbolTableLoc = 0x0
        self.SymbolCount = 0x0
        self.Symbols = coffSymbolList()
        self.OptionalHeaderSize = 0x0
        self.Characteristics = 0x0
        self.Sections = []
        self.StringTableSize = 0
        self.StringTable = ""

    def InitFromFile(self, f):
        self.MachineType = ushortFromFile(f)
        self.NumberOfSections = ushortFromFile(f)
        self.Timestamp = ulongFromFile(f)
        self.SymbolTableLoc = ulongFromFile(f)
        self.SymbolCount = ulongFromFile(f)
        self.OptionalHeaderSize = ushortFromFile(f)
        self.Characteristics = ushortFromFile(f)
        for i in range(self.NumberOfSections):
            sec = coffSection()
            sec.InitFromFilePass1(f)
            self.Sections.append(sec)
        for sec in self.Sections:
            sec.InitFromFilePass2(f)
        assert self.SymbolTableLoc == f.tell(), "Out of sync"
        self.Symbols.InitFromFile(f,self.SymbolCount)
        self.StringTableSize = ulongFromFile(f) - 4 #includes itself in the count
        self.StringTable = f.read(self.StringTableSize)

        if f.read():
            raise Exception("Finished processing before end of file")

    def WriteToFile(self, f):        
        self.SetSizes()
        self.SetOffsets()
        
        ushortToFile(f,self.MachineType)
        ushortToFile(f,self.NumberOfSections)
        ulongToFile(f,self.Timestamp)
        ulongToFile(f,self.SymbolTableLoc)
        ulongToFile(f,self.SymbolCount)
        ushortToFile(f,self.OptionalHeaderSize)
        ushortToFile(f,self.Characteristics)
        for sec in self.Sections:
            sec.WriteToFilePass1(f)
        for sec in self.Sections:
            sec.WriteToFilePass2(f)
        self.Symbols.WriteToFile(f)

        ulongToFile(f, len(self.StringTable)+4)
        stringToFile(f, len(self.StringTable), self.StringTable)

    def Sizeof(self):
        "header only"
        return 20

    def SetSizes(self):
        for sec in self.Sections:
            sec.SetSizes()
        self.NumberOfSections = len(self.Sections)
        self.SymbolCount = 0
        for sym in self.Symbols:
            sym.SetSizes()
            self.SymbolCount += sym.Rows()

    def SetOffsets(self):
        offset = self.Sizeof()
        offset += len(self.Sections) * 40
        i = 1
        for sec in self.Sections:
            tmpOffset = offset
            offset = sec.SetOffsets(offset)
            assert tmpOffset == sec.RawDataLoc, "section %s data out of sync" % i
            i += 1
        self.SymbolTableLoc = offset
        
    def AddSymbol(self,name="",value=0x0,sec=0x0,typ=0x0,cls=0x0,aux=''):
        fullname = name
        if len(name) > 8: #add name to symbol table and reference
            if name[-1] != '\x00':
                name += '\x00'
            pos = len(self.StringTable) + 4
            self.StringTable += name
            name = '\x00\x00\x00\x00' + ulongToString(pos)        
        self.Symbols.append(coffSymbolEntry(name,value,sec,typ,cls,aux,fullname))    
    
    def DumpInfo(self):
        print "Machine Type: %s" % self.MachineType
        print "Number of sections: %s" % self.NumberOfSections
        print "DateTime %s" % self.Timestamp
        print "Pointer to symbol table %s" % self.SymbolTableLoc
        print "Number of symbols %s" % self.SymbolCount
        print "Optional Header size %s" % self.OptionalHeaderSize
        print "Characteristics: %s" % self.Characteristics
        if self.Characteristics & coffFile.NO_RELOC:print "\tNO RELCATION INTO"
        if self.Characteristics & coffFile.EXECUTABLE: print"\tEXECUTABLE"
        if self.Characteristics & coffFile.NO_LINENO: print "\tNO LINE NOs"
        if self.Characteristics & coffFile.NO_SYMBOLS: print "\tNO SYMBOLS"
        if self.Characteristics & coffFile.LITTLEENDIAN: print "\tLITTLEENDIAN"

        for sec in self.Sections:
            sec.DumpInfo()
        self.Symbols.DumpInfo()
        print "String Table %s" % repr(self.StringTable)

if __name__ == "__main__":      
    f = file("C:/objtest/objtest/Release/objtest.obj","rb")

    coff = coffFile()
    coff.InitFromFile(f)
    f.close()

    coff.DumpInfo()

    f2 = file("C:/objtest/objtest/Release/objtest.obj2","wb")
    coff.WriteToFile(f2)
    f2.close()
