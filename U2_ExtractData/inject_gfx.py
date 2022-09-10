import sys
import compress # From U4_Utils
import mmap
from gfx_utils import *

def inject_gfx_at(u2_file, gfx_file, asset_no, block, offset=0):
    u2 = open(u2_file, "r+b")
    gfx = open(gfx_file, "rb")
    gfx_data = compress.compress(gfx.read())
    gfx_len = len(gfx_data)
    gfx.close()

    data = mmap.mmap(u2.fileno(), 0)
    data.seek(8)
    for i in range(128):
        data.write(b'\xFF')  # Assume we're all good!
    data.seek(PAGE_LEN)
    for i in range(asset_no):
        data.read(16) # Skip.
    data.write(block.to_bytes(4, "big"))
    data.write(offset.to_bytes(4, "big"))
    data.write(gfx_len.to_bytes(4, "big"))
    data.write(b'\x02\x00\x00\x00') # Compressed

    data.seek(block_addr(block, offset))
    data.write(gfx_data)
    u2.close()

if __name__ == "__main__":
    if len(sys.argv) < 2: print ("Please specify U2 file as input")
    else:                 inject_gfx_at(sys.argv[1],     sys.argv[2],
                                      int(sys.argv[3]), int(sys.argv[4]))
