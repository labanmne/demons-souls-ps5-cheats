#!/usr/bin/env python3
"""Check that a cheat file matches your copy of the game before you use it.

Usage:
    python verify_eboot.py <path to eboot.bin> [cheat file]

eboot.bin is the game's executable, in the game folder (fake-signed SELF or plain ELF).
For every cheat, the script compares the cheat's "off" bytes with the bytes at that offset
in your eboot. All OK means the file was made for your exact build. A MISMATCH means a
different version or region: don't use that file with that game.

Nothing is written; the script only reads.
"""
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CHEATS = os.path.join(HERE, '..', 'cheats', 'PPSA01341_01.007.000.json')


def load_image(path):
    """Return {vaddr: bytes} for the loadable segments of a SELF or ELF."""
    d = open(path, 'rb').read()
    magic, = struct.unpack_from('<I', d, 0)
    entries = []
    if magic == 0x1D3D154F:                       # PS4/PS5 SELF
        n, = struct.unpack_from('<H', d, 0x18)
        entries = [struct.unpack_from('<QQQQ', d, 0x20 + i * 0x20) for i in range(n)]
        elf_off = 0x20 + n * 0x20
    elif d[:4] == b'\x7fELF':
        elf_off = 0
    else:
        sys.exit('not a SELF or ELF file: ' + path)
    if d[elf_off:elf_off + 4] != b'\x7fELF':
        sys.exit('no ELF header inside the SELF (encrypted?)')
    phoff, = struct.unpack_from('<Q', d, elf_off + 0x20)
    phentsize, phnum = struct.unpack_from('<HH', d, elf_off + 0x36)
    phdrs = [struct.unpack_from('<IIQQQQQQ', d, elf_off + phoff + i * phentsize) for i in range(phnum)]

    seg_data = {}
    if entries:
        for props, off, fsz, msz in entries:
            if not props & 0x800:
                continue
            if props & 0x2:
                sys.exit('this eboot is encrypted; use a decrypted (fake-signed) dump')
            blob = d[off:off + fsz]
            if props & 0x8:
                blob = zlib.decompress(blob)
            seg_data[(props >> 20) & 0xFFF] = blob
    else:
        for i, p in enumerate(phdrs):
            seg_data[i] = d[p[2]:p[2] + p[5]]

    image = {}
    for i, (ptype, flags, poff, vaddr, paddr, filesz, memsz, align) in enumerate(phdrs):
        if ptype == 1 and i in seg_data:          # PT_LOAD
            image[vaddr] = seg_data[i][:filesz]
    return image


def read(image, va, n):
    for base, data in image.items():
        if base <= va and va + n <= base + len(data):
            return data[va - base: va - base + n]
    return None


def kyty_base(image, memory):
    """Do what KytyPS5's loader does (src/loader/gamePatch.cpp, Matches) for a cheat on its own: search the
    segments for the first write's "off" bytes, take the first hit at which every write's "off" bytes
    match, and return the base it implies. 0 means the cheat lands where it was made for."""
    writes = [(int(m['offset'], 16), bytes.fromhex(m['off'])) for m in memory]
    anchor = next((w for w in writes if any(w[1])), None)
    if anchor is None:
        return None
    for seg_va, data in image.items():
        pos = data.find(anchor[1])
        while pos != -1:
            rva = seg_va + pos
            if anchor[0] >= rva:
                base = anchor[0] - rva
                if all(not any(off) or read(image, va - base, len(off)) == off for va, off in writes):
                    return base
            pos = data.find(anchor[1], pos + 1)
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    image = load_image(sys.argv[1])
    cheats = json.load(open(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CHEATS, encoding='utf-8'))
    print(f'{cheats.get("name")} {cheats.get("id")} {cheats.get("version")}')
    bad = 0
    for mod in cheats['mods']:
        results = []
        for m in mod['memory']:
            va = int(m['offset'], 16)
            want = bytes.fromhex(m['off'])
            have = read(image, va, len(want))
            results.append(have == want)
        ok = all(results)
        alone = kyty_base(image, mod['memory']) == 0     # also lands in the right place when used alone
        ok = ok and alone
        bad += not ok
        print(f'  {"OK      " if ok else "MISMATCH"} {mod["name"]}'
              + ('' if alone or not all(results) else '  (ambiguous on its own: KytyPS5 would patch the wrong place)'))
    print('All cheats match this eboot.' if not bad else f'{bad} cheat(s) do not match this eboot: wrong version or region.')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
