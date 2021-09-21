import sys
import mmap
import math

# Used to produce a file containing all compression operations of a compressed CV1000 
# program rom section. Only relevant when debugging compression/decompression algorithms.
#
# Usage examples:
#
# Reads operations from a compressed file from offset 0.
# > python get_operations.py compressed_data operation_output
# 
# Reads operations from a CV1000 rom with compressed data at offset 0x51000
# > python get_operations.py u4_dump operation_output 51000

def get_ops(infile, outfile, in_offset=0, out_offset=0):
    in_data = mmap.mmap(infile.fileno(), 0)

    def _read_int_32(src, offset):
        return int.from_bytes(src[offset:offset+4], "big")
    output_size = _read_int_32(in_data, in_offset)
    bitflags_count = _read_int_32(in_data, in_offset + 4)
    data_offset = in_offset + _read_int_32(in_data, in_offset + 8)
    start_offset = data_offset
    bitflag_addr = in_offset + 0x0C

    bits_loaded = 0
    bitflag_byte = 0

    num_raw = 0
    num_compressed = 0
    b = 0
    while bitflags_count != 0:
        if bits_loaded == 0:
            # Load a new byte from bitflags.
            bitflag_byte = in_data[bitflag_addr]
            bitflag_addr += 1
            bits_loaded = 8
        if (bitflag_byte & 0x80) == 0:
            # Uncompressed. Raw copy from input.
            outfile.write("R:=" + str(out_offset) + "\n")
            out_offset += 1
            num_raw += 1
        else:
            # Compressed. Fetch data from output to write again.
            x = in_data[data_offset]
            data_offset += 1
            compresion_header = ((x << 8) & 0xFF00) | (in_data[data_offset] & 0xFF)
            feedback_length = (compresion_header & 0x1F) + 3
            num_compressed += 1
            outfile.write("C:=" + str(out_offset) + ",L=" + str(feedback_length) + ",OFF="+ str((compresion_header >> 5)) + "\n")
            out_offset += feedback_length
        data_offset += 1
        bits_loaded -= 1
        bitflags_count -= 1
        bitflag_byte <<= 1
    
    print ("Raw: ", num_raw, " Compressed: ", num_compressed)
    return output_size

if __name__ == "__main__":
    infile = open(sys.argv[1], "r+b")
    outfile = open(sys.argv[2], "w")
    offset = 0
    if len(sys.argv) > 3:
        offset = int(sys.argv[3], 16)
    get_ops(infile, outfile, offset, offset)
    infile.close()
    outfile.close()