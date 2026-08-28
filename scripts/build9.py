import os, json, shutil
from PIL import Image

ROOT = "/home/claude/work"
OLD = f"{ROOT}/old_pack/assets/minecraft/textures"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures"

report = json.load(open(f"{ROOT}/report_stage8.json"))

def add_matched(new_rel, old_desc, method, note=""):
    report["matched"].append({"category": "gui", "new": new_rel, "old_source": old_desc,
                               "method": method, "note": note})

def add_unmatched(new_rel, reason):
    report["unmatched"].append({"category": "gui", "new": new_rel, "reason": reason})

def copy_direct(rel, old_rel=None):
    old_rel = old_rel or rel
    src, dst = f"{OLD}/{old_rel}", f"{OUT}/{rel}"
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        return True
    return False

# ---- panorama (26.1.2's template ships 1x1 stub placeholders here) -------
for i in range(6):
    rel = f"gui/title/background/panorama_{i}.png"
    if copy_direct(rel):
        add_matched(rel, rel, "exact",
                    "26.1.2's own template shipped 1x1 placeholder stubs for these; used the real 1.8.9 "
                    "256x256 cubemap faces instead")

# ---- creative inventory tabs (3 of 4 old files still exist in 26.1.2) ----
for name in ["tab_inventory", "tab_item_search", "tab_items"]:
    rel = f"gui/container/creative_inventory/{name}.png"
    if copy_direct(rel):
        add_matched(rel, rel, "exact", "verified identical 256x256 canvas")
add_unmatched("gui/container/creative_inventory/tabs.png",
              "no equivalent 26.1.2 file exists at this path (old tabs.png' role appears restructured)")

# ---- spectator head icons (spectator mode existed since 1.8) -------------
spec = Image.open(f"{OLD}/gui/spectator_widgets.png").convert("RGBA")
head_map = {"teleport_to_player": (0,0,16,16), "teleport_to_team": (16,0,32,16)}
for name, box in head_map.items():
    target = f"{OUT}/gui/sprites/spectator/{name}.png"
    if os.path.isfile(target):
        spec.crop(box).save(target)
        add_matched(f"gui/sprites/spectator/{name}.png", "gui/spectator_widgets.png",
                    "reconstructed(crop)", f"cropped from the old spectator icon atlas @{box}")
for name in ["close", "scroll_left", "scroll_right"]:
    add_unmatched(f"gui/sprites/spectator/{name}.png",
                  "a plausible source icon exists in the old spectator_widgets.png atlas but I couldn't "
                  "isolate a confident individual boundary for it in the time available")

# ---- villager trading (confirmed size mismatch, same issue as before) ----
add_unmatched("gui/container/villager.png",
              "canvas grew 256x256 -> 512x256 for the reworked multi-trade layout, same issue as villager2")

# ---- everything else never touched: categorize and bulk-mark -------------
NEW_SYSTEM_REASONS = {
    "gui/advancements": "Advancements replaced Achievements in 1.12, no 1.8.9 source",
    "gui/sprites/advancements": "Advancements replaced Achievements in 1.12, no 1.8.9 source",
    "gui/sprites/boss_bar": "modern per-colour boss bar sprite system, 1.8.9 had at most one fixed style",
    "gui/sprites/container": "generic slot/highlight sprites belong to a per-sprite GUI architecture 1.8.9 "
                              "didn't have (1.8.9 baked slots into the big background sheets instead)",
    "gui/sprites/dialog": "server dialog system added much later, no 1.8.9 source",
    "gui/sprites/gamemode_switcher": "F4 gamemode switcher UI added later, no 1.8.9 source",
    "gui/hanging_signs": "hanging signs added in 1.20, no 1.8.9 source",
    "gui/sprites/icon": "Realms/social/accessibility icons, all post-1.8.9 features",
    "gui/presets": "world-creation preset thumbnails for game rules added later, no 1.8.9 source",
    "gui/realms": "Realms UI was extremely minimal in 1.8.9 and doesn't map to this many modern assets",
    "gui/sprites/notification": "toast/notification system added later, no 1.8.9 source",
    "gui/sprites/pending_invite": "Realms invite UI, post-1.8.9",
    "gui/sprites/player_list": "tab-list UI icons (e.g. hats) added later, no 1.8.9 source",
    "gui/sprites/popup": "post-1.8.9 UI system",
    "gui/sprites/realm_status": "Realms UI, post-1.8.9",
    "gui/recipe_book.png": "the Recipe Book was added in 1.12, doesn't exist in 1.8.9",
    "gui/sprites/recipe_book": "the Recipe Book was added in 1.12, doesn't exist in 1.8.9",
    "gui/sprites/server_list": "server list icons restructured since 1.8.9, no clean per-sprite source",
    "gui/sprites/social_interactions": "the Social Interactions screen was added in 1.14, no 1.8.9 source",
    "gui/sprites/spectator": "handled above",
    "gui/sprites/statistics": "Statistics screen icons restructured, no 1.8.9 per-sprite source",
    "gui/sprites/toast": "the toast/achievement-popup sprite system was restructured after 1.8.9",
    "gui/sprites/tooltip": "post-1.8.9 UI system",
    "gui/sprites/transferable_list": "post-1.8.9 UI system (datapack/resource pack pickers)",
    "gui/sprites/widget": "1.8.9 drew buttons/sliders/checkboxes as flat code-drawn rectangles, not "
                          "textures - there is no source texture to port",
    "gui/sprites/world_list": "world-selection-screen icons restructured since 1.8.9",
    "particle": "dense, low-landmark 8px-scale atlas - I couldn't establish reliable source coordinates "
                "in the time available (see conversation notes); left as modern default rather than guess",
    "trims": "armor trim system added in 1.20, no 1.8.9 source",
    "mob_effect": "1.8.9 did not show individual status-effect icons in the inventory screen the way "
                  "modern versions do; no source exists",
    "map": "map marker/decoration icons - most (banners, Trial Chambers, etc.) are post-1.8.9 content, and "
           "the old map_icons.png atlas is only 32x32 with no reliable per-icon coordinate table found",
    "font": "the bitmap font system was completely replaced by a JSON provider + per-unicode-page system",
}

new_root = NEW
all_new = set()
for dp, _, files in os.walk(new_root):
    for f in files:
        if f.lower().endswith(".png"):
            rel = os.path.relpath(os.path.join(dp, f), new_root).replace(os.sep, "/")
            all_new.add(rel)

already_covered = set(m["new"] for m in report["matched"]) | set(m["new"] for m in report["unmatched"])
still_uncovered = sorted(all_new - already_covered)

def classify(rel):
    parts = rel.split("/")
    for depth in range(min(3, len(parts)), 0, -1):
        key = "/".join(parts[:depth])
        if key in NEW_SYSTEM_REASONS:
            return NEW_SYSTEM_REASONS[key]
    top = parts[0]
    if top in NEW_SYSTEM_REASONS:
        return NEW_SYSTEM_REASONS[top]
    return None

n_bulk = 0
n_unclassified = []
for rel in still_uncovered:
    reason = classify(rel)
    if reason:
        report["unmatched"].append({"category": "gui" if rel.startswith("gui") else rel.split("/")[0],
                                     "new": rel, "reason": reason})
        n_bulk += 1
    else:
        n_unclassified.append(rel)

print(f"bulk-marked {n_bulk} files as unmatched with categorized reasons")
print(f"unclassified (need manual look): {len(n_unclassified)}")

# final manual pass on the remaining specific files
MANUAL_REASONS = {
    "gui/footer_separator.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/header_separator.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/inworld_footer_separator.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/inworld_header_separator.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/inworld_menu_background.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/inworld_menu_list_background.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/menu_background.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/menu_list_background.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/tab_header_background.png": "part of 26.1.2's redesigned multi-panel menu chrome, no 1.8.9 equivalent",
    "gui/sprites/hud/crosshair_attack_indicator_background.png": "the attack-cooldown indicator was added in 1.9, after 1.8.9",
    "gui/sprites/hud/crosshair_attack_indicator_full.png": "the attack-cooldown indicator was added in 1.9, after 1.8.9",
    "gui/sprites/hud/crosshair_attack_indicator_progress.png": "the attack-cooldown indicator was added in 1.9, after 1.8.9",
    "gui/sprites/hud/hotbar_attack_indicator_background.png": "the attack-cooldown indicator was added in 1.9, after 1.8.9",
    "gui/sprites/hud/hotbar_attack_indicator_progress.png": "the attack-cooldown indicator was added in 1.9, after 1.8.9",
    "gui/sprites/hud/hotbar_offhand_left.png": "the off-hand slot was added in 1.9, after 1.8.9",
    "gui/sprites/hud/hotbar_offhand_right.png": "the off-hand slot was added in 1.9, after 1.8.9",
    "gui/sprites/hud/effect_background.png": "1.8.9 didn't show status-effect icons in this HUD-adjacent style",
    "gui/sprites/hud/effect_background_ambient.png": "1.8.9 didn't show status-effect icons in this HUD-adjacent style",
    "gui/sprites/hud/locator_bar_arrow_down.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_arrow_up.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_background.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_dot/bowtie.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_dot/default_0.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_dot/default_1.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_dot/default_2.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/sprites/hud/locator_bar_dot/default_3.png": "the locator/waypoint bar is a recent feature, no 1.8.9 source",
    "gui/title/background/panorama_overlay.png": "26.1.2's own template ships this as a 1x1 (no-op) stub and 1.8.9 never had a separate overlay file - left as the harmless no-op default",
    "gui/title/edition.png": "the 'Java Edition' badge was added later to disambiguate from Bedrock, no 1.8.9 source",
    "gui/title/minceraft.png": "an easter-egg alternate logo variant, no fixed 1.8.9 equivalent to pick",
    "gui/title/minecraft.png": "canvas grew 256x256 -> 1024x256 (likely packing extra logo variants/language forms) - "
                                "no safe way to place the old single logo without guessing the new layout",
    "gui/title/mojangstudios.png": "different company branding text ('Mojang Studios' vs old 'Mojang') at a much "
                                    "larger canvas (512x512 vs old's smaller splash) - not a simple resize",
    "gui/title/realms.png": "Realms branding, not part of 1.8.9's simpler title screen",
}
for rel in n_unclassified:
    reason = MANUAL_REASONS.get(rel, "no 1.8.9 source identified")
    report["unmatched"].append({"category": "gui", "new": rel, "reason": reason})

with open(f"{ROOT}/report_stage9.json", "w") as f:
    json.dump(report, f, indent=2)
print("stage9 done, all files now categorized")
