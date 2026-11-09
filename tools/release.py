"""Build the release zip, stopping at the first failure:
build -> check -> verify -> smoke -> jp_left -> qa_gate on every manifest -> textcover -> polish list -> README -> patch -> re-apply -> zip.

    python -X utf8 tools/release.py --version 1.0 [--force] [--no-build]

--no-build keeps build/blaze_union_en.iso, for iteration on the later steps. --force overwrites this version's files in release/.
The debug tool is off by construction: warp.py and scenes.py poke RAM from the emulator, build_en adds no debug code, and verify_build.py
accounts for every changed byte. The tour is not rerun here: qa_gate.py check fails unless it ran on this exact build (MANIFEST.build).
"""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build
import check_rom
from skill import SKILL

PY = [sys.executable, "-X", "utf8"]
RELEASE = ROOT / "release"
TEMPLATE = ROOT / "docs/release-readme.txt"


def run(*cmd):
    print("==", " ".join(str(c) for c in cmd), flush=True)
    if subprocess.call([str(c) for c in cmd], cwd=ROOT):
        sys.exit(f"release stopped: {cmd[1:4]} failed")


def hashes(path):
    crc, md5, sha1 = 0, hashlib.md5(), hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            crc = zlib.crc32(chunk, crc)
            md5.update(chunk)
            sha1.update(chunk)
    return {"size": Path(path).stat().st_size, "crc32": f"{crc:08X}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def unticked(text):
    return [line for line in text.splitlines() if line.startswith("- [ ]")]


def placeholders(text):
    """Template holes left in a README: <Game title> style, or a bare <repo>; html tags have no capital and no space."""
    return re.findall(r"<(?:[A-Z][^<>\n]*|repo|file|size|sha1|platform|publisher|year|game|ext)>", text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()

    stem = f"Blaze_Union_EN_v{a.version}"
    patch, zipped = RELEASE / f"{stem}.xdelta", RELEASE / f"{stem}.zip"
    if not a.force and (patch.exists() or zipped.exists()):
        sys.exit(f"{zipped.name} exists: --force to overwrite")
    check_rom.check()
    if not a.no_build:
        run(*PY, "tools/build.py")
    run(*PY, "tools/check.py")
    run(*PY, "tools/verify_build.py")
    run(*PY, f"{SKILL}/scripts/emu.py", build.OUT, "--out", "work/qa/smoke", "--route", "tools/routes/boot.txt", "--smoke")
    run(*PY, "tools/debug/jpleft.py", build.OUT)
    manifests = sorted((ROOT / "work/qa").rglob("manifest.tsv"))
    assert len(manifests) >= 2, f"want the visual and the story manifest: {manifests}"
    for m in manifests:
        run(*PY, f"{SKILL}/scripts/qa_gate.py", "check", m, m.parent / "verdicts")
    run(*PY, "tools/debug/cover.py", "work/qa/plog2")  # writes build/strings.tsv, which a clean build/ lacks
    run(*PY, f"{SKILL}/scripts/textcover.py", "work/qa/plog2", "build/strings.tsv", "--waive", "docs/text_unshown.tsv")

    left = unticked((ROOT / "docs/polish.md").read_text(encoding="utf-8"))
    if left:
        sys.exit(f"docs/polish.md: {len(left)} unticked, first: {left[0][:80]}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if placeholders(readme):
        sys.exit(f"README.md placeholders: {placeholders(readme)[:5]}")

    base, patched = hashes(build.ROM), hashes(build.OUT)
    for h in (base["sha1"], base["crc32"].lower()):
        if h not in readme.lower():
            sys.exit(f"README.md lacks the base hash {h}")
    RELEASE.mkdir(exist_ok=True)
    # -B: rebuilt Data.cpk moved to the end of the image, so matches sit further apart than xdelta3's default 64 MB window
    run("xdelta3", "-e", "-f", "-9", "-S", "djw", "-B", patched["size"], "-s", build.ROM, build.OUT, patch)
    back = ROOT / "build/reapply.iso"
    run("xdelta3", "-d", "-f", "-s", build.ROM, patch, back)
    if hashes(back) != patched:
        sys.exit("re-applied patch differs from the build")
    back.unlink()

    text = TEMPLATE.read_text(encoding="utf-8")
    for key, value in {"version": a.version, "patched_crc32": patched["crc32"], "patched_sha1": patched["sha1"],
                       "patched_size": patched["size"], "base_size": base["size"], "base_crc32": base["crc32"],
                       "base_md5": base["md5"], "base_sha1": base["sha1"]}.items():
        text = text.replace("{" + key + "}", str(value))
    assert "{" not in text, "unfilled field in docs/release-readme.txt"
    with zipfile.ZipFile(zipped, "w", zipfile.ZIP_STORED) as z:  # stored: an xdelta is already compressed
        z.write(patch, patch.name)
        z.writestr("README.txt", text.replace("\n", "\r\n"))
    print(zipped, zipped.stat().st_size, "patch", patch.stat().st_size, "sha1", hashes(patch)["sha1"])


if __name__ == "__main__":
    main()
