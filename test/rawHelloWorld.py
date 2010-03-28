# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

from pyasm.coff import coffFile, coffSection, coffRelocationEntry, coffSymbolEntry
from pyasm.coffConst import *
import time,os,sys

"""Creates a simple .objfile that should be good enough to
link as a hello world program"""

c = coffFile()

c.MachineType = coffFile.I386MAGIC

s1 = coffSection()
s1.Name = ".drectve"
s1.Flags = (SectionFlags.LNK_REMOVE |
            SectionFlags.LNK_INFO |
            SectionFlags.ALIGN_1BYTES)
s1.RawData = '-defaultlib:LIBCMT -defaultlib:OLDNAMES '
c.Sections.append(s1)

s2 = coffSection()
s2.Name = ".text\x00\x00\x00"
s2.Flags = (SectionFlags.CNT_CODE |
            SectionFlags.LNK_COMDAT |
            SectionFlags.MEM_EXECUTE |
            SectionFlags.MEM_READ |
            SectionFlags.ALIGN_16BYTES)
s2.RawData = "\x68\x00\x00\x00\x00\xE8\x00\x00\x00\x00\x83\xC4\x04\x33\xC0\xC3"

r = coffRelocationEntry(addr=0x1,sym=0xC,typ=RelocationTypes.I386_DIR32)
s2.RelocationData.append(r)

r= coffRelocationEntry(addr=0x6,sym=0x9,typ=RelocationTypes.I386_REL32)
s2.RelocationData.append(r)

c.Sections.append(s2)


s3 = coffSection()
s3.Name = '.data\x00\x00\x00'
s3.Flags = (SectionFlags.LNK_COMDAT |
            SectionFlags.CNT_INITIALIZED_DATA |
            SectionFlags.MEM_WRITE |
            SectionFlags.MEM_READ |
            SectionFlags.ALIGN_4BYTES)
s3.RawData = '\x48\x65\x6c\x6c\x6f\x20\x57\x6f\x72\x6c\x64\x21\x0a\x00'
c.Sections.append(s3)

s4=coffSection()
s4.Name = '.debug$F'
s4.Flags = (SectionFlags.LNK_COMDAT |
            SectionFlags.TYPE_NO_PAD |
            SectionFlags.CNT_INITIALIZED_DATA |
            SectionFlags.MEM_DISCARDABLE |
            SectionFlags.MEM_READ |
            SectionFlags.ALIGN_1BYTES)
s4.RawData = '\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00'

r = coffRelocationEntry(addr=0x0,sym=0x8,typ=RelocationTypes.I386_DIR32NB)
s4.RelocationData.append(r)

c.Sections.append(s4)

s = coffSymbolEntry('.file\x00\x00\x00',SymbolValues.SYM_UNDEFINED,-2,
                    SymbolTypes.NULL, SymbolClass.CLASS_FILE)
s.Auxiliaries = 'C:\\objtest\\objtest\\objtest.cpp\x00\x00\x00\x00\x00\x00'
c.Symbols.append(s)

s = coffSymbolEntry('@comp.id',0xB2306, -1, SymbolTypes.NULL, SymbolClass.STATIC)
c.Symbols.append(s)

s = coffSymbolEntry('.drectve', SymbolValues.SYM_UNDEFINED, 1, SymbolTypes.NULL,
                    SymbolClass.STATIC)
s.Auxiliaries = '&\x00\x00\x00\x00\x00\x00\x00O\xe0\xad\x98\x00\x00\x00\x00\x00\x00'
c.Symbols.append(s)

s = coffSymbolEntry('.text\x00\x00\x00', SymbolValues.SYM_UNDEFINED, 2,
                    SymbolTypes.NULL, SymbolClass.STATIC)
s.Auxiliaries = "\x10\x00\x00\x00\x02\x00\x00\x00\x9d\xf0\xcd3\x00\x00\x01\x00\x00\x00"
c.Symbols.append(s)

s = coffSymbolEntry('_main\x00\x00\x00', SymbolValues.SYM_UNDEFINED, 2, 0x20,
                    SymbolClass.EXTERNAL)
c.Symbols.append(s)

s = coffSymbolEntry('_printf\x00', SymbolValues.SYM_UNDEFINED, 0, 0x20,
                    SymbolClass.EXTERNAL)
c.Symbols.append(s)

s = coffSymbolEntry('.data\x00\x00\x00', SymbolValues.SYM_UNDEFINED, 3,
                    SymbolTypes.NULL, SymbolClass.STATIC)
s.Auxiliaries = '\x0e\x00\x00\x00\x00\x00\x00\x00\xfe,\xa6\xfb\x00\x00\x02\x00\x00\x00'
c.Symbols.append(s)

s = coffSymbolEntry('\x00\x00\x00\x00\x04\x00\x00\x00', SymbolValues.SYM_UNDEFINED, 3,
                    SymbolTypes.NULL, SymbolClass.EXTERNAL)
c.Symbols.append(s)

s = coffSymbolEntry('.debug$F', SymbolValues.SYM_UNDEFINED, 4, SymbolTypes.NULL,
                    SymbolClass.STATIC)
s.Auxiliaries = '\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x05\x00\x00\x00'
c.Symbols.append(s)

c.StringTable = '??_C@_0O@FEEI@Hello?5World?$CB?6?$AA@\x00'

c.SetSizes()
c.SetOffsets()

#c.DumpInfo()

f = file("output/rawHelloWorld.obj","wb")
c.WriteToFile(f)
f.close()

if sys.platform == 'win32':
    os.system("cd output && link rawHelloWorld.obj")
    os.system("cd output && rawHelloWorld.exe")
else:
    print "Skipping linker test, coff files are only valid on win32 platforms"
    
