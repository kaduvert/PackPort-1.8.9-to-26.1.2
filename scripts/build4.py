import json
from PIL import Image

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = json.load(open(f"{ROOT}/report_stage3.json"))
unmatched = report["unmatched"]

def slice_strip(name, frame_count, target_prefix):
    im = Image.open(f"{OLD}/items/{name}.png").convert("RGBA")
    w, h = im.size
    fh = h // frame_count
    assert fh == w, f"{name}: expected square frames, got {w}x{fh}"
    done = 0
    for i in range(frame_count):
        frame = im.crop((0, i*fh, w, i*fh+fh))
        target = f"{OUT}/item/{target_prefix}_{i:02d}.png"
        frame.save(target)
        report["matched"].append({
            "category": "item", "new": f"item/{target_prefix}_{i:02d}.png",
            "old_source": f"items/{name}.png", "method": "split-crop(animation frame)",
            "note": f"frame {i} of {frame_count}, cropped from the old {w}x{h} vertical strip"
        })
        done += 1
    return done

n1 = slice_strip("clock", 64, "clock")
n2 = slice_strip("compass", 32, "compass")
print(f"clock frames: {n1}, compass frames: {n2}")

# remove their old 'unmatched' entries (they were logged before this stage ran)
report["unmatched"] = [m for m in unmatched
                        if not (m["category"] == "item" and
                                (m["new"].split("/")[-1].startswith("clock_") or
                                 m["new"].split("/")[-1].startswith("compass_")))]

# recovery_compass has no 1.8.9 source (item added 1.19); leave modern default,
# already copied as part of the initial full-pack seed, just document it
for i in range(32):
    name = f"item/recovery_compass_{i:02d}.png"
    if not any(m["new"] == name for m in report["unmatched"]):
        report["unmatched"].append({"category": "item", "new": name,
                                     "reason": "Recovery Compass is a 1.19+ item, no 1.8.9 source"})

with open(f"{ROOT}/report_final.json", "w") as f:
    json.dump(report, f, indent=2)
print("stage4 done")
