"""
x86tokens.py
------------

I really don't think I'm using this at all.
"""

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
rm32 = token()

r8 = token()
r16 = token()
r32 = token()

imm8 = token()
imm16 = token()
imm32 = token()

mm = token()
xmm = token()

dx = token()
d0 = token()
d1 = token()
d2 = token()
d3 = token()
d4 = token()
d5 = token()
d6 = token()
d7 = token()

rb = token()
rw = token()
rd = token()
