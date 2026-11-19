"""Unpack a fake-signed PS4/PS5 SELF (eboot.bin) into a plain ELF, and print its program headers."""
import struct, sys, zlib

src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
magic, = struct.unpack_from('<I', d, 0)
assert magic == 0x1D3D154F, hex(magic)
n_entries, = struct.unpack_from('<H', d, 0x18)
entries = [struct.unpack_from('<QQQQ', d, 0x20 + i * 0x20) for i in range(n_entries)]
elf_off = 0x20 + n_entries * 0x20
assert d[elf_off:elf_off + 4] == b'\x7fELF'

e_type, = struct.unpack_from('<H', d, elf_off + 0x10)
e_phoff, = struct.unpack_from('<Q', d, elf_off + 0x20)
e_phentsize, e_phnum = struct.unpack_from('<HH', d, elf_off + 0x36)
phdrs = [struct.unpack_from('<IIQQQQQQ', d, elf_off + e_phoff + i * e_phentsize) for i in range(e_phnum)]

size = max(p[2] + p[5] for p in phdrs)  # p_offset + p_filesz
out = bytearray(max(size, e_phoff + e_phnum * e_phentsize))
hdr_len = e_phoff + e_phnum * e_phentsize
out[0:hdr_len] = d[elf_off:elf_off + hdr_len]

for props, off, fsz, msz in entries:
    if not props & 0x800:          # only entries that carry segment data
        continue
    idx = (props >> 20) & 0xFFF
    blob = d[off:off + fsz]
    if props & 0x2:
        sys.exit(f'segment {idx} is encrypted; not a fake-signed SELF')
    if props & 0x8:
        blob = zlib.decompress(blob)
    p = phdrs[idx]
    out[p[2]:p[2] + len(blob)] = blob

open(dst, 'wb').write(out)
print(f'e_type={e_type:#x} phnum={e_phnum} -> {dst} ({len(out)} bytes)')
for i, (pt, fl, po, va, pa, fs, ms, al) in enumerate(phdrs):
    print(f'  [{i:2}] type={pt:#010x} flags={fl:#x} off={po:#010x} vaddr={va:#012x} filesz={fs:#010x} memsz={ms:#010x}')
