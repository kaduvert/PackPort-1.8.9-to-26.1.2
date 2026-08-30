#!/usr/bin/env bash
#
# convert.sh — runs the full 1.8.9 -> 26.1.2 texture pack conversion.
#
# Usage:
#   ./convert.sh <1.8.9-pack.zip> <26.1.2-pack.zip> [workdir]
#
# Requires: python3 (with Pillow: pip install pillow --break-system-packages),
# unzip, zip. Expects a sibling "scripts/" directory containing aliases.py
# and build.py / build2.py ... build13.py (i.e. run this from inside the
# extracted conversion-source-code.zip, or pass -s/--scripts to point at it).
#
# Produces, inside [workdir] (default: ./build):
#   1.8.9-legacy-textures-26.1.2.zip   <- the finished resource pack
#   mapping_data.json                  <- full matched/unmatched audit trail
#
# The individual build*.py scripts hardcode ROOT = "/home/claude/work"
# internally (that's where they were originally developed), so this script
# copies them into the workdir and rewrites that one path with sed rather
# than requiring you to use that exact directory yourself.

set -euo pipefail

usage() {
    echo "Usage: $0 <1.8.9-pack.zip> <26.1.2-pack.zip> [workdir]" >&2
    echo "  workdir defaults to ./build" >&2
    exit 1
}

[ $# -lt 2 ] && usage

OLD_ZIP=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
NEW_ZIP=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
mkdir -p "${3:-$(pwd)/build}"
WORKDIR=$(cd "${3:-$(pwd)/build}" && pwd)
SCRIPT_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/scripts" && pwd)"

for tool in python3 unzip zip sed; do
    command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: '$tool' is required but not found." >&2; exit 1; }
done
[ -f "$OLD_ZIP" ] || { echo "ERROR: 1.8.9 pack not found: $OLD_ZIP" >&2; exit 1; }
[ -f "$NEW_ZIP" ] || { echo "ERROR: 26.1.2 pack not found: $NEW_ZIP" >&2; exit 1; }
[ -d "$SCRIPT_SRC_DIR" ] || { echo "ERROR: no scripts/ directory found next to this script ($SCRIPT_SRC_DIR)." >&2; exit 1; }
python3 -c "import PIL" 2>/dev/null || { echo "ERROR: Pillow is required: pip install pillow --break-system-packages" >&2; exit 1; }

echo "== 1.8.9 -> 26.1.2 texture pack conversion =="
echo "1.8.9 pack:  $OLD_ZIP"
echo "26.1.2 pack: $NEW_ZIP"
echo "Work dir:    $WORKDIR"
echo

mkdir -p "$WORKDIR"/{old_pack,new_pack,scripts}
rm -rf "$WORKDIR/output_pack"
rm -f "$WORKDIR"/report_stage*.json

echo "-- Extracting packs --"
unzip -oq "$OLD_ZIP" -d "$WORKDIR/old_pack"
unzip -oq "$NEW_ZIP" -d "$WORKDIR/new_pack"

echo "-- Copying scripts (patching the hardcoded work path) --"
for f in "$SCRIPT_SRC_DIR"/*.py; do
    sed "s|/home/claude/work|$WORKDIR|g" "$f" > "$WORKDIR/scripts/$(basename "$f")"
done

cd "$WORKDIR"

# Run order matters and is NOT alphabetical/numerical - build11.py was
# written before build12/13 existed and its filename reflects that, not
# when it actually runs. See the source zip's README for the full
# rationale behind each stage.
STAGES=(
    build.py     # blocks/items: exact matches + alias dictionary + fuzzy fallback
    build2.py    # entities/environment/colormap/misc/effect + safety checks
    build3.py    # gui container backgrounds + HUD sprite reconstruction
    build4.py    # clock/compass animation frame slicing
    build5.py    # bed item-icon override; initial chest/glint pass
    build7.py    # paintings
    build8.py    # Bad Omen bottle redesign, promo-stub cleanup
    build9.py    # full texture-tree audit (catches anything missed above)
    build10.py   # pig/cow/mooshroom pad+composite fix (pixel-overlap verified)
    build12.py   # chest UV/seam fix, armor icon swap fix, armor layers, bed
                 # revert, final-audit exact matches, empty-armor-slot icons,
                 # pack icon
    build13.py   # user-requested removals (water/panorama/single-chest/
                 # donkey/air-bubble/redstone-dust/brewing/creative-inv gui)
                 # + crit/enchanted-hit particle port
    build11.py   # broad mob-simplification pass (keep only basic mobs)
    build6.py    # final strip: removes everything logged as unmatched, incl.
                 # unmodified non-texture assets (this is what fixes the
                 # Sodium shader-conflict warning)
)

for stage in "${STAGES[@]}"; do
    echo
    echo "== $stage =="
    python3 "scripts/$stage"
done

echo
echo "-- Packaging --"
find output_pack -type d -empty -delete 2>/dev/null || true

OUT_ZIP="$WORKDIR/1.8.9-legacy-textures-26.1.2.zip"
rm -f "$OUT_ZIP"
(cd output_pack && zip -r -q "$OUT_ZIP" . -x ".*")

LATEST_REPORT=$(ls -1 report_stage*.json | sort -V | tail -1)
cp "$LATEST_REPORT" "$WORKDIR/mapping_data.json"

echo
echo "== Done =="
echo "Resource pack: $OUT_ZIP ($(du -h "$OUT_ZIP" | cut -f1))"
echo "Mapping data:  $WORKDIR/mapping_data.json"
