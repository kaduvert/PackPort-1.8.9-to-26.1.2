import os, sys, shutil, difflib, json
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from aliases import ENTITY_ALIASES_LIST, ENTITY_ALIAS_CLAIMED_SOURCES, BABY_RULE_EXCLUDE

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = json.load(open(f"{ROOT}/report_stage1.json"))

def all_pngs(root, sub):
    """dict: relpath-without-ext (posix, relative to sub) -> abs path"""
    base = os.path.join(root, sub)
    out = {}
    for dp, _, files in os.walk(base):
        for f in files:
            if f.lower().endswith(".png"):
                rel = os.path.relpath(os.path.join(dp, f), base).replace(os.sep, "/")
                out[rel[:-4]] = os.path.join(dp, f)
    return out

def copy_with_mcmeta(old_png_path, new_png_target_path):
    os.makedirs(os.path.dirname(new_png_target_path), exist_ok=True)
    shutil.copyfile(old_png_path, new_png_target_path)
    old_meta = old_png_path + ".mcmeta"
    new_meta_target = new_png_target_path + ".mcmeta"
    note = ""
    if os.path.isfile(old_meta):
        shutil.copyfile(old_meta, new_meta_target)
    elif os.path.isfile(new_meta_target):
        os.remove(new_meta_target)
        note = "removed modern .mcmeta (old source is static)"
    return note

# ---------------------------------------------------------------- ENTITY ---
def process_entity():
    old_files = all_pngs(OLD, "entity")
    new_files = all_pngs(NEW, "entity")
    old_by_basename = {}
    for rel, path in old_files.items():
        old_by_basename.setdefault(os.path.basename(rel), []).append(rel)

    used_old = set()
    n_exact = n_alias = n_fuzzy = n_unmatched = 0
    old_rel_list = list(old_files.keys())

    # Chest is handled entirely by a single consolidated fix later (see
    # build12.py's fix_chests): 1.8.9's flat chest.png layout doesn't line
    # up with 26.1.2's chest UV at all, so any naive copy or crop-split
    # done here would just get overwritten/reverted downstream anyway.
    #
    # Mob folders in SKIP_ENTITY_FOLDERS are fully reverted by build11.py
    # (kept only basic classic mobs), so doing any texture work on them here
    # is pure waste. Skipping them entirely means zero writes for 350+ files
    # that would all be thrown away anyway.
    SKIP_ENTITY_FOLDERS = {
        # chest - handled entirely by build12.py
        "chest/normal", "chest/trapped", "chest/christmas", "chest/ender",
        "chest/normal_left", "chest/normal_right",
        "chest/trapped_left", "chest/trapped_right",
        "chest/christmas_left", "chest/christmas_right",
        # mob folders build11.py fully reverts (non-basic mobs)
        "allay", "armadillo", "axolotl", "bear", "bee", "breeze", "camel",
        "copper_golem", "creaking", "dolphin", "enderdragon", "fish", "fox",
        "frog", "goat", "guardian", "hoglin", "horse", "illager", "llama",
        "nautilus", "panda", "parrot", "phantom", "piglin", "rabbit",
        "shulker", "sniffer", "strider", "tadpole", "turtle",
        "wandering_trader", "warden", "wither", "zombie_villager",
    }
    handled_new = {r for r in SKIP_ENTITY_FOLDERS}

    resolved_source_for = {}  # new_rel -> old abs path, filled as we go
    n_rejected_dimension = 0

    # index explicit aliases by their target new_rel for O(1) lookup, and
    # separately note which new_rel values have MULTIPLE alias sources
    # (e.g. chicken -> chicken_temperate/_cold/_warm all from the same old file)
    alias_by_target = {}
    for old_key, new_target in ENTITY_ALIASES_LIST:
        alias_by_target.setdefault(new_target, old_key)

    def dimension_safe(src_path, new_rel):
        """Reject a source whose pixel dimensions aren't identical to, or a
        uniform integer multiple/divisor of, the modern file it would
        replace. A mob's texture is a hand-authored UV-mapped sheet, not a
        tiled block texture - if the canvas size changed non-uniformly
        between versions the internal layout was almost certainly repacked,
        and pasting old pixels in would sample the wrong regions (this is
        exactly what corrupted the bed/pig/cow textures)."""
        orig_new_path = new_files.get(new_rel)
        if not orig_new_path:
            return True
        try:
            sw, sh = Image.open(src_path).size
            nw, nh = Image.open(orig_new_path).size
        except Exception:
            return True
        if (sw, sh) == (nw, nh):
            return True
        if sw == 0 or sh == 0 or nw == 0 or nh == 0:
            return False
        # uniform scale in both axes (e.g. 128x128 old vs 64x64 new is fine;
        # 64x32 old vs 64x64 new is NOT - that's a 1x vs 2x per-axis mismatch)
        rx, ry = sw / nw, sh / nh
        return abs(rx - ry) < 1e-6

    for new_rel, new_path in sorted(new_files.items()):
        if new_rel in handled_new or any(new_rel.startswith(f"{folder}/") or new_rel == folder for folder in handled_new):
            continue
        target = os.path.join(OUT, "entity", new_rel + ".png")
        src = None; method = None

        if new_rel in old_files:
            src = old_files[new_rel]; method = "exact-path"
        elif new_rel in alias_by_target and alias_by_target[new_rel] in old_files:
            old_key = alias_by_target[new_rel]
            src = old_files[old_key]; method = f"alias({old_key})"
        else:
            base = os.path.basename(new_rel)
            cands = [c for c in old_by_basename.get(base, [])
                     if os.path.dirname(c) == "" and c not in ENTITY_ALIAS_CLAIMED_SOURCES]
            if cands:
                src = old_files[cands[0]]; method = f"basename({cands[0]})"

        if src and not dimension_safe(src, new_rel):
            n_rejected_dimension += 1
            report["unmatched"].append({
                "category": "entity", "new": f"entity/{new_rel}.png",
                "reason": f"REJECTED unsafe source {os.path.relpath(src, OLD)} - canvas size changed "
                          f"non-uniformly between versions (old UV layout doesn't fit the new model), "
                          f"left as modern default rather than risk visual corruption"
            })
            src = None; method = None; already_logged_unmatched = True
        else:
            already_logged_unmatched = False

        if src is None and new_rel.endswith("_baby") and new_rel not in BABY_RULE_EXCLUDE:
            # 1.8.9 had no separate baby textures at all for most mobs (baby
            # mobs just reused the adult texture at a smaller model scale),
            # so the correct fill-in for a *_baby file is whatever we
            # resolved for its adult counterpart - but only where the baby
            # slot's own dimensions still match that adult source (checked
            # again below), since several mobs (cat/chicken/pig/rabbit/
            # squid/wolf) actually use a dedicated, differently-laid-out
            # compact baby texture in 26.1.2.
            adult_rel = new_rel[: -len("_baby")]
            candidate_src = resolved_source_for.get(adult_rel)
            if candidate_src is None and adult_rel in new_files:
                if adult_rel in old_files:
                    candidate_src = old_files[adult_rel]
                else:
                    base = os.path.basename(adult_rel)
                    cands = old_by_basename.get(base, [])
                    same_parent = [c for c in cands if os.path.dirname(c) == os.path.dirname(adult_rel)]
                    if same_parent:
                        candidate_src = old_files[same_parent[0]]
            if candidate_src and dimension_safe(candidate_src, new_rel):
                src = candidate_src; method = f"baby-of({adult_rel})"
            elif candidate_src:
                report["unmatched"].append({
                    "category": "entity", "new": f"entity/{new_rel}.png",
                    "reason": f"REJECTED unsafe baby source (26.1.2 uses a dedicated, differently "
                              f"laid-out compact baby texture here, not a scaled-down adult one)"
                })
                n_rejected_dimension += 1
                already_logged_unmatched = True

        # NOTE: no generic string-similarity fallback here on purpose.
        # Entity names collide dangerously ("pillager" ~ "villager",
        # "flow" ~ "flower" banner pattern) even at high cutoffs, and a
        # wrong mob texture is worse than a clean, honestly-reported miss.

        if src:
            resolved_source_for[new_rel] = src
            note = copy_with_mcmeta(src, target)
            report["matched"].append({
                "category": "entity", "new": f"entity/{new_rel}.png",
                "old_source": os.path.relpath(src, OLD), "method": method, "note": note
            })
            used_old.add(src)
            if method == "exact-path": n_exact += 1
            elif method.startswith("alias") or method.startswith("basename"): n_alias += 1
            else: n_fuzzy += 1  # baby-of(...) counted here too
        else:
            if not already_logged_unmatched:
                report["unmatched"].append({
                    "category": "entity", "new": f"entity/{new_rel}.png",
                    "reason": "no matching 1.8.9 source found (new content)"
                })
            n_unmatched += 1

    print(f"[entity] new={len(new_files)} exact={n_exact} alias/basename={n_alias} fuzzy={n_fuzzy} "
          f"unmatched={n_unmatched} rejected_unsafe_dimension={n_rejected_dimension}")

# ----------------------------------------------------- SIMPLE FLAT DIRS ---
def process_flat(catname, sub, alias_map=None, no_equiv=None, fuzzy_cutoff=0.85, skip=None):
    alias_map = alias_map or {}
    no_equiv = no_equiv or {}
    skip = skip or set()
    old_files = all_pngs(OLD, sub)
    new_files = all_pngs(NEW, sub)
    n_exact = n_alias = n_fuzzy = n_unmatched = 0
    old_keys = list(old_files.keys())

    for new_rel, new_path in sorted(new_files.items()):
        if new_rel in skip:
            continue
        target = os.path.join(OUT, sub, new_rel + ".png")
        src = None; method = None
        if new_rel in old_files:
            src = old_files[new_rel]; method = "exact"
        else:
            for old_key, mapped in alias_map.items():
                if mapped == new_rel and old_key in old_files:
                    src = old_files[old_key]; method = f"alias({old_key})"
                    break
        if src is None and new_rel not in no_equiv:
            candidates = difflib.get_close_matches(new_rel, old_keys, n=1, cutoff=fuzzy_cutoff)
            if candidates:
                src = old_files[candidates[0]]; method = f"fuzzy({candidates[0]})"
        if src:
            note = copy_with_mcmeta(src, target)
            report["matched"].append({"category": catname, "new": f"{sub}/{new_rel}.png",
                                       "old_source": os.path.relpath(src, OLD), "method": method, "note": note})
            if method == "exact": n_exact += 1
            elif method.startswith("alias"): n_alias += 1
            else: n_fuzzy += 1
        else:
            reason = no_equiv.get(new_rel, "no matching 1.8.9 source found (new content)")
            report["unmatched"].append({"category": catname, "new": f"{sub}/{new_rel}.png", "reason": reason})
            n_unmatched += 1
    print(f"[{catname}] new={len(new_files)} exact={n_exact} alias={n_alias} fuzzy={n_fuzzy} unmatched={n_unmatched}")

# ------------------------------------------------------------------ MISC --
def process_misc():
    """misc/ has a couple of 1-old -> 2-new duplications (glint split)."""
    old_files = all_pngs(OLD, "misc")
    new_files = all_pngs(NEW, "misc")
    dup_map = {
        "enchanted_glint_armor": "enchanted_item_glint",
        "enchanted_glint_item": "enchanted_item_glint",
    }
    handled = set()
    for new_rel, old_key in dup_map.items():
        if new_rel in new_files and old_key in old_files:
            target = os.path.join(OUT, "misc", new_rel + ".png")
            note = copy_with_mcmeta(old_files[old_key], target)
            report["matched"].append({"category": "misc", "new": f"misc/{new_rel}.png",
                                       "old_source": f"misc/{old_key}.png", "method": "alias(split-reuse)",
                                       "note": (note + " | shared source used for both the armor and item glint variants").strip(" |")})
            handled.add(new_rel)
    no_equiv = {
        "nausea": "new post-processing effect, no 1.8.9 source",
        "powder_snow_outline": "new (Caves & Cliffs) effect, no 1.8.9 source",
        "spyglass_scope": "new (spyglass item) effect, no 1.8.9 source",
        "credits_vignette": "reuses vignette.png conceptually but is a distinct modern credits-screen asset; left as default to avoid guessing intent",
    }
    process_flat("misc", "misc", alias_map={}, no_equiv=no_equiv, skip=handled)

# ------------------------------------------------------------ ENVIRONMENT -
def process_environment():
    old_files = all_pngs(OLD, "environment")
    new_files = all_pngs(NEW, "environment")
    # moon phase slicing: 128x64 grid, 4 cols x 2 rows of 32x32, row-major index 0-7
    moon_order = ["full_moon","waning_gibbous","third_quarter","waning_crescent",
                  "new_moon","waxing_crescent","first_quarter","waxing_gibbous"]
    handled = set()
    moon_src = old_files.get("moon_phases")
    if moon_src:
        im = Image.open(moon_src).convert("RGBA")
        for i, name in enumerate(moon_order):
            col, row = i % 4, i // 4
            crop = im.crop((col*32, row*32, col*32+32, row*32+32))
            target_rel = f"celestial/moon/{name}"
            if target_rel in new_files:
                target = os.path.join(OUT, "environment", target_rel + ".png")
                os.makedirs(os.path.dirname(target), exist_ok=True)
                crop.save(target)
                report["matched"].append({"category": "environment", "new": f"environment/{target_rel}.png",
                                           "old_source": "environment/moon_phases.png", "method": "split-crop(moon phase grid)",
                                           "note": f"cropped cell col={col} row={row} from the old 4x2 moon phase atlas"})
                handled.add(target_rel)
    alias_map = {"sun": "celestial/sun"}
    no_equiv = {"celestial/end_flash": "new effect, no 1.8.9 source"}
    process_flat("environment", "environment", alias_map=alias_map, no_equiv=no_equiv, skip=handled)

if __name__ == "__main__":
    process_entity()
    process_environment()
    process_misc()
    process_flat("colormap", "colormap", no_equiv={"dry_foliage": "new biome-feature colormap, no 1.8.9 source"})
    process_flat("effect", "effect")

    with open(f"{ROOT}/report_stage2.json", "w") as f:
        json.dump(report, f, indent=2)
    print("done stage2")
