#!/usr/bin/env python

from distutils.core import setup, Extension

excmem = Extension('pyasm.excmem',['pyasm/excmem/excmem.c'])

setup(name='pyasm',
      version='0.2',
      description='dynamic x86 assembler for python',
      author='Grant Olson',
      author_email='olsongt@verizon.net',
      packages=['pyasm','pyasm.test'],
      ext_modules=[excmem]
      )
