# _harness_finalize.py — NOT one of the original build*.py stages.
#
# Runs once, after build.py..build13.py have all completed. Replaces the
# tail end of convert.sh: pruning now-empty directories (no `find` binary
# in the browser), zipping output_pack (no `zip` binary either), and
# picking out mapping_data.json exactly the way convert.sh does --
# `ls report_stage*.json | sort -V | tail -1` -- which in practice resolves
# to report_stage11.json (written by build11.py, even though build6.py
# runs after it) because build6 writes report_final2.json instead, and
# build4 writes report_final.json instead of report_stage4.json -- neither
# of those matches the report_stage*.json pattern. This is original,
# intentional behavior, just faithfully preserved here.

import glob
import json
import os
import re
import zipfile

ROOT = "/work"


def prune_empty_dirs(root):
    """Equivalent of `find output_pack -type d -empty -delete`.

    Done as a fixed-point loop (re-checking os.listdir live) rather than a
    single os.walk pass, since a single bottom-up pass won't cascade a
    multi-level empty chain: os.walk snapshots a directory's contents
    before descending, so a parent whose only child was *just* removed
    still looks non-empty to that same pass.
    """
    changed = True
    while changed:
        changed = False
        for dirpath, _, _ in os.walk(root, topdown=False):
            if dirpath == root:
                continue
            if os.path.isdir(dirpath) and not os.listdir(dirpath):
                os.rmdir(dirpath)
                changed = True


prune_empty_dirs(f"{ROOT}/output_pack")

out_zip = f"{ROOT}/1.8.9-legacy-textures-26.1.2.zip"
if os.path.exists(out_zip):
    os.remove(out_zip)

with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    base = f"{ROOT}/output_pack"
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            zf.write(full, os.path.relpath(full, base))

# mapping_data.json = the highest-numbered report_stage*.json on disk,
# same selection convert.sh uses.
reports = glob.glob(f"{ROOT}/report_stage*.json")
if not reports:
    raise RuntimeError("No report_stage*.json files were produced by any stage — something upstream didn't run as expected.")


def _stage_num(path):
    m = re.search(r"report_stage(\d+)\.json", path)
    return int(m.group(1)) if m else -1


latest_report = sorted(reports, key=_stage_num)[-1]
with open(latest_report) as f:
    mapping = json.load(f)

with open(f"{ROOT}/mapping_data.json", "w") as f:
    json.dump(mapping, f, indent=2)

# Summary stats for the UI. Grouped by top-level method name (exact /
# alias / fuzzy), stripping the "(old-filename)" detail suffix.
by_method = {}
for m in mapping.get("matched", []):
    key = m.get("method", "unknown").split("(")[0]
    by_method[key] = by_method.get(key, 0) + 1

by_category = {}
for m in mapping.get("matched", []) + mapping.get("unmatched", []):
    key = m.get("category", "unknown")
    by_category[key] = by_category.get(key, 0) + 1

summary = {
    "source_report": os.path.basename(latest_report),
    "matched_total": len(mapping.get("matched", [])),
    "unmatched_total": len(mapping.get("unmatched", [])),
    "by_method": by_method,
    "by_category": by_category,
    "pack_zip_bytes": os.path.getsize(out_zip),
}
with open(f"{ROOT}/summary.json", "w") as f:
    json.dump(summary, f)

print(f"Done. {summary['matched_total']} matched, {summary['unmatched_total']} unmatched. "
      f"Pack size: {summary['pack_zip_bytes'] / 1024:.0f} KB")
