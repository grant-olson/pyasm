from pyasm import pyasm

pyasm(globals(),r"""
     !CHARS hello_str 'Hello world!\n\0'

     !PROC hello_world PYTHON
     !ARG  self
     !ARG  args
          !CALL PySys_WriteStdout hello_str
          ADD ESP, 0x4
          MOV EAX,PyNone
          ADD [EAX],1
     !ENDPROC
     """)

hello_world()
