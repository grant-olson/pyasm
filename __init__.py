from x86asm import codePackageFromFile
from x86cpToMemory import CpToMemory
#from pythonConstants import PythonConstants
import cStringIO

def PythonConstants(a):
    """
    HACK UNTIL WE FIGURE OUT WHY DISTUTILS WON'T ADD pythonConstants.py
    takes an assembler object and loads appropriate constants for
    python
    """
    a.AC("PyNone",repr(id(None)))

def pyasm(scope,s):
    cp = codePackageFromFile(cStringIO.StringIO(s),PythonConstants)
    mem = CpToMemory(cp)
    mem.MakeMemory()
    mem.BindPythonFunctions(scope)

    