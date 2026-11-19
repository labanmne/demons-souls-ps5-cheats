"""Build the etaHEN/KytyPS5 cheat JSON for Demon's Souls (PPSA01341 1.07) from the unpacked eboot.
Each patch's "off" bytes are read from the game binary itself, so they are exact.
Usage:
    python unself.py eboot.bin eboot.elf
    python build_table.py eboot.elf ../cheats/PPSA01341_01.007.000.json
See docs/how-it-works.md for what each patch does."""
import json, struct, sys

elf = open(sys.argv[1], 'rb').read()
FILE_DELTA = 0x4000          # file offset = vaddr + 0x4000 for the text and rodata segments


def orig(va, n):
    return elf[va + FILE_DELTA: va + FILE_DELTA + n]


def nop_patch(va, n):
    return (va, orig(va, n), b'\x90' * n)


def bytes_patch(va, new):
    return (va, orig(va, len(new)), bytes(new))


def repoint_load(va, target):
    """An 8-byte 'vmovss xmmN, [rip+disp32]' at va: make it load from target instead."""
    o = orig(va, 8)
    assert o[:3] == b'\xc5\xfa\x10' and (o[3] & 0xC7) == 0x05, (hex(va), o.hex())
    disp = target - (va + 8)
    return (va, o, o[:4] + struct.pack('<i', disp))


def f32(va):
    return struct.unpack('<f', elf[va + FILE_DELTA: va + FILE_DELTA + 4])[0]


# read-only float constants already in the game's literal pool (.rodata)
C10000, C2, C5, C10 = 0x237f008, 0x237e6ac, 0x237ead8, 0x237e12c
assert (f32(C10000), f32(C2), f32(C5), f32(C10)) == (10000.0, 2.0, 5.0, 10.0)

MODS = [
    ("God mode (no damage)",
     "You take no damage from anything that goes through the damage code (hits, spells, falls that hurt). "
     "Forces the game's own debug switch cp11_characters_playerNoDamage on. Instant-death events (falling into "
     "a pit, being grabbed off a ledge) still kill you.",
     [nop_patch(0x32D693, 2)]),
    ("No death (HP never drops below 1)",
     "You still take damage, but a hit that would kill you leaves you at 1 HP. Forces the game's own "
     "cp11_characters_playerNoDead switch (and the debug gate in front of it) on. Pits still kill.",
     [nop_patch(0x32D7A4, 2), nop_patch(0x32D7B9, 2)]),
    ("One-hit kill",
     "Every hit you land deals 999,999 damage (bosses included). Forces the game's own "
     "cp11_characters_playerExterminate switch on.",
     [nop_patch(0x32D592, 2)]),
    ("Infinite stamina",
     "Attacks, rolls, sprinting and other actions cost no stamina. Forces the game's own "
     "cp11_characters_playerNoStaminaConsume switch on. Blocking a hit still drains stamina.",
     [nop_patch(0x331A72, 2)]),
    ("Infinite MP",
     "Spells and miracles cost no MP. The spell-cost check keeps your MP as it is instead of subtracting "
     "the cost.",
     [bytes_patch(0x31640B, b'\x85\xf6')]),          # sub esi,eax -> test esi,esi
    ("Infinite items and ammo (stacks refill to max when used)",
     "Whenever a stack in your inventory changes (you use, pick up, drop or move an item, or fire an arrow "
     "or bolt), it is set to its maximum (99, ammo 999). Same idea as hejran7's 'Max Items' cheat for 1.04.",
     [bytes_patch(0x43DF6B, b'\x89\x42\x08\x90')]),  # mov [rdx+8],r13d -> mov [rdx+8],eax (eax = max stack)
    ("Infinite durability",
     "Weapons and armour never lose durability.",
     [nop_patch(0x44471F, 2), nop_patch(0x4446CC, 2)]),
    ("No soul loss on death",
     "You keep your souls when you die. Your bloodstain still appears, so picking it up adds those souls "
     "again.",
     [nop_patch(0x203593, 7)]),
    ("Souls x2",
     "Souls from kills are doubled (stacks with the Ring of Avarice and similar effects). Enable only one "
     "souls multiplier.",
     [repoint_load(0x3DDA40, C2)]),
    ("Souls x5",
     "Souls from kills x5. Enable only one souls multiplier.",
     [repoint_load(0x3DDA40, C5)]),
    ("Souls x10",
     "Souls from kills x10. Enable only one souls multiplier.",
     [repoint_load(0x3DDA40, C10)]),
    ("Near-infinite item burden",
     "Max item burden becomes 10000 + 2 x Vitality instead of 70 + 2 x Vitality, so you can pick up "
     "everything. Item weights are unchanged.",
     [repoint_load(0x300F9A, C10000), repoint_load(0x301049, C10000)]),
    ("No equipment weight limit",
     "Max equip burden becomes 10000 + Endurance instead of 29 + Endurance: you always fast-roll, whatever "
     "you wear. Equipment weights are unchanged.",
     [repoint_load(0x301109, C10000), repoint_load(0x3011B9, C10000)]),
    ("Freeze enemies",
     "Every character except you stops updating: enemies, bosses and NPCs freeze in place. Forces the "
     "game's own cp11_characters_allNoUpdate switch on, minus the player. Turn it off to talk to NPCs or "
     "progress scripted events.",
     [nop_patch(0x34C85C, 2)]),
]

out = {
    "name": "Demon's Souls",
    "id": "PPSA01341",
    "version": "01.007.000",
    "process": "eboot.bin",
    "mods": [],
    "credits": ["labanmne", "Claude (Anthropic)"],
}
def unique_window(va, off, on):
    """Widen a patch with unchanged neighbouring bytes until its "off" bytes occur only once in the whole
    eboot. KytyPS5 finds the game by searching for the first enabled cheat's "off" bytes, so a short
    pattern such as 75 14 could otherwise match (and patch) the wrong place when one cheat is used alone."""
    for pre in range(max(0, 8 - len(off)), 49):          # at least 8 bytes, and unique
        start = va - pre
        window = elf[start + FILE_DELTA: start + FILE_DELTA + pre + len(off)]
        first = elf.find(window)
        if elf.find(window, first + 1) == -1:
            return start, window, window[:pre] + on
    raise SystemExit(f'no unique window for {va:#x}')


for name, desc, patches in MODS:
    mem = []
    for va, off, on in patches:
        assert off != on and len(off) == len(on), (name, hex(va))
        start, woff, won = unique_window(va, off, on)
        mem.append({"offset": f"{start:X}", "on": won.hex().upper(), "off": woff.hex().upper()})
    out["mods"].append({"name": name, "description": desc, "type": "checkbox", "enabled": False, "memory": mem})

json.dump(out, open(sys.argv[2], 'w', encoding='utf-8', newline='\n'), indent=2, ensure_ascii=False)
open(sys.argv[2], 'a', newline='\n').write('\n')
for m in out["mods"]:
    print(f'{m["name"]}: ' + '; '.join(f'{x["offset"]} {x["off"]}->{x["on"]}' for x in m["memory"]))
