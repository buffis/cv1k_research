# Tool for adjusting Cave U2 files to work with bad blocks on NAND for repairs.
# Example usages:
#
# List bad blocks of a U2 dump:
#  python u2tool.py bad_blocks dump.u2
#
# Adjust a CLEAN (dump without bad blocks) to work on a NAND with bad blocks
#  python u2tool.py adjust clean_dump.u2 --outfile=adjusted.u2 --bad_blocks=75,229
#
# TODO:
# - Add support for producing a clean dump (no bad blocks) from a dirty one.
# - Maybe add support for cleaning up settings / high score area for later games
#   that store that in NAND.

import argparse
import binascii
import sys

PAGE_SIZE = 0x840
BLOCK_SIZE = 0x21000
NAND_SIZE = BLOCK_SIZE * 1024

def hex_print(bytedata):
    for i, b in enumerate(bytedata):        
        if i == 0 or (i + 1) % 16:
            print (hex(b)[2:], end = " ")
            if not (i + 1) % 8:
                print (" ", end = "")
        else:
            print (hex(b)[2:])

def get_bad_blocks(filename):
    f=open(filename, "rb")
    f.seek(8)  # Bad block table offset.
    blockmap = f.read(128)

    bad_blocks = []
    block = 0
    for x in blockmap:
        for c in range(8):
            if not x & 1:
                bad_blocks.append(block)
            block += 1
            x >>= 1
    return bad_blocks

def make_bad_block_table(bad_blocks = []):
    table = (1 << 1024) - 1
    for block in bad_blocks:
        table -= 1 << block
    return table.to_bytes(128, "little")

def adjust_data(clean_file, out_file, bad_blocks):
    clean_file = open(clean_file, "rb")
    out_file = open(out_file, "wb")

    def handle_block0(bad_blocks):
        out_file.write(clean_file.read(8))  # Dunno what this is
        clean_file.read(128)  # Ignore old table, since it's assumed good.
        out_file.write(make_bad_block_table(bad_blocks))
        out_file.write(clean_file.read(PAGE_SIZE - 128 - 8))  # Here be dragons.

        # Rest of block 1 has the asset mapping.
        offset = 0
        while clean_file.tell() < BLOCK_SIZE:
            next_asset = clean_file.read(4)
            block = int.from_bytes(next_asset, "big")
            if block >= 1024 or block == 0:  # Reached end of assets.
                out_file.write(next_asset)
                out_file.write(clean_file.read(12))
                break
            block += offset
            if block in bad_blocks:
                # Offset everything (including this) by +1 since bad block.
                bad_blocks.remove(block)
                block += 1
                offset += 1
            out_file.write(block.to_bytes(4, "big"))
            out_file.write(clean_file.read(12))
        out_file.write(clean_file.read(BLOCK_SIZE - clean_file.tell()))
    handle_block0(bad_blocks[:])

    # Don't do any magic or cleanup for block 1.
    cur_block = 1
    while out_file.tell() < NAND_SIZE:
        block_data = clean_file.read(BLOCK_SIZE)
        if cur_block in bad_blocks:
            for i in range(0x21000):
                out_file.write(b'\x00')
            cur_block += 1
        out_file.write(block_data)
        cur_block += 1

class Sprite(object):
    def __init__(self, index, block, offset, length, compression):
        self.index = index
        self.block = block
        self.offset = offset
        self.length = length
        self.compression = compression
    def address(self):
        return self.block * BLOCK_SIZE + self.offset

def print_checksums(infile):
    f = open(infile, "rb")
    f.seek(PAGE_SIZE)

    index = 0
    sprites = []
    while True:
        block = int.from_bytes(f.read(4), "big")
        offset = int.from_bytes(f.read(4), "big")
        length = int.from_bytes(f.read(4), "big")
        compression = f.read(4)
        if block >= 1024 or (block + offset + length) == 0:  # Reached end of assets.
            break
        sprites.append(Sprite(index, block, offset, length, compression))
        index += 1        
    
    for sprite in sprites:
        f.seek(sprite.address())
        data = f.read(sprite.length)
        crc = "{0:#0{1}x}".format(binascii.crc32(data), 10)
        print (sprite.index, crc)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('cmd', type=str)
    p.add_argument('infile', type=str)
    p.add_argument('--outfile', type=str)
    p.add_argument('--bad_blocks', type=str,)
    args = p.parse_args()

    if args.cmd == "bad_blocks":
        bad_blocks = get_bad_blocks(args.infile)
        print ("Bad blocks:", bad_blocks, "\n")
        print ("Bad block table:")
        hex_print(make_bad_block_table(bad_blocks))
    if args.cmd == "adjust":
        bad_blocks = list([int(x.strip()) for x in args.bad_blocks.split(",")])
        adjust_data(args.infile, args.outfile, bad_blocks)
    if args.cmd == "checksums":
        print_checksums(args.infile)
