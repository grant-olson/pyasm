#!/usr/bin/env python

from distutils.core import setup, Extension

excmem = Extension('pyasm.excmem',['pyasm/excmem/excmem.c'])
structs = Extension('pyasm.structs',['pyasm/structs/structs.c'])

setup(name='pyasm',
      version='0.3',
      description='dynamic x86 assembler for python',
      author='Grant Olson',
      author_email='olsongt@verizon.net',
      packages=['pyasm','pyasm.test','pyasm.examples'],
      ext_modules=[excmem, structs]
      )
