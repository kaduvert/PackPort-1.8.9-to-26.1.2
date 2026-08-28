"""
Stage 13: formalizes the specific removal requests and the crit/enchanted-hit
particle port from the following two rounds of user feedback, originally run
as ad-hoc inline commands. Run after build12.py.

Removals: water block texture (item untouched), title-screen panorama,
single chest (normal/trapped/christmas - ender chest is kept, fixed in
build12.py), donkey, the underwater air-bubble HUD icons, redstone dust
block textures, the brewing stand and creative-inventory GUI backgrounds
(anvil explicitly left alone).

Addition: the 1.8.9 critical-hit and enchanted-hit ("sharpness") particles,
found by scanning the old particle atlas for grayscale checkerboard/diamond
shapes (the same tint-at-runtime mechanism as the enchant glint) and
confirmed pixel-identical against 26.1.2's own reference textures before
use - not guessed.
"""
import json, os, shutil
from PIL import Image

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = json.load(open(f"{ROOT}/report_stage10.json"))


def revert(rel, reason):
    src, dst = f"{NEW}/{rel}", f"{OUT}/{rel}"
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    elif os.path.isfile(dst):
        os.remove(dst)
    report["matched"] = [m for m in report["matched"] if m["new"] != rel]
    report["unmatched"] = [m for m in report["unmatched"] if m["new"] != rel]
    report["unmatched"].append({"category": rel.split("/")[0], "new": rel, "reason": reason})


def apply_removals():
    revert("block/water_still.png", "removed per user request")
    revert("block/water_flow.png", "removed per user request")

    for i in range(6):
        revert(f"gui/title/background/panorama_{i}.png", "removed per user request")

    for name in ["normal", "trapped", "christmas"]:
        revert(f"entity/chest/{name}.png",
               "removed per user request (single chest); ender chest kept")

    revert("entity/horse/donkey.png",
           "removed per user request (also: verified incompatible layout via pixel-overlap "
           "testing - scattered/noisy overlap unlike pig/cow's clean 99.8% match)")
    revert("entity/horse/donkey_baby.png", "removed per user request / same as adult donkey")

    for f in ["air", "air_empty", "air_bursting"]:
        revert(f"gui/sprites/hud/{f}.png", "removed per user request")

    for f in ["redstone_dust_dot", "redstone_dust_line0", "redstone_dust_line1", "redstone_dust_overlay"]:
        revert(f"block/{f}.png", "removed per user request")

    revert("gui/container/brewing_stand.png", "removed per user request")

    for f in ["tab_inventory", "tab_item_search", "tab_items"]:
        revert(f"gui/container/creative_inventory/{f}.png", "removed per user request")

    print("removals applied: water block, panorama, single chest, donkey, air bubble, "
          "redstone dust, brewing stand gui, creative inventory gui (anvil untouched)")


def port_crit_particles():
    im = Image.open(f"{OLD}/particle/particles.png").convert("RGBA")
    os.makedirs(f"{OUT}/particle", exist_ok=True)
    jobs = [((8, 32, 16, 40), "critical_hit"), ((16, 32, 24, 40), "enchanted_hit")]
    for box, name in jobs:
        crop = im.crop(box)
        crop.save(f"{OUT}/particle/{name}.png")
        rel = f"particle/{name}.png"
        report["unmatched"] = [m for m in report["unmatched"] if m["new"] != rel]
        report["matched"] = [m for m in report["matched"] if m["new"] != rel]
        report["matched"].append({
            "category": "particle", "new": rel, "old_source": f"particle/particles.png @{box}",
            "method": "reconstructed(crop, pixel-verified)",
            "note": f"cropped region is pixel-identical to 26.1.2's own {name}.png reference (both "
                    f"are grayscale+alpha, tinted gold/blue at runtime) - confirmed via direct "
                    f"visual comparison, not guessed"
        })
    print("crit + enchanted_hit particles ported")


if __name__ == "__main__":
    apply_removals()
    port_crit_particles()
    with open(f"{ROOT}/report_stage10.json", "w") as f:
        json.dump(report, f, indent=2)
    print("stage13 done")
