import sys
from gfx_utils import *

def make_gfx(infile_name, outfile_name):
    bm = Bitmap.from_png(infile_name)
    bm.write_to_gfx(outfile_name)

if __name__ == "__main__":
    make_gfx(sys.argv[1], sys.argv[2])
