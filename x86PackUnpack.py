"""
x86PackUnpack.py
----------------

Contains all the functions to go between little-endian data streams and
actual binary data.

"""
import struct, sys

def pylongToSignedInt(x):
    """
    TODO: Use Guido's formula
    """
    if x > 0xFFFFFFFF:
        raise TypeError("This is too big to convert to a signed int")
    elif x >= 0x80000000:
        x = x - sys.maxint - sys.maxint - 2
    else:
        pass
    return int(x)

def ucharFromFile(f):return struct.unpack("<B", f.read(1))[0]
def ushortFromFile(f):return struct.unpack("<H", f.read(2))[0]
def shortFromFile(f):return struct.unpack("<h", f.read(2))[0]
def ulongFromFile(f): return struct.unpack("<L", f.read(4))[0]

def stringFromFile(n,f):return struct.unpack("<%ds" % n, f.read(n))[0]

def ucharToFile(f,u): f.write(struct.pack("<B", u))
def ushortToFile(f, u): f.write(struct.pack("<H", u))
def shortToFile(f, u): f.write(struct.pack("<h", u))
def ulongToFile(f, u): f.write(struct.pack("<L", u))
def stringToFile(f, n, u): f.write(struct.pack("<%ds" % n, u))

# These are a bit wierd because of python's use of longs with
# bitwise operations
def longFromFile(f): return struct.unpack("<L", f.read(4))[0]
def longToFile(f, u): f.write(struct.pack("<i", pylongToSignedInt(u)))