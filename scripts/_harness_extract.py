# _harness_extract.py — NOT one of the original build*.py stages.
#
# This is browser-harness glue: it replaces the "unzip" calls convert.sh
# makes on the command line, plus a bit of defensive normalization for
# packs that come wrapped in an extra top-level folder (a common quirk of
# e.g. GitHub's "Download ZIP" button, or re-zipping a folder in Finder/
# Explorer instead of its contents). It runs once, before build.py..build13.py.
#
# Expects /work/old_pack.zip and /work/new_pack.zip to already exist
# (written there by app.js from the user's upload and the bundled
# reference pack). Extracts them to /work/old_pack and /work/new_pack.

import os
import shutil
import zipfile


def _extract(zip_path, dest, friendly_name):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            members = [
                name for name in zf.namelist()
                if name.startswith("assets/")
                or name in ("pack.mcmeta", "pack.png")
            ]
            zf.extractall(dest, members=members)
    except zipfile.BadZipFile:
        raise RuntimeError(
            f"{friendly_name} doesn't look like a valid .zip file. "
            f"Please double-check the file and try again."
        )

    # Normalize: if assets/ isn't directly at the top level, but there's
    # exactly one subfolder that itself contains assets/, hoist its
    # contents up. Handles zips that wrap everything in one extra folder.
    if not os.path.isdir(f"{dest}/assets"):
        entries = [e for e in os.listdir(dest) if e not in ("__MACOSX",) and not e.startswith(".")]
        subdirs = [e for e in entries if os.path.isdir(os.path.join(dest, e))]
        if len(subdirs) == 1 and os.path.isdir(os.path.join(dest, subdirs[0], "assets")):
            inner = os.path.join(dest, subdirs[0])
            for name in os.listdir(inner):
                shutil.move(os.path.join(inner, name), os.path.join(dest, name))
            shutil.rmtree(inner)

    if not os.path.isdir(f"{dest}/assets/minecraft/textures"):
        raise RuntimeError(
            f"Couldn't find assets/minecraft/textures inside {friendly_name}. "
            f"Is this a real Minecraft resource pack .zip (with pack.mcmeta "
            f"and an assets/ folder), and not, say, a zip of a zip?"
        )


_extract("/work/old_pack.zip", "/work/old_pack", "your uploaded 1.8.9 pack")
_extract("/work/new_pack.zip", "/work/new_pack", "the bundled 26.1.2 reference pack")

print("Extracted and validated both packs.")
