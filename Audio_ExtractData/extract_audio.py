# Usage:
# python extract_audio.py u23 u24

import sys
import os
import swap

def to_byte(x, size=1): return x.to_bytes(size, byteorder="big")

def calculate_bitrate(len):
    """Guess bitrate + padding based on packet length. A bit hacky.
    Output is (bitflag for mp2 header, kbps bitrate, padding bytes)."""
    if 430 <= len <= 432:
        pad = 432 - len
        return (6, 48000, pad)
    if 358 <= len <= 360:
        pad = 360 - len
        return (5, 40000, pad)
    else:
        print ("Unexpected packet length!", len)
        return None

class AmmMpeg(object):
    def __init__(self, data):
        self.data = data
        self.data_ptr = 0
        self.min_packet_len = 0

    def _next(self, n=1, increment=True):
        data = self.data[self.data_ptr: self.data_ptr + n]
        if increment: self.data_ptr += n
        return data

    def _get_header_info1(self):
        pkt_data = int.from_bytes(self._next(), byteorder="big")
        full_pkt_count = pkt_data >> 4
        srate_index = (pkt_data >> 2) & 0b11
        last_packet_frame_id = pkt_data & 0b11
        return (full_pkt_count, srate_index, last_packet_frame_id)
    def _get_header_info2(self): # Should this be used?
        return self._next()

    def _get_packet(self):
        if self._next(2, False) == b"\xFF\xF0":
            return False  # End of packet.

        start = self.data_ptr

        sync = self._next(2)
        if sync == b"\xFF\xFc":
            print ("Empty sequence")
            return False
        if sync != b"\xFF\xF4":
            print ("Unexpected start of packet", sync)
            return False

        (full_pkt_count, srate_index, last_packet_frame_id) = self._get_header_info1()
        self._get_header_info2()

        if full_pkt_count == 0:
            return False  # No data in packet!

        while True:
            nxt = self._next(2, False)

            # If we have a minimum packet length, read at most that many packets.
            if self.min_packet_len and (self.data_ptr - start) < self.min_packet_len:
                self.data_ptr += 1
            elif nxt == b"\xFF\xF4": break  # New packet.
            elif nxt == b"\xFF\xF0": break  # End of sequence.
            else: self.data_ptr += 1

        packet_len = self.data_ptr - start
        (br_flag, br_real, pad) = calculate_bitrate(packet_len)
        
        out_data = self._make_mpeg_header(bitrate=br_flag, pad=pad) + self.data[start + 4: self.data_ptr]
        out_data += b'\x00' * pad

        if not self.min_packet_len:
            self.min_packet_len = len(out_data) - 2  # May pad up to two bytes.

        return out_data
        
    def to_mp2(self, outfile_name):
        pkt = self._get_packet()
        if not pkt: return

        f = open(outfile_name, "wb")
        while pkt:
            f.write(pkt)
            pkt = self._get_packet()
        f.close()

    def _make_mpeg_header(self, bitrate=5, samplerate = 2, pad=0, mpeg_ver=2, layer=2):
        b1 = 0xFF  # Sync
        b2 = 0b11100000 | (mpeg_ver << 3) | (layer << 1) | 0b1
        b3 = (bitrate << 4) | (samplerate << 2 )
        b4 = 0b11000100
        return to_byte(b1) + to_byte(b2) + to_byte(b3) + to_byte(b4)

class AudioData(object):
    def __init__(self, u23="u23", u24="u24"):
        swap.swap(u23, "swapped_" + u23)
        swap.swap(u24, "swapped_" + u24)
        self.u23 = open("swapped_" + u23, "rb")
        self.u24 = open("swapped_" + u24, "rb")
        self.data = self.u23.read() + self.u24.read()
        
        self.phrases = []
        self.sequences = []
        self.simple_access_codes = []
    
    def _read_u23_entry(self, target):
        target.append(int.from_bytes(self.u23.read(4)[1:], byteorder="big"))

    def read_header(self):
        self.u23.seek(0)
        i = 0
        while i < 0xC00:
            if i < 0x400:    self._read_u23_entry(self.phrases)
            elif i < 0x800:  self._read_u23_entry(self.sequences)
            else:            self._read_u23_entry(self.simple_access_codes)
            i += 4

    def print_list(self):
        l = self.phrases
        for i, x in enumerate(l):
            sys.stdout.write("%d : %s" % (i, hex(x)))
            if i and not i % 5:
                sys.stdout.write("\n")
            else:
                sys.stdout.write("  ")
    
    def get_phrase_data(self, idx):
        start = self.phrases[idx]
        i = start
        while True:
            if self.data[i:i+3] == b"\xFF\xF0\xFF": break
            i += 1
        end = i + 2
        print ("SFX at:", hex(start), " - ", hex(end))
        return self.data[start: end]

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print ("Please specify u23 and u24 files as inputs")
        sys.exit(1)
    u23, u24 = sys.argv[1], sys.argv[2]
    
    try: os.mkdir("out")
    except: pass

    a = AudioData(u23, u24)
    a.read_header()
    for i in range (256):
        m = AmmMpeg(a.get_phrase_data(i))
        m.to_mp2("out/"+ str(i) + ".mp2")