import re

class labelRef:
    def __init__(self, name):
        self.Name = name
        
class label:
    def __init__(self, name):
        self.Name = name
        self.Address = 0x0
        
class data:
    def __init__(self, dat):
        self.Data = dat
        self.Address = 0x0

regRe = ''
memRe = ''
commaRe = ''
labelRe = ''
numberRe = ''


class assembler:
    def __init__(self):
        self.Instructions = []
        self.Data = []
        self.Labels = {}

    def registerLabel(self,lbl):
        if self.Labels.has_key(lbl.Name):
            raise RuntimeError("Duplicate Label Registration [%s]" % lbl.Name)
        self.Labels[lbl.Name] = lbl
        
    def AddInstruction(self,inst):
        self.Instructions.append(inst)

    def AI(self,inst):
        self.AddInstruction(inst)

    def AddInstructionLabel(self,name):
        lbl = label(name)
        self.registerLabel(lbl)
        self.Instructions.append(lbl)

    def AIL(self,name):
        self.AddInstructionLabel(name)

    def AddData(self,name,dat):
        lbl = label(name)
        self.registerLabel(lbl)
        self.Data.append(lbl)
        self.Data.append(data(dat))


if __name__ == '__main__':
    a = assembler()
    a.AddData('hw_string','Hello, World!\n\0')
    a.AIL('_main')
    a.AI('PUSH hw_string')
    a.AI('CALL _printf')
    a.AI('ADD ESP,4')
    a.AI('XOR EAX,EAX')
    a.AI('RET')

    