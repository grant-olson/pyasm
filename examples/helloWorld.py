from pyasm import pyasm

pyasm(globals(),r"""
     !PROC hello_world PYTHON
     !ARG  self
     !ARG  args
          !CALL PySys_WriteStdout 'Hello world!\n\0'
          ADD ESP, 0x4
          MOV EAX,PyNone
          ADD [EAX],1
     !ENDPROC
     """)

hello_world()
