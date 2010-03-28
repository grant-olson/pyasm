# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

import sys

"""
By default we link with the MSVC toolchain.  Change 'True' to 'False'
if you want to use the mingw toolchain.

Thanks to Markus Lall for figuring out that (bizarrely) the mingw ld
will not link coff format files, but running the object file through
gcc will cause the files to link correctly.

"""

if True:
    def linkCmd(s):
        return "cd output && link /DEBUG /OPT:REF /OPT:ICF %s.obj" % s
else:
    def linkCmd(s):
        return "cd output && gcc %s.obj -o %s.exe" % (s,s)

