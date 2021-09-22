# Replacing U2 with other NAND Flash 

By default, CV1000 comes with a K9F1G08U0M NAND Flash placed at U2. This chip is long obsolete, and the best way to find them is to try to find NOS chips from online auctions. These may come with bad blocks present, which complicates swapping out chips for repair.

By default, trying other Flash IC's with the same structure and interface does not work, since all CV1000 games does a manufacturer check at startup to make sure that U2 is in fact a K9F1G08U0M, and if another chip is detected, the games goes into an infinite loop and wont start.

This project describes what these checks are, and how to patch them out to allow using other compatible chips.

## TL;DR: How do I patch out these checks

Get the following tools:

- u4patcher.py (this dir)
- compress.py (from U4_Utils)
- compress_data_extract.py (from U4_Utils)
- swap.py (from U4_Utils)

For roms not using compression:

```
> python swap.py u4_dump u4_dump_swapped
> python u4patcher.py u4_dump_swapped
> python swap.py u4_dump_swapped u4_dump
```

For roms using compression:

```
> python swap.py u4_dump u4_dump_swapped
> python compress_data_extract.py u4_dump_swapped compressed_data get
> python compress.py compressed_data decompressed_data d
> python u4patcher.py decompressed_data
> python compress.py decompressed_data compressed_data c
> python compress_data_extract.py u4_dump_swapped compressed_data put
> python swap.py u4_dump_swapped u4_dump
```

## What Flash IC should I use?

Anything with the same structure, pinout and interface of K9F1G08U0M should work.

This means:
- NAND Flash
- TSOP-48 footprint
- 3.3V
- 1 Gbit
- 8 bit parallel interface
- Device = 1024 Blocks
- Block = 64 pages
- Page = 2112 bytes

Timing doesn't seem hugely important since the SH-3 will wait for a few cycles when doing access to U4.

## What does the patch do?

At startup, CV1000 games does the following check for Flash IC's that are compatible:

```
  if ((man_id == 0x98) && (id_code == 0x76)) {
    flash_type = 0;
    num_blocks = 0x1000;
    page_size = 0x210;
    pages_per_block = 0x20;
  }
  if ((man_id == 0x98) && (id_code == 0x79)) {
    flash_type = 1;
    num_blocks = 0x2000;
    page_size = 0x210;
    pages_per_block = 0x20;
  }
  if ((man_id == 0xec) && (id_code == 0xf1)) {  // <- This is K9F1G08U0M
    flash_type = 2;
    num_blocks = 0x400;
    page_size = 0x840;
    pages_per_block = 0x40;
  }
```

The patcher simply replaces the last check (for 0xEC 0xF1) to always return true. U4 contents are compressed for most CV1000 games (not the first few), which means that for those, the data part needs to be decompressed and then compressed back.

## Thanks to
- Enrico Pozzobon: [Initial reverse engineering of U4 compression](https://gitlab.com/-/snippets/2101367), help with Ghidra.
