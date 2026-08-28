import os, json
from PIL import Image
import numpy as np

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT_ASSETS = f"{ROOT}/output_pack/assets/minecraft"
OUT = f"{OUT_ASSETS}/textures"

report = json.load(open(f"{ROOT}/report_stage7.json"))

# ------------------------------------------------------------- BAD OMEN ---
def process_bad_omen():
    bottle = Image.open(f"{NEW}/item/potion.png").convert("RGBA")
    overlay = Image.open(f"{NEW}/item/potion_overlay.png").convert("RGBA")

    arr = np.array(overlay).astype(np.float32)
    lum = (0.3*arr[...,0]+0.59*arr[...,1]+0.11*arr[...,2])/255.0
    black = np.array([12,10,14], dtype=np.float32)
    out = np.zeros_like(arr)
    for c in range(3):
        out[...,c] = black[c]*np.clip(lum*1.3,0.25,1.0)
    out[...,3] = arr[...,3]
    tinted = Image.fromarray(out.astype(np.uint8),"RGBA")

    canvas = Image.new("RGBA", bottle.size, (0,0,0,0))
    canvas = Image.alpha_composite(canvas, tinted)
    canvas = Image.alpha_composite(canvas, bottle)

    ov = np.array(overlay)
    opaque_ys, opaque_xs = np.where(ov[...,3] > 40)
    cx = int(opaque_xs.mean())
    top_y = int(opaque_ys.min()) + 2
    for dx in (-2, 1):
        x, y = cx+dx, top_y
        if 0 <= x < canvas.width and 0 <= y < canvas.height:
            canvas.putpixel((x,y), (214,20,20,255))

    target = f"{OUT}/item/ominous_bottle.png"
    canvas.save(target)
    report["matched"].append({
        "category": "item", "new": "item/ominous_bottle.png",
        "old_source": "item/potion.png + item/potion_overlay.png (composited, not a real 1.8.9 item)",
        "method": "reconstructed(redesigned shape, kept black/red-eyes design)",
        "note": "Bad Omen didn't exist in 1.8.9 so there's no source to port - per your request, rebuilt "
                "using the standard potion bottle silhouette instead of 26.1.2's custom angular flask "
                "shape, keeping the black liquid + red eye-dots design"
    })
    print("bad omen done")

# ------------------------------------------------ STRAY TOP-LEVEL FILES ---
def strip_stray_files():
    removed = []
    for f in os.listdir(OUT_ASSETS):
        full = os.path.join(OUT_ASSETS, f)
        if os.path.isfile(full) and f not in ("pack.mcmeta",):
            os.remove(full)
            removed.append(f)
    print("removed stray top-level files:", removed)

if __name__ == "__main__":
    process_bad_omen()
    strip_stray_files()
    with open(f"{ROOT}/report_stage8.json", "w") as f:
        json.dump(report, f, indent=2)
    print("stage8 done")
