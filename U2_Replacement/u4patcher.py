# Replaces 32 10 8b 13 61 e3 71 04 71 01 61 10 62 1c 91 23 32 10 8b 0b
# with     31 10 8b 13 61 e3 71 04 71 01 61 10 62 1c 91 23 31 10 8b 0b
# Diff      *                                               *

import mmap
import sys

if __name__ == "__main__":
    infile = open(sys.argv[1], "r+b")
    data = mmap.mmap(infile.fileno(), 0)
    i = data.find(bytes.fromhex("".join("32 10 8b 13 61 e3 71 04 71 01 61 10 62 1c 91 23 32 10 8b 0b".split())))
    if i == -1:
        print ("Flash check not found! Did you swap and decompress the data?")
        sys.exit(1)
    print ("Found check at ", i)
    data[i]  = data[i]  - 1
    data[i + 16] = data[i + 16] - 1
    infile.close()
    print ("Successfully patched.")
