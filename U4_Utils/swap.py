import sys

# Byteswap an input file (passed as argument).
# Useful for dumps.

def swap(infile, outfile):
    f = open(infile, "rb")
    f2 = open(outfile, "wb")
    while f:
        x = f.read(1)
        y = f.read(1)
        f2.write(y)
        f2.write(x)
        if not x: break
    print("Done swapping")

if __name__ == "__main__":
    swap(sys.argv[1], sys.argv[2])
    
