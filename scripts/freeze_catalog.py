#!/usr/bin/env python3
"""Step A — freeze the Macrocosm catalog (run ONCE, on SciServer).

One CasJobs query over DR17 (PhotoObj x SpecObj) -> catalog_v1.parquet.
This ordered table *is* the dataset definition: every image stamp built later
is index-aligned to a row here, and every training subset is sliced from it.

Why everything is pulled here (not later, separately):
  - We must query the catalog anyway to get run/camcol/field for cutting stamps,
    so we pull a *generous* set of candidate tabular features in the SAME query.
    "Decide features later" then = selecting columns from this parquet — no
    re-query, no aligning 600k objIDs by IN(...). SQL columns are nearly free.

Two derived columns we add ourselves:
  - idx  : 0..N-1 in (run, camcol, field) order == the order stamps are built,
           so images_shard_*.npy row i  <-> catalog row idx==i.
  - perm : a fixed-seed random rank. The loader takes rows with perm < N to get
           a representative AND nested subset (6k subset of 60k subset of 600k).
           Plain "first N rows" would be spatially clustered (first runs only).

Run on SciServer (Compute container, persistent volume):
    !pip install -q pyarrow            # if not already present
    %run scripts/freeze_catalog.py     # or: !python scripts/freeze_catalog.py
"""
import argparse
import numpy as np
import pandas as pd
from SciServer import CasJobs

# ---- selection (scope: low-z galaxies, clean spectra) -----------------------
N_MAX = 600_000          # superset size; smaller routes are subsets of this
Z_MIN, Z_MAX = 0.02, 0.35   # project scope is z<0.4; 0.35 keeps a margin
SEED = 42                # fixes the `perm` column -> reproducible subsets
CONTEXT = "DR17"

# Generous candidate tabular features (decide which to USE later).
_BANDS = "ugriz"
_PHOTO_COLS = (
    ["p.objid", "p.ra", "p.dec", "p.run", "p.rerun", "p.camcol", "p.field"]
    + [f"p.modelMag_{b}" for b in _BANDS]
    + [f"p.modelMagErr_{b}" for b in _BANDS]
    + [f"p.cModelMag_{b}" for b in _BANDS]
    + [f"p.psfMag_{b}" for b in _BANDS]
    + [f"p.dered_{b}" for b in _BANDS]        # dereddened model mags
    + [f"p.extinction_{b}" for b in _BANDS]   # galactic extinction (deredden yourself)
    + ["p.petroMag_r", "p.petroRad_r", "p.petroR50_r", "p.petroR90_r"]  # size / concentration
    + ["p.fracDeV_r", "p.deVRad_r", "p.expRad_r"]                       # morphology
)
_SPEC_COLS = ["s.specObjID", "s.z AS redshift", "s.zErr", "s.zWarning",
              "s.class", "s.subClass", "s.plate", "s.mjd", "s.fiberID"]


def build_sql(n):
    cols = ",\n  ".join(_PHOTO_COLS + _SPEC_COLS)
    return f"""
SELECT TOP {n}
  {cols}
FROM PhotoObj p
JOIN SpecObj  s ON s.bestObjID = p.objID
WHERE s.class = 'GALAXY'
  AND s.zWarning = 0
  AND p.clean = 1
  AND s.z BETWEEN {Z_MIN} AND {Z_MAX}
ORDER BY p.run, p.camcol, p.field, p.objid
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-n", "--n-max", type=int, default=N_MAX,
                    help=f"max rows (superset size); default {N_MAX}")
    ap.add_argument("-o", "--out", default="catalog_v1.parquet",
                    help="output parquet path (write to a persistent volume)")
    args = ap.parse_args()

    sql = build_sql(args.n_max)
    print(f"[freeze] querying DR17 for up to {args.n_max:,} galaxies "
          f"(z in [{Z_MIN}, {Z_MAX}]) ...")
    # executeQuery streams the result; a straightforward indexed selection of
    # ~600k rows runs server-side in well under the quick-query limit. If it ever
    # times out, submit it as a CasJobs job into MyDB instead and download that.
    df = CasJobs.executeQuery(sql, context=CONTEXT, format="pandas")
    print(f"[freeze] got {len(df):,} rows, {df.shape[1]} columns")

    # row order == build order == image-array order
    df = df.reset_index(drop=True)
    df.insert(0, "idx", np.arange(len(df), dtype=np.int64))

    # fixed-seed permutation -> representative, nested subsets via perm < N
    df["perm"] = np.argsort(
        np.random.RandomState(SEED).permutation(len(df))
    ).astype(np.int64)

    df.to_parquet(args.out, index=False)
    print(f"[freeze] wrote {args.out}")

    # quick sanity / build-cost estimate
    nframes = df.groupby(["run", "camcol", "field"]).ngroups
    print(f"[freeze] unique (run,camcol,field) frames: {nframes:,}  "
          f"(~{nframes * 5:,} band-frame decompressions to build all stamps)")
    print(f"[freeze] z: min={df.redshift.min():.3f} "
          f"med={df.redshift.median():.3f} max={df.redshift.max():.3f}")
    print("[freeze] next: upload catalog_v1.parquet to "
          "gs://macrocosm-lewagon/data/sample_v1/, then run prepare_data.py shards")


if __name__ == "__main__":
    main()
