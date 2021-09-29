# Dependencies:
# - Python 3
# - pypng (https://pypi.org/project/pypng/)
# - compress from U4_Utils in this repo
#
# Example usecase:
# - python extract_gfx.py u2dump
#
# This will produce an output under directory "u2dump_out".
# Note: Does not work for MMP (yet), since it's compression is not implemented.

import sys
import os
import png
# From U4_Utils
import compress

PAGE_LEN  = 2112
BLOCK_LEN = 2112 * 64

def block_addr(block, offset=0):
    return BLOCK_LEN * block + offset

def get_int32(infile):
    return int.from_bytes(infile.read(4), "big")

class Bitmap(object):
    def __init__(self, data, compressed=False):
        self.png_data = []
        self.width = ((data[12] << 8) | data[13]) + 1
        self.height = ((data[14] << 8) | data[15]) + 1
        i = 16 # Initial offset

        for h in range(self.height):
            row = []
            for w in range(self.width):
                row.extend(self._get_clr(data[i:i+2]))
                i += 2
            self.png_data.append(row)
        
    def _get_clr(self, x):
        a = 255 if (x[0] >> 7) else 0
        r = 8 * ((x[0] >> 2) & 0b11111)
        g = 8 * (((x[0] & 0b11) << 3) | (x[1] >> 5))
        b = 8 * (x[1] & 0b11111)
        return (r,g,b,a)
    def write_to_png(self, filename):
        f=open(filename, "wb")
        w = png.Writer(self.width, self.height, greyscale=False, alpha=True)
        w.write(f, self.png_data)
        f.close()
        
class U2Metadata(object):
    def __init__(self):
        self.data = {}
        self.num_entries = 0
    def read_from(self, filename):
        infile = open(filename, "rb")
        self.bad_block_table = infile.read(PAGE_LEN)
    
        while True:
            block = get_int32(infile)
            offset = get_int32(infile)
            length = get_int32(infile)
            compression_info = get_int32(infile)

            if length == 0 or length == 0xFFFFFFFF:
                break
            print ("Data at %s. Length = %s. Compression info: %s" %
                (hex(block_addr(block, offset)), hex(length), hex(compression_info)))
            self.data[self.num_entries] = (block, offset, length, compression_info)
            self.num_entries += 1
        print ("Found %d entries" % self.num_entries)
        infile.close()
    def get_entry_data(self, filename, entry_no):
        infile = open(filename, "rb")
        block, offset, length, compression_info = self.data[entry_no]
        infile.seek(block_addr(block, offset))
        data = infile.read(length)
        if compression_info == 0: # Raw
            return data
        elif compression_info == 0x2000000: # Compressed
            return compress.decompress(data) 
        elif compression_info == 0x4000000: # MMP Compression (unsupported)
            print ("MMP compression not supported: %s" % hex(compression_info))
            sys.exit(1)
        else:
            print ("Unsupported compression: %s" % hex(compression_info))
            sys.exit(1)
        infile.close()

def get_u2_data(infile_name):
    try: os.mkdir(infile_name + "_out")
    except: pass

    metadata = U2Metadata()
    metadata.read_from(infile_name)
    for i in range(metadata.num_entries):    
        data = metadata.get_entry_data(infile_name, i)
        print ("Fetching", i)
        Bitmap(data).write_to_png(infile_name + "_out/u2_" + str(i) + ".png")

if __name__ == "__main__":
    if len(sys.argv) < 2: print ("Please specify U2 file as input")
    else:                 get_u2_data(sys.argv[1])
