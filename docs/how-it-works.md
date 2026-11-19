# How the cheats work

Notes for anyone porting this table to another version or region, or adding cheats. All addresses are
virtual addresses in `eboot.bin` of **PPSA01341 1.07** (`01.007.000`). The text segment starts at vaddr 0,
so the `offset` in the cheat file is the vaddr (KytyPS5 logs `matched eboot.bin with source base 0x0`).
The eboot is a fake-signed SELF: `tools/unself.py` turns it into a plain ELF (file offset = vaddr + 0x4000
for text and rodata). An x86-64 disassembler such as `objdump -D -b binary -m i386:x86-64` does the rest.

## The developer switches

Bluepoint left its debug tweakables in the retail build. They are registered at startup by name, with a
byte or float in `.data` as storage, for example:

| Name | Storage | Read by gameplay at |
|---|---|---|
| `cp11_characters_playerNoDamage` | `0x27cbd50` | `0x32d689` (damage apply) |
| `cp11_characters_playerNoDead` | `0x27cbc60` | `0x32d7af` (damage apply), and 3 more |
| `cp11_characters_playerExterminate` | `0x27cbb70` | `0x32d588` (damage calc) |
| `cp11_characters_playerNoStaminaConsume` | `0x27cbf30` | `0x331a68` (stamina consume) |
| `cp11_characters_allNoUpdate` | `0x27cc890` | `0x34c855` (character update) |
| `cp11_gameRules_maxItemBurdenBase` (70.0) | `0x2724718` | `0x300f9a`, `0x301049` |
| `cp11_gameRules_maxItemBurdenCoefficient` (2.0) | `0x272471c` | same functions |
| `cp11_gameRules_maxEquipBurdenBase` (29.0) | `0x2724710` | `0x301109`, `0x3011b9` |

Others exist but are not read by gameplay code in 1.07 (only by the debug menu): `playerNoHit`,
`playerNoManaConsume`, `allNoManaConsume`, `allNoArrowConsume`, `allNoAttack`, `allNoMove`, `allNoHit`.
The registration code is at `0x355700`–`0x356360` and `0x305400`–`0x305a40`; each call passes the name
string, the tweakable object (`rdi`) and the storage (`rdx`).

Every gameplay check has the same shape: `lea rax,[flag]; cmp byte [rax],1; jne skip; call [vtbl+0x120]`
(`+0x120` is "is this character the local player"). Turning the `jne` into two NOPs makes the check behave
as if the switch were on, and only for the player, which is how most of the table works.

## Character data

The character instance (`ChrIns`) used by the damage and stamina code:

| Offset | Field |
|---|---|
| `+0x710` | HP |
| `+0x718` | max HP |
| `+0x71c` | MP |
| `+0x720` | max MP |
| `+0x724` | stamina |
| `+0x728` | max stamina |
| `+0x7d8` | debug flags (dword): bit 5 No Dead, bit 6 No Damage, bit 7 No Hit, bit 8 No Attack, bit 9 No Move, bit 10 No Stamina Consume, bit 11 No MP Consume, bit 15 No Update |

`SetHP` is `0x325890`, `SetMP` is `0x3259e0`. The player's game data is `[[0x27e6948]+0x10]`: souls at
`+0x80` (capped at 999,999,999), total souls earned at `+0x88`.

## Each cheat

Addresses below are the patched instruction itself; the cheat file starts each patch a few bytes earlier
so its original bytes are unique.

| Cheat | Where | Original | Patch |
|---|---|---|---|
| God mode | `0x32d693`, damage apply `0x32d630` | `jne` past the playerNoDamage check | NOP |
| No death | `0x32d7a4`, `0x32d7b9` | `je` (debug gate from `0x8469c0`) and `jne` past the playerNoDead check | NOP both; a lethal hit then calls `SetHP(1)` |
| One-hit kill | `0x32d592`, damage calc `0x32d090` | `jne` past the playerExterminate check | NOP; damage becomes the constant 999999.0 when the attacker is the player |
| Infinite stamina | `0x331a72`, stamina consume | `jne` past the playerNoStaminaConsume check | NOP |
| Infinite MP | `0x31640b`, spell cost check | `sub esi,eax` (MP − cost) | `test esi,esi`: MP stays, the `jge` is still taken |
| Infinite items and ammo | `0x43df6b`, inventory quantity change `0x43deb0` | `mov [rdx+8],r13d` (new quantity) | `mov [rdx+8],eax` (`eax` = max stack from `0x43e0f0`: 99, ammo 999) |
| Infinite durability | `0x44471f`, `0x4446cc` | `mov [rdx],edi` / `mov [rsi],ecx` (durability − 1) | NOP |
| No soul loss on death | `0x203593` | `mov [r13+0x80],ecx` (souls = 0) | NOP |
| Souls x2/x5/x10 | `0x3dda40`, soul-rate getter (one caller, the kill reward at `0x37a8b0`) | `vmovss xmm0,[1.0]` | load 2.0 / 5.0 / 10.0 from the game's own read-only constants |
| Item burden | `0x300f9a`, `0x301049` | `vmovss xmm, [maxItemBurdenBase]` | load the read-only 10000.0 at `0x237f008` |
| Equip burden | `0x301109`, `0x3011b9` | `vmovss xmm0, [maxEquipBurdenBase]` | load 10000.0 |
| Freeze enemies | `0x34c85c`, character update | `jne` past the allNoUpdate check | NOP: every non-player character skips its update |

The burden functions also contain Bluepoint's own `GameRule.IsDbgMaxBaseItemWeight` /
`GameRule.IsDbgMaxBaseEquipWeight` switches, which set the base to 1e8. The two unused debug routines at
`0x42f440` and `0x438ca0` set `maxItemBurdenBase` to 10000.

## Porting to another version

1. Unpack the new eboot with `tools/unself.py`.
2. Find each spot again by its surroundings rather than its address: the tweakable names above are plain
   strings, so find the code that references their storage; the burden functions reference the 70.0 / 2.0
   / 29.0 globals; the inventory function has `add r13d,r12d` right after reading the quantity at `+8`;
   the durability store follows `cmp esi,2; cmovge edi,esi; neg ecx; dec edi`.
3. Edit the addresses in `tools/build_table.py` and run it: it reads every `off` value from the eboot
   itself, and widens each patch with unchanged neighbouring bytes until it is at least 8 bytes long and
   occurs only once in the eboot (KytyPS5 anchors on the first enabled cheat's `off` bytes).
4. Check the result with `tools/verify_eboot.py`.

hejran7's cheat file for 1.04 (in the etaHEN PS5_Cheats repository) patched the same inventory and
durability instructions, which helped confirm those two.
