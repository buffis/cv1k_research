# Usage:
# python get_block.py u2_dump start_block end_block
#
# Will output to "blocks_to_write"

import sys

if __name__ == "__main__":
    f = open(sys.argv[1], "rb")
    first_block = int(sys.argv[2])
    last_block = int(sys.argv[3])
    blocks = last_block - first_block + 1
    f.seek(first_block * 0x21000)
    data = f.read(blocks * 0x21000)
    f.close()

    f = open("blocks_to_write", "wb")
    f.write(data)
    f.close()