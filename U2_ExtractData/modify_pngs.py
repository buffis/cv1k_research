import png
import glob
import sys

def flatten(t): return [item for sublist in t for item in sublist]

def join(files, outfile):
    out_data = []
    w, h = 0, 0
    out_w = 0
    for filename in glob.glob(files):
        print ("Reading", filename)
        reader = png.Reader(filename).asRGBA()

        if h == 0:
            (w, h) = reader[:2]
        if (w, h) != reader[:2]:
            print ("Trying to join with sizes ", (w,h), " and ", reader[:2])
        if not out_data:
            out_data.extend(reader[2])
        else:
            for i, row in enumerate(reader[2]):
                out_data[i] = row + out_data[i]

        out_w += w

    f=open(outfile, "wb")
    w = png.Writer(out_w, h, greyscale=False, alpha=True)
    w.write(f, out_data)
    f.close()

def rotate_r(filename, outfile):
    reader = png.Reader(filename).asRGBA()
    (w, h, data) = reader[:3]
    data = flatten(data)

    rows = []
    for y in range(w):
        print (y)
        row = []
        for x in range(h):
            old_x = w - y - 1
            old_y = x
            i = old_y*w*4 + old_x*4
            row.extend(data[i: i+4])
        rows.append(row)
    f=open(outfile, "wb")
    w = png.Writer(h, w, greyscale=False, alpha=True)
    w.write(f, rows)
    f.close()
    
if __name__ == "__main__":
    op = sys.argv[1]
    if op == "join":
        join(sys.argv[2], sys.argv[3])
    if op == "rotate":
        rotate_r(sys.argv[2], sys.argv[3])
    