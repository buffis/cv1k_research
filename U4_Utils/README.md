# U4 utils

Various utilities for working with CV1000 U4 roms.

## compress.py

Useful for decompressing/compressing data for U4 roms.
Games that use compressing have their compressed data at offset 0x51000.

## swap.py

Swaps bytes of input words. Needed to get U4 readable in Ghidra/elsewhere.

# get_operations.py

Only useful if you want to mess around with compression algorithms. Maybe ignore this.