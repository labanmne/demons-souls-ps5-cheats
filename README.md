# Demon's Souls (PS5) cheat table for KytyPS5 and etaHEN

A cheat table for **Demon's Souls** (the 2020 PS5 remake), **PPSA01341 version 1.07** (`01.007.000`), in the
etaHEN JSON format that the [KytyPS5](https://github.com/chenxiao07/KytyPS5) emulator loads.

Most cheats switch on Bluepoint's own developer switches, which are still in the retail game (no damage,
no death, one-hit kill, no stamina use, freeze everything), only for the player. The rest are small edits
to the code that spends MP, items, durability and souls, or to the burden limits.

## Cheats

| Cheat | What it does |
|---|---|
| God mode (no damage) | You take no damage. Instant-death events (pits, ledge grabs) still kill you. |
| No death (HP never drops below 1) | You take damage, but a lethal hit leaves you at 1 HP. |
| One-hit kill | Your hits deal 999,999 damage, bosses included. |
| Infinite stamina | Attacks, rolls and sprinting cost no stamina. Blocking a hit still does. |
| Infinite MP | Spells and miracles cost no MP. |
| Infinite items and ammo | A stack you use (or pick up, drop or move) refills to its maximum: 99, arrows and bolts 999. |
| Infinite durability | Weapons and armour never wear down. |
| No soul loss on death | You keep your souls when you die. Your bloodstain still appears. |
| Souls x2 / x5 / x10 | More souls per kill. Stacks with the Ring of Avarice. **Turn on only one.** |
| Near-infinite item burden | Max item burden 10000 + 2 × Vitality: pick up everything. Weights are unchanged. |
| No equipment weight limit | Max equip burden 10000 + Endurance: always a fast roll. |
| Freeze enemies | Every character except you stops moving, NPCs and bosses too. Turn it off to talk to NPCs or trigger events. |

**Status (2026-11-19):** all 14 match the 1.07 eboot (`tools/verify_eboot.py`). KytyPS5 applies all of them
together and boots the game with them on, and each one also lands in the right place when it's the only
cheat turned on. They haven't been played through in game yet. If one misbehaves, please open an issue.

Every patch carries enough unchanged neighbouring bytes (8 or more) to occur only once in the eboot.
KytyPS5 finds the game by searching for the first enabled cheat's original bytes, so a bare two-byte
patch such as `75 14` could otherwise land somewhere else when it's used alone.

## Using it with KytyPS5

1. Download [`cheats/PPSA01341_01.007.000.json`](cheats/PPSA01341_01.007.000.json).
2. Save it as `_Patches\PPSA01341.json` in the KytyPS5 folder (the one with `KytyLauncher.exe`); create
   the `_Patches` folder if it isn't there.
3. In the launcher's **Game** page, tick **Cheats**, click **Select...** and tick the cheats you want.
   All of them start off. You can also set `"enabled": true` in the file yourself.
4. Start the game. The log (`logs\*.out.log`) has a `Successfully applied cheat: <name>` line for each one.

Cheats are applied when the game starts, so restart it after changing them. KytyPS5 checks every cheat's
original bytes first: on a different game version it stops with
`cheat file does not match the loaded game` instead of patching the wrong place.

## On a PS5 (etaHEN)

The file is in the same format as the [etaHEN PS5_Cheats](https://github.com/etaHEN/PS5_Cheats) files, so it
should work there like any other JSON cheat, but it hasn't been tried on a console yet. Only use it with
version 1.07 of PPSA01341.

## Check that it matches your game

```
python tools/verify_eboot.py "C:\path\to\the\game\eboot.bin"
```

It reads your `eboot.bin` and compares each cheat's original bytes. "All cheats match" means the table
was made for your exact build. Nothing is written.

## Other versions and regions

Only the EU release (PPSA01341) 1.07 has been checked. The US release (PPSA01342) may well use the same
eboot, but nobody has compared them yet: run `verify_eboot.py` on it first. To port the table to another
version, see [docs/how-it-works.md](docs/how-it-works.md): it lists every function, switch and offset, and
`tools/build_table.py` regenerates the file from an eboot. Pull requests welcome.

## Other Demon's Souls cheats

As of 2026-11-19, these exist for the remake (worth a look if this table doesn't have what you want):

- **Yharnam**: a 9-cheat table for 1.07 in etaHEN's `.mc4` format, for PPSA01340, PPSA01341 and PPSA01342
  (in the [HEN-Cheats-Collection](https://github.com/TeeKay87/HEN-Cheats-Collection)). Its durability, MP and
  souls patches sit in the same functions as this table's, which is a useful cross-check. Two of its
  cheats need its "Master Code" first, which KytyPS5's loader doesn't support as-is.
- **[JShipps/Demons-Souls-PPSA01341-Cheats](https://github.com/JShipps/Demons-Souls-PPSA01341-Cheats)**: a
  2-cheat KytyPS5 file for 1.07 (Untouchable, Infinite Stamina).
- **KytyPS5 discussion [#171](https://github.com/chenxiao07/KytyPS5/discussions/171)**: a 9-cheat KytyPS5 file
  for EU 1.07 ported from 1.05, mostly untested according to its author.
- **Cissa90's Cheat Engine table** for KytyPS5 on
  [FearLess Revolution](https://fearlessrevolution.com/viewtopic.php?t=41223): live memory editing (HP,
  stamina, world tendency, item burden).
- **[sekhnat/des-save-editor](https://github.com/sekhnat/des-save-editor)**: edits save files (souls, stats,
  items, world tendency), so it works with any game version.
- hejran7, Celogamez and Super Death made tables for 1.00 and 1.04; Yharnam's 1.05 table has KytyPS5 ports.

## Notes

- Use cheats offline only.
- No game files are included: the table only holds offsets and a few bytes of original code for checking.

## Credits

- Reverse engineering and table: labanmne, with Claude (Anthropic).
- hejran7's 1.04 cheat file (etaHEN PS5_Cheats) patched the same inventory and durability code, which
  helped confirm those two.
- [KytyPS5](https://github.com/chenxiao07/KytyPS5) by chenxiao07.

Not affiliated with Sony Interactive Entertainment, Bluepoint Games or FromSoftware.

## License

MIT, see [LICENSE](LICENSE).
