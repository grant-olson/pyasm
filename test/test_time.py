from pyasm.x86asm import assembler, CDECL
from pyasm.x86cpToMemory import CpToMemory

nonePointer = id(None)
noneRefcount = nonePointer

a = assembler()
a.ADStr("hello_world", "Hello world!\n\0")
a.AP("test_print", CDECL)
a.AddLocal("self")
a.AddLocal("args")
#a.AI("INT 3")
a.AI("PUSH hello_world")
a.AI("CALL PySys_WriteStdout")
#a.AI("INT 3")
a.AI("MOV EAX,%s" % id(None))
a.AI("ADD [EAX],0x1")
a.EP()


mem = CpToMemory(a.Compile())
mem.MakeMemory()
mem.BindPythonFunctions(globals())

def normalHelloWorld():
    print "Hello World!"
    return None

