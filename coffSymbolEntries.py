# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

"""
Coff symbol entries.

There are a bunch of subclasses of coff symbol entries that MS uses.  Here is an
attempt to create they as actual subclasses so that we're not doing any 'magic'
with the Auxialary strings.

Refer to "Microsoft Portable Executable and Common Object File Format
Specification" revision 6.0 for additional details.
"""
from coffConst import *
from x86PackUnpack import *


class coffSymbolError(Exception): pass

def attemptNameLookup(const,id):
    """ Doesn't necessarily belong here but this avoids circular imports"""
    return const.get(id, "UNDEF??[%0X]" % id)

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


class coffSymbolFile(coffSymbolEntry):
    """
    See section 5.5.4 of Microsoft COFF Spec
    """
    def __init__(self,filename):
        #pad filename with nulls
        filename = filename + "\x00" * (18 - len(filename) % 18)
        coffSymbolEntry.__init__(self,'.file\x00\x00\x00',SymbolValues.SYM_UNDEFINED,-2,
                            SymbolTypes.NULL, SymbolClass.CLASS_FILE, filename)

class coffSectionDef(coffSymbolFile):
    """
    Section Definitions 5.5.5
    """
    def __init__(self,name,sectionNumber,length=0,relocs=0,line_nos=1,chksum=0,number=0,selection=0):
        coffSymbolEntry.__init__(self,name,SymbolValues.SYM_UNDEFINED, sectionNumber,
                            SymbolTypes.NULL, SymbolClass.STATIC)
        self.Length = length
        self.Relocations = relocs
        self.LineNumbers = line_nos
        self.Checksum=chksum
        self.Number = number
        self.Selection = selection
        self.BuildAuxiliaries()

    def BuildAuxiliaries(self):
        aux = ''
        aux += ulongToString(self.Length)
        aux += ushortToString(self.Relocations)
        aux += ushortToString(self.LineNumbers)
        aux += ulongToString(self.Checksum)
        aux += ushortToString(self.Number)
        aux += ucharToString(self.Selection)
        aux += "\x00\x00\x00"
        self.Auxiliaries = aux

    def RebuildAuxiliaries(self,length=0,relocs=0,line_nos=0,chksum=0,number=0,selection=0):
        self.Length = length
        self.Relocations = relocs
        self.LineNumbers = line_nos
        self.Checksum=chksum
        self.Number = number
        self.Selection = selection
        self.BuildAuxiliaries()

class coffFunctionDef(coffSymbolEntry):
    def __init__(self,name,addr,sectionNumber,tag=0,size=0,line=1,fun=0):
        coffSymbolEntry.__init__(self,name,addr, sectionNumber,
                            0x20, SymbolClass.EXTERNAL)
        self.TagIndex = tag
        self.TotalSize = size
        self.PointerToLineNumber = line
        self.PointerToNextFunction = fun
        
        self.BuildAuxiliaries()

    def BuildAuxiliaries(self):
        aux = ''
        aux += ulongToString(self.TagIndex)
        aux += ulongToString(self.TotalSize)
        aux += ulongToString(self.PointerToLineNumber)
        aux += ulongToString(self.PointerToNextFunction)
        aux += "\x00\x00"
        self.Auxiliaries = aux

    def RebuildAuxiliaries(self,tag=0,size=0,line=1,fun=0):
        self.TagIndex = tag
        self.TotalSize = size
        self.PointerToLineNumber = line
        self.PointerToNextFunction = fun
        self.BuildAuxiliaries()

class coffBf(coffSymbolEntry):
    def __init__(self,sec,line=1,nextBf=0):
        coffSymbolEntry.__init__(self,".bf\x00\x00\x00\x00\x00",0,sec,0x20,
                                 101, aux="\x00" * 18)
        self.LineNumber = line
        self.PointerToNextBf = 0
        self.BuildAuxiliaries()

    def BuildAuxiliaries(self):
        aux = '\x00\x00\x00\x00'
        aux += ushortToString(self.LineNumber)
        aux += '\x00\x00\x00\x00\x00\x00'
        aux += ulongToString(self.PointerToNextBf)
        aux += '\x00\x00'
        self.Auxiliaries = aux

    def RebuildAuxiliaries(self,line=1,nextBf=0):
        self.LineNumber = line
        self.PointerToNextBf = nextBf
        self.BuildAuxiliaries()

class coffLf(coffSymbolEntry):
    def __init__(self,sec,lines=1):
        coffSymbolEntry.__init__(self,".lf\x00\x00\x00\x00\x00",lines,sec,0x20,
                                 101)
        
class coffEf(coffSymbolEntry):
    def __init__(self,sec,totalSize=0,line=1,nextBf=0):
        coffSymbolEntry.__init__(self,".ef\x00\x00\x00\x00\x00",totalSize,sec,0x20,
                                 101,aux="\x00" * 18)
        self.LineNumber = line
        self.BuildAuxiliaries()

    def BuildAuxiliaries(self):
        aux = '\x00\x00\x00\x00'
        aux += ushortToString(self.LineNumber)
        aux += '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.Auxiliaries = aux

    def RebuildAuxiliaries(self,line=1):
        self.LineNumber = line
        self.BuildAuxiliaries()

        