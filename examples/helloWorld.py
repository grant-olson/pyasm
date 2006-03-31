from pyasm import pyasm

pyasm(globals(),r"""
     !PROC hello_world PYTHON
     !ARG  self
     !ARG  args
          !CALL PyString_FromString 'Hello world!\n\0'
          ADD ESP, 0x4

          ADD EAX,PyStringObject_ob_sval
          PUSH EAX
          PUSH EDI
          MOV EDI,EAX
          MOV AL, 0x42
          STOSB
          MOV AL, 0x43
          STOSB
          POP EDI
          CALL PySys_WriteStdout
          ADD ESP, 0x4
          MOV EAX,PyNone
          ADD [EAX+PyObject_ob_refcnt],1
     !ENDPROC
     """)

hello_world()
