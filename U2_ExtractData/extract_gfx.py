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
# From U4_Utils
import compress
from gfx_utils import *
        
class U2Metadata(object):
    def __init__(self):
        self.data = {}
        self.num_entries = 0
        self.bad_blocks = []

    def _read_bad_block_table(self, infile):
        bad_block_table = infile.read(PAGE_LEN)[8: 8 + 128]
        i = 0
        for b in bad_block_table:
            for _ in range(8):
                if not b & 1:
                    self.bad_blocks.append(i)
                b >>= 1
                i += 1

    def _read_data(self, infile, start_block, offset, length):
        """Read data from infile, respecting bad blocks."""
        end_block = get_block(block_addr(start_block, offset + length - 1))
        assert start_block not in self.bad_blocks, "Trying to read from bad block."
            
        start_addr = block_addr(start_block, offset) 
        infile.seek(start_addr)
        if end_block not in self.bad_blocks:
            return infile.read(length)
        else:
            # Read rest from starting block.
            bytes_from_start_block = block_addr(start_block + 1) - start_addr
            data1 = infile.read(bytes_from_start_block)

            # Skip ahead to next working block
            while end_block in self.bad_blocks:
                end_block += 1

            # Read rest of data from second block. Assume reads don't span three blocks.
            # TODO: Support reads across more than 2 blocks?
            infile.seek(block_addr(end_block))
            assert length - bytes_from_start_block < BLOCK_LEN, "Read across three blocks"
            data2 = infile.read(length - bytes_from_start_block)
            return data1 + data2

    def read_from(self, filename):
        infile = open(filename, "rb")
        self._read_bad_block_table(infile)
        if self.bad_blocks:
            print ("Found bad blocks:", self.bad_blocks)
    
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
        data = self._read_data(infile, block, offset, length)
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
        Bitmap.from_u2_data(data).write_to_png(infile_name + "_out/u2_" + str(i) + ".png")

if __name__ == "__main__":
    if len(sys.argv) < 2: print ("Please specify U2 file as input")
    else:                 get_u2_data(sys.argv[1])
