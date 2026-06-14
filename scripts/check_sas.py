#!/usr/bin/env python3
"""Probe the SDSS SAS mount inside a Compute Job — find where the DR17 frames
actually live, so we can point --sas at the right path.

Symptom this diagnoses: a build where EVERY galaxy is "missing/broken frame"
(all-zero stamps, finishes in ~1s) — that means fits.open never found a file,
i.e. the SAS mount path is wrong.

Usage (as a quick Job command, with SDSS SAS mounted):
    python scripts/check_sas.py "/home/idies/workspace/SDSS SAS"
"""
import sys
import os
import glob

sas = sys.argv[1] if len(sys.argv) > 1 else "/home/idies/workspace/SDSS SAS"
print("SAS root:", repr(sas), "isdir:", os.path.isdir(sas))


def show(p, n=20):
    try:
        items = sorted(os.listdir(p))
        print(f"  {p!r}: {len(items)} entries -> {items[:n]}")
    except Exception as e:
        print(f"  {p!r}: ERROR {type(e).__name__}: {e}")


# walk the expected DR17 frames path one level at a time
show(sas)
acc = sas
for part in ["dr17", "eboss", "photoObj", "frames", "301"]:
    acc = os.path.join(acc, part)
    show(acc)

# look for ANY frame file a few ways
patterns = [
    os.path.join(sas, "dr17/eboss/photoObj/frames/301/*/*/frame-r-*.fits.bz2"),
    os.path.join(sas, "**/frame-r-*.fits.bz2"),
]
for pat in patterns:
    hits = glob.glob(pat, recursive=True)
    print(f"glob {pat!r}: {len(hits)} matches")
    if hits:
        print("   example:", hits[0])
        break

# also show what's directly under workspace (in case the mount name differs)
show("/home/idies/workspace")
