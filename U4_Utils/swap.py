import sys

# Byteswap an input file (passed as argument).
# Useful for U4 dumps.

if __name__ == "__main__":
    f = open(sys.argv[1], "rb")
    f2 = open(sys.argv[2], "wb")
    while f:
        x = f.read(1)
        y = f.read(1)
        f2.write(y)
        f2.write(x)
        if not x: break
    print("Done")
