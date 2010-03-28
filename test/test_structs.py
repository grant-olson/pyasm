# Copyright 2004-2010 Grant T. Olson.
# See license.txt for terms.

import unittest
from pyasm.structs import PyObject, PyUnicodeObject

debugOffset = 0
from sys import executable
if executable.endswith("_d.exe"):
     debugOffset = 8

class test_long_to_string(unittest.TestCase):
    def testPyObject(self):
        self.assertEquals(PyObject.ob_refcnt, debugOffset+0)
        self.assertEquals(PyObject.ob_type, debugOffset+4)

    def testPyUnicodeObject(self):
        """ This is the last object, make sure this got generated"""

        self.assertEquals(PyUnicodeObject.ob_refcnt,debugOffset+0)
        self.assertEquals(PyUnicodeObject.ob_type, debugOffset+4)
        self.assertEquals(PyUnicodeObject.str, debugOffset+ 12)

if __name__ == "__main__":
    unittest.main()    
