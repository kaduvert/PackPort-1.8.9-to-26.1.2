import os, json, shutil

ROOT = "/home/claude/work"
OUT_ASSETS = f"{ROOT}/output_pack/assets/minecraft"

report = json.load(open(f"{ROOT}/report_stage11.json"))

# --------------------------------------------------- STRIP UNMATCHED TEXTURES
# Authority is the report, NOT a byte-diff against new_pack - many correct
# 1.8.9 matches are *intentionally* byte-identical to the modern default
# (e.g. glowstone.png never changed), and those must stay. Only files we
# explicitly logged as having no 1.8.9 source get removed.
#
# Safety: a handful of files (bed, chest, glint) got a fresh "matched" entry
# appended in stage5 AFTER an earlier stage had already logged them as
# "unmatched" - the stale unmatched entry is still sitting in the list. Never
# strip a path that also appears in matched, regardless of ordering.
matched_paths = set(m["new"] for m in report["matched"])
strip_paths = set(m["new"] for m in report["unmatched"]) - matched_paths

removed_textures = 0
for rel in strip_paths:
    path = f"{OUT_ASSETS}/textures/{rel}"
    if os.path.isfile(path):
        os.remove(path)
        removed_textures += 1
        meta = path + ".mcmeta"
        if os.path.isfile(meta):
            os.remove(meta)
print(f"removed {removed_textures} unmatched texture files ({len(matched_paths & set(m['new'] for m in report['unmatched']))} rescued from stale double-logging)")

# ---------------------------------------- STRIP ALL UNMODIFIED NON-TEXTURE DATA
# None of these ever had a 1.8.9 counterpart in this format (the .mcmeta-era
# pack format had no items/models/blockstates/equipment/shaders/atlases/
# waypoint_style component system at all) - so under the same rule as
# textures, "no 1.8.9 equivalent could possibly be used" means these get
# removed too UNLESS we explicitly authored/modified something in them
# (currently: the bed item-model override).
KEEP_EXPLICIT = set()
for color in ["white","orange","magenta","light_blue","yellow","lime","pink","gray",
              "light_gray","cyan","purple","blue","brown","green","red","black"]:
    KEEP_EXPLICIT.add(f"models/item/{color}_bed.json")
    KEEP_EXPLICIT.add(f"items/{color}_bed.json")

STRIP_DIRS = ["atlases","blockstates","equipment","font","items","lang","models",
              "particles","post_effect","shaders","texts","waypoint_style"]

removed_other = 0
for d in STRIP_DIRS:
    base = f"{OUT_ASSETS}/{d}"
    if not os.path.isdir(base):
        continue
    for dirpath, dirs, files in os.walk(base, topdown=False):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, OUT_ASSETS).replace(os.sep, "/")
            if rel in KEEP_EXPLICIT:
                continue
            os.remove(full)
            removed_other += 1
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
print(f"removed {removed_other} unmodified non-texture files across {STRIP_DIRS}")

# sanity: confirm the bed overrides survived
for color in ["red", "white"]:
    assert os.path.isfile(f"{OUT_ASSETS}/models/item/{color}_bed.json")
    assert os.path.isfile(f"{OUT_ASSETS}/items/{color}_bed.json")
print("bed model overrides confirmed present")

# confirm shaders/ is fully gone (this is what fixes the Sodium conflict)
assert not os.path.isdir(f"{OUT_ASSETS}/shaders"), "shaders dir should be fully removed"
print("shaders/ directory confirmed removed - resolves the Sodium terrain-shader conflict")

with open(f"{ROOT}/report_final2.json", "w") as f:
    json.dump(report, f, indent=2)
print("stage6 done")
