Pyasm
=====

Pyasm is a full-featured dynamic assembler written entirely in
Python. By dynamic, I mean that it can be used to generate and execute
machine code in python at runtime without requiring the generation of
object files and linkage. It essentially allow 'inline' assembly in
python modules on x86 platforms.

Pyasm can also generate object files (for windows) like a traditional
standalone assembler, although you're probably better off using one of
the many freely available assemblers if this is you primary goal.

Pyasm was written as an experimental proof-of-concept, and although it
works, many x86 Opcodes remain to be implemented.

For more information, read the Users Guide, available under
doc/usersGuide.txt in reStructuredText format or [online in
html](http://www.grant-olson.net/python/pyasm).