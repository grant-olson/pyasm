"""
Coff symbol entries.

There are a bunch of subclasses of coff symbol entries that MS uses.  Here is an
attempt to create they as actual subclasses so that we're not doing any 'magic'
with the Auxialary strings.
"""
from coffConst import *
from x86PackUnpack import *

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


            