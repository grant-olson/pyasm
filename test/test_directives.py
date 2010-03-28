# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

from pyasm.x86asm import assembler
from pyasm.x86cpToMemory import CpToMemory

a = assembler()


a("!COMMENT This is a samle hello world program")
a("!COMMENT by Grant")

a("!CHARS hello_str 'hello world\n\0'")

a("!PROC hello_world PYTHON")
a("!ARG self")
a("!ARG args")
#a("     INT 3")
a("     PUSH hello_str")
a("     CALL PySys_WriteStdout")
a("     ADD ESP,0x4") #CDECL
a("     MOV EAX,%s" % id(None))
a("     ADD [EAX], 0x1")
a("!ENDPROC")

cp = a.Compile()
mem = CpToMemory(cp)

mem.MakeMemory()
mem.BindPythonFunctions(globals())

hello_world()

