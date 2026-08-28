# 1.8.9 → 26.1.2 Texture Pack Conversion

## Run order

Extract the two uploaded zips to `old_pack/` and `new_pack/`, then:

1. **build.py** — Blocks and items: exact-name matches, the curated
   BLOCK_ALIASES/ITEM_ALIASES rename dictionaries, conservative fuzzy
   fallback.
2. **build2.py** — Entities, environment, colormap, misc, effect. The
   alias-priority matcher with the basename-collision guard, the `_baby`
   reuse rule, and the dimension/aspect-ratio safety check.
3. **build3.py** — GUI container backgrounds and the HUD sprite
   reconstruction (hearts/food/armor/xp bar/hotbar) from the legacy
   `icons.png`/`widgets.png` atlases.
4. **build4.py** — Slices the old `clock.png`/`compass.png` animation
   strips into 26.1.2's individual frame files.
5. **build5.py** — Bed item-icon override, initial chest/glint work
   (superseded/corrected by build12.py below).
6. **build7.py** — Paintings: atlas region detection + placement.
7. **build8.py** — Bad Omen bottle redesign, stray top-level file cleanup.
8. **build9.py** — Full-tree audit: every 26.1.2 texture file the earlier
   stages never touched gets explicitly matched or explicitly marked
   unmatched with a categorized reason, so nothing survives silently
   unaccounted for.
9. **build10.py** — The pad-and-composite fix for pig/cow/mooshroom,
   verified via pixel-overlap testing before being applied.
10. **build12.py** *(new)* — Formalizes the "chase perfection" review round:
    the ender-chest fix build5 missed, reverting the double-chest
    experiment that corrupted alpha, explicit chest seam colour-matching,
    the armor_full/armor_empty swap correction, porting the 12 armor-layer
    textures (`textures/models/armor/` → `entity/equipment/`, a whole path
    the original sweep never processed), reverting bed's block texture
    after its alignment couldn't be verified, 7 more exact-match fixes
    found by manually auditing every unused 1.8.9 file, the 4
    empty-armor-slot icons, and the pack icon/description.
11. **build13.py** *(new)* — Formalizes the specific removal requests
    (water block, title panorama, single chest, donkey, underwater air
    bubble, redstone dust, brewing stand + creative inventory GUI) and
    the crit/enchanted-hit particle port.
12. **build11.py** — The broad mob-simplification pass: keeps only
    zombie/enderman/chicken/sheep/pig/cow/creeper/skeleton/spider/squid/
    slime/ghast/blaze/silverfish/endermite/bat/snow_golem/iron_golem/witch
    plus base wolf/villager/ocelot, reverting 35 other mob folders (horse,
    rabbit, guardian, wither, all the newer mobs, etc.) to modern default.
    Runs *after* build12/13 despite the filename - see note below.
13. **build6.py** — Final pass: strips every texture logged as unmatched
    (the report is the authority, never a byte-diff - genuine 1.8.9
    content that happens to be byte-identical to the modern default is
    never removed) plus every unmodified non-texture asset category
    (shaders, models, blockstates, lang, items, equipment, atlases,
    particle definitions, fonts, post-effects, waypoint styles).

**Note on numbering:** build11.py was written before build12/13 existed,
back when it was the newest addition - the filename reflects when it was
*written*, not when it *runs*. Actual execution order is build9, 10, 12,
13, 11, 6, as listed above.

`aliases.py` holds every rename dictionary and alias list build.py/build2.py
depend on.
