from x86asm import codePackageFromFile
from x86cpToMemory import CpToMemory
from pythonConstants import PythonConstants
import cStringIO

def pyasm(scope,s):
    cp = codePackageFromFile(cStringIO.StringIO(s),PythonConstants)
    mem = CpToMemory(cp)
    mem.MakeMemory()
    mem.BindPythonFunctions(scope)

    