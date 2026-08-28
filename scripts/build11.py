import json, shutil, os

ROOT = "/home/claude/work"
NEW = f"{ROOT}/new_pack/assets/minecraft/textures/entity"
OUT = f"{ROOT}/output_pack/assets/minecraft/textures/entity"

report = json.load(open(f"{ROOT}/report_stage10.json"))

# Non-mob object/entity folders - never touched by this instruction either way
NOT_A_MOB = {"banner", "beacon", "bed", "bell", "boat", "chest", "chest_boat",
             "conduit", "decorated_pot", "enchantment", "end_crystal", "end_portal",
             "entity", "equipment", "experience", "fishing", "lead_knot", "minecart",
             "projectiles", "shield", "signs", "trident", "player", "armorstand"}

# Explicit + "very basic" classic mobs - keep whatever 1.8.9 mapping exists
KEEP_MOB_FOLDERS = {"zombie", "enderman", "chicken", "sheep", "pig", "cow",
                     "creeper", "skeleton", "spider", "squid", "slime", "ghast",
                     "blaze", "silverfish", "endermite", "bat", "snow_golem",
                     "iron_golem", "witch"}

# Folders kept, but only for their BASE file - the "fancy variant" work
# (coat colours, professions, biome skins, extra cat breeds) gets reverted
# since that goes beyond "very basic"
SIMPLIFY_TO_BASE = {
    "wolf": {"wolf.png", "wolf_angry.png", "wolf_tame.png", "wolf_collar.png"},
    "villager": {"villager.png"},
    "cat": {"ocelot.png"},
}

all_folders = set(os.path.basename(p) for p in
                   [d for d in os.listdir(NEW) if os.path.isdir(f"{NEW}/{d}")])
revert_folders = all_folders - NOT_A_MOB - KEEP_MOB_FOLDERS - set(SIMPLIFY_TO_BASE.keys())

def revert_file(rel, reason):
    src, dst = f"{NEW}/{rel}", f"{OUT}/{rel}"
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    elif os.path.isfile(dst):
        os.remove(dst)
    full_rel = f"entity/{rel}"
    report['matched'] = [m for m in report['matched'] if m['new'] != full_rel]
    report['unmatched'] = [m for m in report['unmatched'] if m['new'] != full_rel]
    report['unmatched'].append({"category": "entity", "new": full_rel, "reason": reason})

n = 0
# 1. fully revert non-basic mob folders
for folder in sorted(revert_folders):
    for dp, _, files in os.walk(f"{NEW}/{folder}"):
        for f in files:
            if f.lower().endswith(".png"):
                rel = os.path.relpath(os.path.join(dp, f), NEW).replace(os.sep, "/")
                revert_file(rel, "removed per user request: kept only explicit/very-basic classic mobs "
                                  "(zombie, enderman, chicken, sheep + similar simple iconic mobs); "
                                  f"'{folder}' is not in that reduced set")
                n += 1

# 2. simplify the 3 mixed-complexity folders down to just their base file
for folder, keep_files in SIMPLIFY_TO_BASE.items():
    for dp, _, files in os.walk(f"{NEW}/{folder}"):
        for f in files:
            if f.lower().endswith(".png"):
                rel = os.path.relpath(os.path.join(dp, f), NEW).replace(os.sep, "/")
                if os.path.basename(rel) not in keep_files:
                    revert_file(rel, "removed per user request: simplified back to just the base "
                                      f"1.8.9-equivalent file for '{folder}', dropping the profession/"
                                      "biome/coat-colour variant consolidation as beyond 'very basic'")
                    n += 1

print(f"reverted {n} files across {len(revert_folders)} non-basic mob folders + 3 simplified folders")
print("reverted folders:", sorted(revert_folders))

with open(f"{ROOT}/report_stage11.json", "w") as f:
    json.dump(report, f, indent=2)
