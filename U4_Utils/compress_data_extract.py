import sys

# Fetch data from 0x51000 of a rom (that has been byteswapped with swap.py):
# > python compress_data_extract.py u4_dump_swapped compressed_data get
#
# Inject data
# > python compress_data_extract.py u4_dump_swapped compressed_data put

if __name__ == "__main__":
    op = sys.argv[3]
    if op == "get":
        f = open(sys.argv[1], "rb")
        f2 = open(sys.argv[2], "wb")
        f.read(0x51000)
        f2.write(f.read()) # This will grab more than needed. Maybe fix?
        f.close()
        f2.close()
        print ("Extracted data")
    elif op == "put":
        f = open(sys.argv[1], "r+b")
        f2 = open(sys.argv[2], "rb")
        f.seek(0x51000)
        f.write(f2.read())
        f.close()
        f2.close()
        print ("Injected data")

