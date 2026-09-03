import os, json, shutil
from PIL import Image
import numpy as np

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW_ASSETS = f"{ROOT}/new_pack/assets/minecraft"
OUT_ASSETS = f"{ROOT}/output_pack/assets/minecraft"
OUT = f"{OUT_ASSETS}/textures"

report = json.load(open(f"{ROOT}/report_final.json"))

DYE_RGB = {
    "white": (233,236,236), "orange": (240,118,19), "magenta": (189,68,179),
    "light_blue": (58,175,217), "yellow": (248,198,39), "lime": (112,185,25),
    "pink": (237,141,172), "gray": (62,68,71), "light_gray": (142,142,134),
    "cyan": (21,137,145), "purple": (121,42,172), "blue": (53,57,157),
    "brown": (114,71,40), "green": (84,109,27), "red": (160,39,34), "black": (20,21,25),
}

# ============================================================== BED =======
def retint_fabric(im, target_rgb, g_thresh=75, b_thresh=75):
    arr = np.array(im).astype(np.float32)
    r,g,b,a = arr[...,0],arr[...,1],arr[...,2],arr[...,3]
    is_fabric = (g < g_thresh) & (b < b_thresh) & (r > 60)
    lum = np.clip(r/140.0, 0.25, 1.6)
    t = np.array(target_rgb, dtype=np.float32)
    out = arr.copy()
    for c in range(3):
        newc = np.clip(t[c]*lum, 0, 255)
        out[...,c] = np.where(is_fabric, newc, arr[...,c])
    out[...,3]=a
    return Image.fromarray(out.astype(np.uint8),"RGBA")

def process_bed():
    """Only the flat item icon override survives - the block/entity texture
    composite (16 files, per-colour tinted from bed_head_top/feet_top/
    planks_oak) was tried here originally but its alignment could never be
    verified (bed's 1.8.9 format is six separate files, not a taller
    version of one comparable file the way pig/cow's UV-safety check
    could verify), so it was always going to be reverted later. Not
    generating it at all removes that dead work."""
    item_bed = Image.open(f"{OLD}/items/bed.png").convert("RGBA")

    for color in DYE_RGB:
        # flat item icon (old 1.8.9 sprite, recoloured), overriding the
        # modern 3D-rendered item model with a flat generated icon
        icon = retint_fabric(item_bed, DYE_RGB[color])
        icon_target = f"{OUT}/item/{color}_bed.png"
        os.makedirs(os.path.dirname(icon_target), exist_ok=True)
        icon.save(icon_target)

        model_path = f"{OUT_ASSETS}/models/item/{color}_bed.json"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, "w") as f:
            json.dump({"parent": "minecraft:item/generated",
                       "textures": {"layer0": f"minecraft:item/{color}_bed"}}, f, indent=2)

        item_def_path = f"{OUT_ASSETS}/items/{color}_bed.json"
        with open(item_def_path, "w") as f:
            json.dump({"model": {"type": "minecraft:model", "model": f"minecraft:item/{color}_bed"}}, f, indent=2)

        report["matched"].append({
            "category": "item", "new": f"item/{color}_bed.png (+ model/item override)",
            "old_source": "items/bed.png", "method": "reconstructed(flat icon, item model overridden)",
            "note": "replaced the modern 3D-rendered bed item model with the flat 1.8.9 sprite, recoloured per dye"
        })
    print("bed done")

# ============================================================= CHEST ======

# ============================================================= GLINT ======
def process_glint():
    old = Image.open(f"{OLD}/misc/enchanted_item_glint.png").convert("L")
    old_arr = np.array(old).astype(np.float32)/255.0
    rotated = np.array(old.rotate(90)).astype(np.float32)/255.0
    cross = 1.0 - (1.0-old_arr)*(1.0-rotated)
    cross_tiled = np.tile(cross, (2,2))  # 64x64 -> 128x128

    dark = np.array([39,15,67], dtype=np.float32)
    bright = np.array([157,80,249], dtype=np.float32)
    t = cross_tiled[...,None]
    rgb = dark*(1-t) + bright*t
    alpha = np.full(cross_tiled.shape, 255, dtype=np.uint8)
    out = np.dstack([rgb.astype(np.uint8), alpha])
    result = Image.fromarray(out, mode="RGBA")

    for name in ["enchanted_glint_armor", "enchanted_glint_item"]:
        target = f"{OUT}/misc/{name}.png"
        result.save(target)
        for m in report["matched"]:
            if m["new"] == f"misc/{name}.png":
                m["method"] = "reconstructed(recoloured + crosshatched)"
                m["note"] = ("26.1.2's glint shader multiplies the texture's own RGB directly (confirmed "
                              "from the shipped glint.fsh) - 1.8.9's source is plain greyscale, which is why "
                              "a raw copy rendered whatever colour the engine's ColorModulator happened to "
                              "apply. Rebuilt it colourised with vanilla's actual purple (sampled from this "
                              "pack's own default glint texture) and cross-hatched (rotate+screen-blend a "
                              "copy of the old stripe pattern) since 1.8.9 achieved its crosshatch via two "
                              "separate scrolling draw passes that 26.1.2's single-pass shader doesn't do")
    print("glint done")

if __name__ == "__main__":
    process_bed()
    process_glint()
    with open(f"{ROOT}/report_stage5.json","w") as f:
        json.dump(report, f, indent=2)
    print("stage5 done")
