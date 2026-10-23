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


def _detect_zip_root_prefix(zf):
    """
    Return a prefix to strip (e.g. ``'MyPack/'``) when the zip looks like a
    "zip of a folder": every entry lives under exactly one top-level
    directory and there are no real files directly at the root.

    Returns ``''`` (no stripping) when:
    * more than one distinct top-level name is present, or
    * at least one real file sits directly at the zip root, or
    * the single top-level folder is named ``'assets'`` (already correct layout).

    ``__MACOSX`` metadata and hidden (``'.'``-prefixed) entries are ignored.
    """
    top_roots = set()
    has_root_files = False

    for name in zf.namelist():
        top = name.split('/')[0]
        if not top or top.startswith('.') or top == '__MACOSX':
            continue
        top_roots.add(top)
        # A root-level file has no '/' in the path at all.
        if '/' not in name:
            has_root_files = True

    if has_root_files or len(top_roots) != 1:
        return ''

    folder = next(iter(top_roots))
    return '' if folder == 'assets' else folder + '/'


def _is_pack_file(name, prefix):
    """True if *name* is a resource-pack entry we want, after stripping *prefix*."""
    unprefixed = name[len(prefix):]
    return unprefixed.startswith("assets/") or unprefixed in ("pack.mcmeta", "pack.png")


def _extract_stripped(zf, members, prefix, dest):
    """Extract *members* from *zf* into *dest*, removing *prefix* from each path."""
    for member in members:
        rel = member[len(prefix):]
        if not rel or rel.endswith('/'):
            continue  # skip bare directory entries
        target = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(member) as src, open(target, 'wb') as dst:
            shutil.copyfileobj(src, dst)


def _extract(zip_path, dest, friendly_name):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path) as zf:
            prefix = _detect_zip_root_prefix(zf)
            members = [n for n in zf.namelist() if _is_pack_file(n, prefix)]
            if prefix:
                _extract_stripped(zf, members, prefix, dest)
            else:
                zf.extractall(dest, members=members)
    except zipfile.BadZipFile:
        raise RuntimeError(
            f"{friendly_name} doesn't look like a valid .zip file. "
            f"Please double-check the file and try again."
        )

    # Safety net: if assets/ still isn't directly at the top level but
    # there's exactly one subfolder that contains it, hoist it up.
    # Handles unusual layouts the prefix detection above may not have caught.
    if not os.path.isdir(os.path.join(dest, "assets")):
        entries = [
            e for e in os.listdir(dest)
            if e != "__MACOSX" and not e.startswith(".")
        ]
        subdirs = [e for e in entries if os.path.isdir(os.path.join(dest, e))]
        if len(subdirs) == 1 and os.path.isdir(
            os.path.join(dest, subdirs[0], "assets")
        ):
            inner = os.path.join(dest, subdirs[0])
            for item in os.listdir(inner):
                shutil.move(os.path.join(inner, item), os.path.join(dest, item))
            shutil.rmtree(inner)

    if not os.path.isdir(os.path.join(dest, "assets", "minecraft", "textures")):
        raise RuntimeError(
            f"Couldn't find assets/minecraft/textures inside {friendly_name}. "
            f"Is this a real Minecraft resource pack .zip (with pack.mcmeta "
            f"and an assets/ folder), and not, say, a zip of a zip?"
        )


_extract("/work/old_pack.zip", "/work/old_pack", "your uploaded 1.8.9 pack")
_extract("/work/new_pack.zip", "/work/new_pack", "the bundled 26.1.2 reference pack")

print("Extracted and validated both packs.")
