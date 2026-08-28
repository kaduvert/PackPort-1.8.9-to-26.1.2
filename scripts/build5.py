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
def load_block(n):
    return Image.open(f"{OLD}/blocks/{n}.png").convert("RGBA")

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

def flat_fabric(target_rgb, size, noise=10, seed=42):
    rng = np.random.default_rng(seed)
    base = np.array(target_rgb, dtype=np.float32)
    arr = np.clip(base + rng.integers(-noise,noise+1,(size[1],size[0],3)), 0,255).astype(np.uint8)
    alpha = np.full((size[1],size[0],1), 255, dtype=np.uint8)
    return Image.fromarray(np.dstack([arr,alpha]), "RGBA")

def tile_into(canvas, swatch, box):
    w,h = box[2]-box[0], box[3]-box[1]
    sw,sh = swatch.size
    tiled = Image.new("RGBA",(w,h))
    for yy in range(0,h,sh):
        for xx in range(0,w,sw):
            tiled.paste(swatch,(xx,yy))
    canvas.paste(tiled.crop((0,0,w,h)), (box[0],box[1]))

def build_bed_block_texture(color, head_top, feet_top, planks):
    rgb = DYE_RGB[color]
    ht = retint_fabric(head_top, rgb)
    ft = retint_fabric(feet_top, rgb)
    fabric_sw = flat_fabric(rgb, (8,8))
    canvas = Image.new("RGBA",(64,64),(0,0,0,0))
    canvas.paste(ht.resize((16,16), Image.NEAREST), (6,0))
    tile_into(canvas, planks, (22,0,48,22))
    tile_into(canvas, fabric_sw, (0,16,22,22))
    tile_into(canvas, fabric_sw, (22,22,40,24))
    canvas.paste(ft.resize((16,16), Image.NEAREST), (0,32))
    tile_into(canvas, fabric_sw, (16,24,32,32))
    tile_into(canvas, planks, (24,24,48,56))
    leg_sw = planks.resize((8,8), Image.NEAREST)
    tile_into(canvas, leg_sw, (48,0,64,16))
    tile_into(canvas, leg_sw, (48,16,64,32))
    return canvas

def process_bed():
    head_top = load_block("bed_head_top")
    feet_top = load_block("bed_feet_top")
    planks = load_block("planks_oak")
    item_bed = Image.open(f"{OLD}/items/bed.png").convert("RGBA")

    for color in DYE_RGB:
        # 1) block/entity texture
        block_tex = build_bed_block_texture(color, head_top, feet_top, planks)
        target = f"{OUT}/entity/bed/{color}.png"
        if os.path.isfile(target):
            block_tex.save(target)
            report["matched"].append({
                "category": "entity", "new": f"entity/bed/{color}.png",
                "old_source": "blocks/bed_head_top.png + bed_feet_top.png + planks_oak.png (composited)",
                "method": "reconstructed(bed UV layout inferred + per-color tint)",
                "note": "best-effort UV layout (no old single-file reference existed to verify against, "
                        "unlike chest); pillow/fabric regions confirmed via colour-diffing all 16 modern "
                        "bed files against each other, wood regions use planks_oak.png for a clean tileable look"
            })

        # 2) flat item icon (old 1.8.9 sprite, recoloured), overriding the
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
def fix_chest_layout(im):
    """Swap lid-top pair, base pair, and the latch-bearing strip cell to
    match 26.1.2's chest UV layout. Verified pixel-exact against the real
    old vs new default chest.png (see conversation notes)."""
    im = im.copy()
    def swap_box(a_box, b_box):
        a = im.crop(a_box); b = im.crop(b_box)
        im.paste(b, a_box); im.paste(a, b_box)
    swap_box((14,0,28,14), (28,0,42,14))
    swap_box((14,14,28,19), (42,14,56,19))
    swap_box((14,19,28,33), (28,19,42,33))
    swap_box((14,33,28,43), (42,33,56,43))
    return im

def process_chest():
    for name in ["normal", "trapped", "christmas"]:
        src = f"{OLD}/entity/chest/{name}.png"
        if not os.path.isfile(src):
            continue
        fixed = fix_chest_layout(Image.open(src).convert("RGBA"))
        target = f"{OUT}/entity/chest/{name}.png"
        fixed.save(target)
        for m in report["matched"]:
            if m["new"] == f"entity/chest/{name}.png":
                m["method"] = "exact + UV-relayout fix"
                m["note"] = ("1.8.9's flat chest.png cells don't line up with 26.1.2's chest UV anymore "
                              "(lid-top pair, base pair, and each side-strip's latch cell were relocated) "
                              "- relocated the source pixels to match, verified pixel-exact against the "
                              "actual old-vs-new default texture diff")
    # double-chest halves: crop first, then apply the SAME relative fix to
    # each 64-wide half independently (extrapolated - unlike the single
    # chest, there's no modern reference to diff this against, since 26.1.2
    # never shipped a combined double-chest file to compare with)
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from aliases import CHEST_DOUBLE_SPLITS
    for old_rel, left_rel, right_rel in CHEST_DOUBLE_SPLITS:
        src = f"{OLD}/{old_rel}.png"
        if not os.path.isfile(src):
            continue
        im = Image.open(src).convert("RGBA")
        w, h = im.size
        half = w // 2
        left_img = fix_chest_layout(im.crop((0,0,half,h)))
        right_img = fix_chest_layout(im.crop((half,0,w,h)))
        for half_img, target_rel in [(left_img, left_rel), (right_img, right_rel)]:
            target = f"{OUT}/entity/{target_rel}.png"
            if os.path.isfile(target):
                half_img.save(target)
                for m in report["matched"]:
                    if m["new"] == f"entity/{target_rel}.png":
                        m["note"] = m["note"] + (" | UV-relayout fix also applied per-half (extrapolated "
                                                  "from the single-chest fix - no modern combined-double "
                                                  "reference exists to verify this one independently)")
    print("chest done")

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
    process_chest()
    process_glint()
    with open(f"{ROOT}/report_stage5.json","w") as f:
        json.dump(report, f, indent=2)
    print("stage5 done")
