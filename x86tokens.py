class token:
    """"
    A token's only useful property is that it evaluates to itself
    and only itself
    """
    def __cmp__(self,other):
        return self is other
    def __hash__(self):
        return id(self)

rm8 = token()
rm16 = token()
rm32 = token

r8 = token()
r16 = token()
r32 = token()

imm8 = token()
imm16 = token()
imm32 = token()



        
