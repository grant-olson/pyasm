# Copyright 2004-2005 Grant T. Olson.
# See license.txt for terms.

import unittest
from pyasm.structs import PyObject, PyUnicodeObject

class test_long_to_string(unittest.TestCase):
    def testPyObject(self):
        self.assertEquals(PyObject.ob_refcnt,0)
        self.assertEquals(PyObject.ob_type, 4)

    def testPyUnicodeObject(self):
        """ This is the last object, make sure this got generated"""
        self.assertEquals(PyUnicodeObject.ob_refcnt,0)
        self.assertEquals(PyUnicodeObject.ob_type, 4)
        self.assertEquals(PyUnicodeObject.str, 12)

if __name__ == "__main__":
    unittest.main()    