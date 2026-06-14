#!/usr/bin/env python3
"""Pull arbitrary tabular columns for the FROZEN catalog and ship to GCS.

Infra tool: given a list of SDSS field names (PhotoObj `p.*` / SpecObj `s.*`),
fetch them for exactly the frozen 600k objIDs (aligned to `catalog_v1.parquet`
by `idx`) and upload as a parquet. Lets the team add features later without
re-freezing or touching the image build.

Runs on SciServer (CasJobs). Mirrors the selection in `freeze_catalog.py`, then
inner-joins to the frozen objIDs so the result is the SAME 600k, in `idx` order.

Usage (SciServer terminal / a small Compute Job):
    python scripts/pull_tabular.py p.deVAB_r p.deVPhi_r s.velDisp \\
        --catalog gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet \\
        --key <sciserver-uploader.json> \\
        --out gs://macrocosm-lewagon/data/sample_v1/tabular_extra.parquet
"""
import argparse
import numpy as np
import pandas as pd
from SciServer import CasJobs

# must match freeze_catalog.py's selection
Z_MIN, Z_MAX, CONTEXT = 0.02, 0.35, "DR17"


def build_sql(fields, k, n_chunks):
    cols = ",\n  ".join(["p.objid"] + fields)
    return f"""
SELECT
  {cols}
FROM PhotoObj p
JOIN SpecObj  s ON s.bestObjID = p.objID
WHERE s.class = 'GALAXY' AND s.zWarning = 0 AND p.clean = 1
  AND s.z BETWEEN {Z_MIN} AND {Z_MAX}
  AND p.objID % {n_chunks} = {k}
"""


def gcs_read_parquet(path, key):
    from google.cloud import storage
    bucket, blob = path[5:].split("/", 1)
    local = "/tmp/" + blob.split("/")[-1]
    storage.Client.from_service_account_json(key).bucket(bucket).blob(blob).download_to_filename(local)
    return pd.read_parquet(local)


def gcs_write_parquet(df, path, key):
    from google.cloud import storage
    local = "/tmp/" + path.split("/")[-1]
    df.to_parquet(local, index=False)
    bucket, blob = path[5:].split("/", 1)
    storage.Client.from_service_account_json(key).bucket(bucket).blob(blob).upload_from_filename(local)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fields", nargs="+", help="qualified column names, e.g. p.deVAB_r s.velDisp")
    ap.add_argument("--catalog", required=True, help="gs:// path to catalog_v1.parquet (objid+idx)")
    ap.add_argument("--key", required=True, help="sciserver-uploader.json (GCS read+write)")
    ap.add_argument("--out", required=True, help="gs:// output parquet path")
    ap.add_argument("-k", "--chunks", type=int, default=64)
    args = ap.parse_args()

    frozen = gcs_read_parquet(args.catalog, args.key)[["objid", "idx"]]
    print(f"[pull] frozen catalog: {len(frozen):,} objIDs; fetching {args.fields}")

    parts = []
    for k in range(args.chunks):
        parts.append(CasJobs.executeQuery(build_sql(args.fields, k, args.chunks),
                                          context=CONTEXT, format="pandas"))
        print(f"[pull]   chunk {k + 1}/{args.chunks}: total {sum(len(p) for p in parts):,}")
    extra = pd.concat(parts, ignore_index=True).drop_duplicates("objid")

    # keep exactly the frozen set, align to its idx order
    out = frozen.merge(extra, on="objid", how="left").sort_values("idx").reset_index(drop=True)
    missing = out[args.fields].isna().any(axis=1).sum()
    if missing:
        print(f"[pull] WARNING: {missing} rows missing some field (NaN)")
    gcs_write_parquet(out, args.out, args.key)
    print(f"[pull] wrote {args.out}  ({len(out):,} rows, cols: idx,objid,{','.join(args.fields)})")


if __name__ == "__main__":
    main()
