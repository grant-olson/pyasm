import pyasm.structs

def PythonConstants(a):
    """
    takes an assembler object and loads appropriate constants for
    python
    """
    a.AC("PyNone",repr(id(None)))

    # add precalculated values from structs modules.
    for obj in dir(pyasm.structs):
        if obj.startswith("_"):
            continue

        for offset in dir(getattr(pyasm.structs,obj)):
            if offset.startswith("_"):
                continue
            
            mangledName = "%s_%s" % (obj,offset)
            val = repr(getattr(getattr(pyasm.structs,obj),offset))
            a.AC(mangledName, val)
            


    