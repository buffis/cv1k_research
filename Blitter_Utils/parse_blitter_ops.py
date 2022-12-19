import sys
from collections import defaultdict

# To use:
# - Run MAME with debugger
# - When you want to dump Blitter operations for a frame do:
# - wpset 18000008,1,w,1,{dump blitter_ops.txt,(wpdata-0xA0000000),20000}
# - The debugger will stop at the next frame, and write the operations for it to blitter_ops.txt
# - Parse it with: python parse_blitter_ops.py blitter_ops.txt

def hextointpos(x):
    return int(x,16)
def hextointdim(x):
    return int(x,16) + 1

def extract_hex_instructions(f):
    hexdata = []
    for line in f.readlines():
        tmp = line[9:-17].strip()
        hexdata.append(tmp[:16] + tmp[17:])
    return "".join(hexdata)

def dump_data(data, num_chars):
    split_data = [data[offset:offset+4] + " " for offset in range(0, num_chars, 4)]
    return "".join(split_data)

def parse(hexdata):
    cmd_count = defaultdict(int)
    length_bytes = 0
    seen_sizes = []
    last_draw = ("", 0)
    while(hexdata):
        cmd = hexdata[:1]
        if cmd == "F" or cmd == "0":
            cmd_count["exit"] += 1
            print ("Exit", cmd)
            break
        elif cmd == "C":
            cmd_count["clip"] += 1
            print ("Clip", dump_data(hexdata, 8))
            hexdata = hexdata[8:]
            length_bytes += 4
        elif cmd == "2":
            cmd_count["upload"] += 1
            print ("Upload", dump_data(hexdata, 32))
            dstx = hextointpos(hexdata[16:20])
            dsty = hextointpos(hexdata[20:24])
            dimx = hextointdim(hexdata[24:28])
            dimy = hextointdim(hexdata[28:32])
            print ("  Dst: %d,%d. Dim: %d,%d" % (dstx, dsty, dimx, dimy)) 
            hexdata=hexdata[32+4*dimx*dimy:]
            length_bytes += 16+2*dimx*dimy
        elif cmd == "1":
            cmd_count["draw"] += 1
            print ("Draw", dump_data(hexdata, 40))
            attr = hexdata[1:4]
            src_alpha, dst_alpha = hexdata[4:6], hexdata[6:8]
            src_x, srx_y = hextointpos(hexdata[8:12]), hextointpos(hexdata[12:16])
            dst_x, dst_y = hextointpos(hexdata[16:20]), hextointpos(hexdata[20:24])
            src_w, src_h = hextointdim(hexdata[24:28]), hextointdim(hexdata[28:32])
            src_r, src_g, src_b = hexdata[34:36], hexdata[36:38], hexdata[38:40]
            sz = "%d x %d" % (src_w, src_h)
            if not last_draw[0]:
                last_draw = (sz, 1)
            else:
                if last_draw[0] != sz:
                    seen_sizes.append(last_draw)
                    last_draw = (sz, 1)
                else:
                    last_draw = (sz, last_draw[1]+1)
            print ("  Attr %s. Alpha: %s, %s. Src XY: %d, %d." \
                "Dst XY: %d, %d. Src w/h: %d,%d. Src RGB: %s,%s,%s" % 
                (attr, src_alpha, dst_alpha,
                    src_x, srx_y, dst_x, dst_y, src_w, src_h, src_r, src_g, src_b))
            hexdata=hexdata[40:]
            length_bytes += 20
        else:
            print("Unexpected command", cmd)
    seen_sizes.append(last_draw)

    print ("")
    print ("Operation list length:", length_bytes, "bytes")
    print ("Seen Operations:")
    for cmd, cnt in cmd_count.items():
        print (" ", cmd, "(", cnt, "times )")
    print ("Draw size sequences (image_size, image_count):")
    for x in seen_sizes:
        print ("   -" , x)

if __name__ == "__main__":
    f = open(sys.argv[1])
    hexdata = extract_hex_instructions(f)
    parse(hexdata)
