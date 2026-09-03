import os, sys, shutil, difflib, json
sys.path.insert(0, os.path.dirname(__file__))
from aliases import BLOCK_ALIASES, ITEM_ALIASES, ITEM_NO_EQUIVALENT, BLOCK_NO_EQUIVALENT

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = {"matched": [], "unmatched": [], "special": []}

def list_pngs(root, sub):
    d = os.path.join(root, sub)
    out = {}
    if not os.path.isdir(d):
        return out
    for f in os.listdir(d):
        if f.lower().endswith(".png"):
            out[f[:-4]] = os.path.join(d, f)
    return out

def copy_with_mcmeta(old_png_path, new_png_target_path, note=""):
    """Copy an old texture into the output pack at new_png_target_path,
    syncing companion .mcmeta per the animation-safety rule."""
    os.makedirs(os.path.dirname(new_png_target_path), exist_ok=True)
    shutil.copyfile(old_png_path, new_png_target_path)
    old_meta = old_png_path + ".mcmeta"
    new_meta_target = new_png_target_path + ".mcmeta"
    if os.path.isfile(old_meta):
        shutil.copyfile(old_meta, new_meta_target)
    else:
        # if the modern default had an mcmeta (animated) but our static old
        # source doesn't, drop it so the engine treats it as a static image
        if os.path.isfile(new_meta_target):
            os.remove(new_meta_target)
            note = (note + " | removed modern .mcmeta (old source is static)").strip(" |")
    return note

def process_category(catname, old_sub, new_sub, alias_dict, no_equiv_dict, fuzzy_cutoff=0.84):
    old_files = list_pngs(OLD, old_sub)   # basename(no ext) -> abs path
    new_files = list_pngs(NEW, new_sub)
    used_old = set()
    n_exact = n_alias = n_fuzzy = n_unmatched = 0

    old_names = list(old_files.keys())

    for new_base, new_path in sorted(new_files.items()):
        rel_target = os.path.join(OUT, new_sub, new_base + ".png")
        src = None
        method = None

        if new_base in old_files:
            src = old_files[new_base]; method = "exact"
        else:
            # search alias dict values -> is there an old key mapping to this new_base?
            for old_key, mapped in alias_dict.items():
                if mapped == new_base and old_key in old_files:
                    src = old_files[old_key]; method = f"alias({old_key})"
                    break

        if src is None and new_base not in no_equiv_dict:
            # fuzzy fallback among old names not yet used as an alias target's source
            candidates = difflib.get_close_matches(new_base, old_names, n=1, cutoff=fuzzy_cutoff)
            if candidates:
                src = old_files[candidates[0]]; method = f"fuzzy({candidates[0]})"

        if src:
            note = copy_with_mcmeta(src, rel_target)
            report["matched"].append({
                "category": catname, "new": f"{new_sub}/{new_base}.png",
                "old_source": os.path.relpath(src, OLD), "method": method, "note": note
            })
            used_old.add(src)
            if method == "exact": n_exact += 1
            elif method.startswith("alias"): n_alias += 1
            else: n_fuzzy += 1
        else:
            # output_pack already has this file byte-identical, from the
            # initial copytree of new_pack - nothing to copy, just record why
            reason = no_equiv_dict.get(new_base, "no matching 1.8.9 source found (new content)")
            report["unmatched"].append({
                "category": catname, "new": f"{new_sub}/{new_base}.png", "reason": reason
            })
            n_unmatched += 1

    print(f"[{catname}] new={len(new_files)} exact={n_exact} alias={n_alias} fuzzy={n_fuzzy} unmatched={n_unmatched}")

if __name__ == "__main__":
    # start output pack as a full copy of the new pack (everything not
    # explicitly touched below stays as modern 26.1.2 default)
    if os.path.isdir(f"{ROOT}/output_pack"):
        shutil.rmtree(f"{ROOT}/output_pack")
    shutil.copytree(f"{ROOT}/new_pack", f"{ROOT}/output_pack")

    process_category("block", "blocks", "block", BLOCK_ALIASES, BLOCK_NO_EQUIVALENT, fuzzy_cutoff=0.9)
    process_category("item", "items", "item", ITEM_ALIASES, ITEM_NO_EQUIVALENT, fuzzy_cutoff=0.9)

    with open(f"{ROOT}/report_stage1.json","w") as f:
        json.dump(report, f, indent=2)
    print("done stage1")
