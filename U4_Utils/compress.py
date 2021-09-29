import sys
import mmap
import math
import io

##
## Stuff for working with CV1000 compression.
##
## To decompress data from a rom:
## - Byteswap rom (see swap.py)
## - Copy bytes starting from 0x51000 to a file 'compressed.bin'
## - python compress.py compressed.bin decompressed.bin d
##
## To compress data for a rom:
## - Get your uncompressed data in a file decompressed.bin
## - python compress.py decompressed.bin compressed.bin c
## - Place data at offset 0x51000
##

def decompress(in_data):
    def _read_int_32(src, offset):
        return int.from_bytes(src[offset:offset+4], "big")
    output_size =    _read_int_32(in_data, 0)
    bitflags_count = _read_int_32(in_data, 4)
    data_offset =    _read_int_32(in_data, 8)
    print ("Size: ", hex(output_size), " Ops: ", bitflags_count, " Data offset: ", hex(data_offset))
    
    out_data = mmap.mmap(-1, output_size)

    bits_loaded = 0
    bitflag_byte = 0
    out_ptr = 0
    bitflag_ptr = 0x0C
    while bitflags_count != 0:
        if bits_loaded == 0:
            # Load a new byte from bitflags.
            bitflag_byte = in_data[bitflag_ptr]
            bitflag_ptr += 1
            bits_loaded = 8
        if (bitflag_byte & 0x80) == 0:
            # Uncompressed. Raw copy from input.
            out_data[out_ptr] = in_data[data_offset]
            out_ptr += 1
        else:
            # Compressed. Fetch data from output to write again.
            x = in_data[data_offset]
            data_offset += 1
            compresion_header = ((x << 8) & 0xFF00) | (in_data[data_offset] & 0xFF)
            feedback_length = (compresion_header & 0x1F) + 3
            feedback_offset = out_ptr - (compresion_header >> 5)
            while feedback_length > 0:
                reused_data = out_data[feedback_offset]
                feedback_offset += 1
                out_data[out_ptr] = reused_data
                out_ptr += 1
                feedback_length -= 1
        data_offset += 1
        bits_loaded -= 1
        bitflags_count -= 1
        bitflag_byte <<= 1
    
    print ("Wrote: ", hex(out_ptr), " expected: ", hex(output_size))
    assert out_ptr == output_size
    return out_data.read()

def compress(in_data):
    out_data = mmap.mmap(-1, len(in_data))
    bitmasks = mmap.mmap(-1, 1000000)  # Just picked a big number. RAM is cheap.

    # TODO: Better docstring.
    def _find_data(in_ptr):
        """ Look for longest patterns before "in_ptr" which matches.
            Return (offset, length) where offset is backwards from in_ptr."""
        # Look up to 2047 bytes behind the search pointer.
        search_start = max(0, in_ptr - (0xFFFF >> 5))
        
        # Normally it's fine to look up to 33 bytes ahead of the
        # search pointer for expansions
        search_end = min(in_ptr + 33, len(in_data))
        # ... but at the start of the input, this is not allowed for some reason.
        # Not obvious to me why this edgecase is in place, but otherwise the compressed
        # data will not match what's on PCBs.
        if in_ptr < 34:
            search_end = in_ptr
                    
        search_bytes = in_data[search_start: search_end]
        
        hit = (-1, 0)  # No hit.
        for x in range (3, 0x1F+4):
            # Don't look further in memory map than the file size.
            if in_ptr + x > len(in_data):
                break

            # Look for matches that start at least one character before in_ptr.
            hit_index = search_bytes.find(in_data[in_ptr: in_ptr+x])
            if hit_index != -1 and (search_start + hit_index + 1) <= in_ptr:
                hit = (in_ptr - search_start - hit_index, x)
            else:
                # No match at this length. Return longest prior match.
                return hit
        return hit

    in_ptr = 0
    out_ptr = 0
    output_size = 0
    num_bitflags = 0
    bitdata = 0
    while (in_ptr < len(in_data)):
        h = _find_data(in_ptr)
        if h[0] == -1:
            # No earlier matches, raw write.
            out_data[out_ptr] = in_data[in_ptr]
            in_ptr += 1
            out_ptr += 1
            output_size += 1
        else:
            # Matched! Write compression header.
            compression_header = ((h[0]) << 5) | (h[1]-3)
            out_data.seek(out_ptr)
            out_data.write_byte(compression_header >> 8)
            out_data.write_byte(compression_header & 0xFF)
            in_ptr += h[1]
            out_ptr += 2
            output_size += h[1]
        if num_bitflags > 0 and (num_bitflags % 8 == 0):
            # Filled up a byte of bitflags. Start a new one.
            bitmasks.write_byte(bitdata)
            bitdata = 0
        # Write bitflag (0=raw, 1=compressed).
        bitdata = (bitdata << 1) | (h[1] > 0)
        num_bitflags += 1

    # Flush remaining bitflags and seek to start.
    if (num_bitflags % 8 != 0):
        bitdata = bitdata << (8 - (num_bitflags%8))
    bitmasks.write_byte(bitdata)
    bitmasks.seek(0)
        
    data_offset = math.ceil(num_bitflags / 8) + 12
    print ("Output size:", output_size)
    print ("Num bitflags:", num_bitflags)
    print ("Data offset:", data_offset)

    outfile = io.BytesIO()
    outfile.write(output_size.to_bytes(4, 'big'))
    outfile.write(num_bitflags.to_bytes(4, 'big'))
    outfile.write(data_offset.to_bytes(4, 'big'))
    
    outfile.write(bitmasks.read(math.ceil(num_bitflags / 8)))
    
    out_data.seek(0)
    outfile.write(out_data.read(out_ptr))
    outfile.seek(0)
    return outfile.read()

if __name__ == "__main__":
    infile = open(sys.argv[1], "r+b")
    outfile = open(sys.argv[2], "wb")
    if sys.argv[3] == "c":
        compressed = compress(infile.read())
        outfile.write(compressed)
    elif sys.argv[3] == "d":
        decompressed = decompress(infile.read())
        outfile.write(decompressed)
    infile.close()
    outfile.close()