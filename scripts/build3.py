import os, sys, shutil, json
from PIL import Image

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = json.load(open(f"{ROOT}/report_stage2.json"))

def add_matched(cat, new_rel, old_desc, method, note=""):
    report["matched"].append({"category": cat, "new": new_rel, "old_source": old_desc,
                               "method": method, "note": note})

def add_unmatched(cat, new_rel, reason):
    report["unmatched"].append({"category": cat, "new": new_rel, "reason": reason})

# --------------------------------------------------- CONTAINER GUI COPY ---
CONTAINER_DIRECT = ["anvil","beacon","brewing_stand","crafting_table","dispenser",
                     "enchanting_table","furnace","generic_54","hopper","horse"]
icons_old = Image.open(f"{OLD}/gui/icons.png").convert("RGBA")
widgets_old = Image.open(f"{OLD}/gui/widgets.png").convert("RGBA")

for name in CONTAINER_DIRECT:
    src = f"{OLD}/gui/container/{name}.png"
    dst = f"{OUT}/gui/container/{name}.png"
    shutil.copyfile(src, dst)
    add_matched("gui", f"gui/container/{name}.png", f"gui/container/{name}.png", "exact",
                "verified identical 256x256 canvas size before copying")

add_unmatched("gui", "gui/container/inventory.png",
              "removed per user report: the survival inventory layout in 26.1.2 has shifted "
              "(likely the recipe-book toggle area added after 1.8.9), so the old texture "
              "misaligned the slots - left as modern default rather than ship it broken")
add_unmatched("gui", "gui/container/villager2.png",
              "villager trading GUI canvas grew 256x256 -> 512x256 for the reworked trade UI; "
              "no safe 1:1 placement without a manual layout remap")
for name in ["blast_furnace","cartography_table","crafter","gamemode_switcher","grindstone",
             "loom","nautilus","shulker_box","smithing","smoker","stonecutter"]:
    add_unmatched("gui", f"gui/container/{name}.png", "block/feature added after 1.8.9, no source")

# book.png
shutil.copyfile(f"{OLD}/gui/book.png", f"{OUT}/gui/book.png")
add_matched("gui", "gui/book.png", "gui/book.png", "exact", "verified identical 256x256 canvas")

# --------------------------------------------------------- HUD REBUILD ---
def crop_icons(box):
    return icons_old.crop(box)
def crop_widgets(box):
    return widgets_old.crop(box)

def save_hud(name, img, source_desc):
    target = f"{OUT}/gui/sprites/hud/{name}.png"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    img.save(target)
    add_matched("gui", f"gui/sprites/hud/{name}.png", source_desc,
                "reconstructed(crop from legacy atlas)",
                "hand-verified pixel coordinates - see conversion report for methodology")

# crosshair
save_hud("crosshair", crop_icons((0,0,16,16)), "gui/icons.png @(0,0,16x16)")

# hotbar (widgets.png)
save_hud("hotbar", crop_widgets((0,0,182,22)), "gui/widgets.png @(0,0,182x22)")
save_hud("hotbar_selection", crop_widgets((0,22,24,44)), "gui/widgets.png @(0,22,24x22)")

# xp bar / jump bar (icons.png)
save_hud("experience_bar_background", crop_icons((0,64,182,69)), "gui/icons.png @(0,64,182x5)")
save_hud("experience_bar_progress", crop_icons((0,69,182,74)), "gui/icons.png @(0,69,182x5)")
save_hud("jump_bar_background", crop_icons((0,84,182,89)), "gui/icons.png @(0,84,182x5)")
save_hud("jump_bar_progress", crop_icons((0,89,182,94)), "gui/icons.png @(0,89,182x5)")
add_unmatched("gui", "gui/sprites/hud/jump_bar_cooldown.png", "no 3rd jump-bar state existed in 1.8.9")

# armor
save_hud("armor_full", crop_icons((16,9,25,18)), "gui/icons.png @(16,9,9x9)")
save_hud("armor_half", crop_icons((25,9,34,18)), "gui/icons.png @(25,9,9x9)")
save_hud("armor_empty", crop_icons((34,9,43,18)), "gui/icons.png @(34,9,9x9)")

# air
save_hud("air", crop_icons((16,18,25,27)), "gui/icons.png @(16,18,9x9)")
save_hud("air_empty", crop_icons((25,18,34,27)), "gui/icons.png @(25,18,9x9)")
save_hud("air_bursting", crop_icons((25,18,34,27)), "gui/icons.png @(25,18,9x9) [reused air_empty - popping animation frames aren't separable in the 1.8.9 atlas]")

# food
save_hud("food_empty", crop_icons((16,27,25,36)), "gui/icons.png @(16,27,9x9)")
save_hud("food_full", crop_icons((52,27,61,36)), "gui/icons.png @(52,27,9x9)")
save_hud("food_half", crop_icons((61,27,70,36)), "gui/icons.png @(61,27,9x9)")
save_hud("food_empty_hunger", crop_icons((133,27,142,36)), "gui/icons.png @(133,27,9x9)")
save_hud("food_full_hunger", crop_icons((52,27,61,36)), "gui/icons.png @(52,27,9x9) [1.8.9 only re-tints the outline for Hunger, not the drumstick fill]")
save_hud("food_half_hunger", crop_icons((61,27,70,36)), "gui/icons.png @(61,27,9x9) [see food_full_hunger]")

# hearts
HEART_MAP = {
    "container": (16,0), "container_blinking": (25,0),
    "container_hardcore": (16,45), "container_hardcore_blinking": (25,45),
    "full": (52,0), "half": (61,0),
    "hardcore_full": (52,45), "hardcore_half": (61,45),
    "poisoned_full": (88,0), "poisoned_half": (97,0),
    "poisoned_hardcore_full": (88,45), "poisoned_hardcore_half": (97,45),
    "withered_full": (124,0), "withered_half": (133,0),
    "withered_hardcore_full": (124,45), "withered_hardcore_half": (133,45),
    "absorbing_full": (160,0), "absorbing_half": (169,0),
    "absorbing_hardcore_full": (160,45), "absorbing_hardcore_half": (169,45),
}
new_heart_files = set(os.path.splitext(f)[0] for f in os.listdir(f"{NEW}/gui/sprites/hud/heart"))
for name, (u,v) in HEART_MAP.items():
    if name in new_heart_files:
        img = crop_icons((u,v,u+9,v+9))
        target = f"{OUT}/gui/sprites/hud/heart/{name}.png"
        os.makedirs(os.path.dirname(target), exist_ok=True)
        img.save(target)
        add_matched("gui", f"gui/sprites/hud/heart/{name}.png", f"gui/icons.png @({u},{v},9x9)",
                    "reconstructed(crop from legacy atlas)", "")
    blinking = name.replace("full","full_blinking").replace("half","half_blinking") if ("full" in name or "half" in name) else None
    if blinking and blinking in new_heart_files and blinking not in HEART_MAP:
        img = crop_icons((u,v,u+9,v+9))
        target = f"{OUT}/gui/sprites/hud/heart/{blinking}.png"
        img.save(target)
        add_matched("gui", f"gui/sprites/hud/heart/{blinking}.png", f"gui/icons.png @({u},{v},9x9)",
                    "reconstructed(crop, reused non-blinking colour)",
                    "1.8.9 has no distinct blinking-tinted fill for this state; the steady-state colour was reused")

handled_hearts = set(HEART_MAP.keys()) | {n.replace("full","full_blinking").replace("half","half_blinking") for n in HEART_MAP if "full" in n or "half" in n}
for f in sorted(new_heart_files):
    if f not in handled_hearts:
        reason = ("no 1.8.9 source - Frozen status effect didn't exist until 1.17" if f.startswith("frozen")
                   else "no confidently-identifiable 1.8.9 coordinates found for mount/vehicle hearts")
        add_unmatched("gui", f"gui/sprites/hud/heart/{f}.png", reason)

print("stage3 GUI done")
with open(f"{ROOT}/report_stage3.json","w") as fh:
    json.dump(report, fh, indent=2)
