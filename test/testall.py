import unittest

"""
Quick and dirty way to run all tests.  Should probably use introspection
in the future.
"""

from rawHelloWorld import *
from disasmHelloWorld import *
from test_x86asm import *
from test_x86inst import *
from test_x86tokenizer import *
from test_object_creation import *
from test_bugs import *
from test_variables import *


if __name__ == "__main__":
    unittest.main()