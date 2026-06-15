#!/usr/bin/env python3
"""Shortlist tabular features for the photo-z model.

The frozen catalog has ~50 candidate columns. Don't eyeball them one by one:
this script ranks every column by how much it relates to redshift (mutual
information + RandomForest importance), drops the non-features (IDs, errors,
labels) and near-duplicates (collinear), and prints a shortlist to take into
the model + the detailed EDA (see KB · Preprocessing & features, EDA task).

Run anywhere with the data-science deps (Colab, or the `macrocosm` venv):
    python scripts/feature_shortlist.py                    # quick pass, ~500 rows
    python scripts/feature_shortlist.py --n 5000 --top 15  # steadier ranking

Tip: the slow part is downloading the 207 MB parquet every run. Grab it ONCE and
pass the local path so re-runs are instant:
    gcloud storage cp gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet .
    python scripts/feature_shortlist.py --catalog catalog_v1.parquet
Reading `gs://...` directly needs GCS auth (Colab `auth.authenticate_user()`,
locally `gcloud auth application-default login`).
"""
import argparse
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.ensemble import RandomForestRegressor

CATALOG = "gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet"

# columns that are never model features (IDs, locators, label-adjacent)
NON_FEATURES = {
    "idx", "perm", "objid", "specObjID", "ra", "dec", "run", "rerun", "camcol",
    "field", "plate", "mjd", "fiberID", "redshift", "zErr", "zWarning", "class", "subClass",
}


def build_features(df):
    """Drop non-features, derive colors + a concentration index. Returns (X, y)."""
    drop = set(NON_FEATURES) | {c for c in df.columns if "Err" in c}      # error columns
    X = df.drop(columns=[c for c in drop if c in df.columns]).select_dtypes("number").copy()
    # colors = the core photo-z signal (SED shape), from the dereddened mags
    for a, b in [("u", "g"), ("g", "r"), ("r", "i"), ("i", "z")]:
        if {f"dered_{a}", f"dered_{b}"} <= set(df.columns):
            X[f"{a}-{b}"] = df[f"dered_{a}"] - df[f"dered_{b}"]
    # light-concentration index (helps break colour degeneracies)
    if {"petroR90_r", "petroR50_r"} <= set(df.columns):
        X["conc_r"] = df["petroR90_r"] / df["petroR50_r"].replace(0, np.nan)
    X = X.replace([np.inf, -np.inf], np.nan).dropna()
    y = df.loc[X.index, "redshift"].values
    return X, y


def rank_features(X, y, seed=0):
    """Rank by RandomForest importance + mutual information with z (nonlinear)."""
    mi = pd.Series(mutual_info_regression(X, y, random_state=seed), index=X.columns)
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, n_jobs=-1,
                               random_state=seed).fit(X, y)
    imp = pd.Series(rf.feature_importances_, index=X.columns)
    return pd.concat({"rf_importance": imp, "mutual_info": mi}, axis=1) \
             .sort_values("rf_importance", ascending=False)


def decorrelate(X, ranked, thresh=0.95):
    """Keep features in importance order, skipping any near-duplicate of a kept one."""
    corr, keep = X.corr().abs(), []
    for f in ranked.index:
        if all(corr.loc[f, k] < thresh for k in keep):
            keep.append(f)
    return keep


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", default=CATALOG, help="catalog parquet (local path or gs://)")
    ap.add_argument("--n", type=int, default=500,
                    help="sample size (perm < n). ~500 is fine for a quick ranking; "
                         "bump to a few thousand for the final selection; 0 = all")
    ap.add_argument("--top", type=int, default=15, help="shortlist length")
    ap.add_argument("--corr", type=float, default=0.95, help="collinearity threshold to drop dupes")
    args = ap.parse_args()

    df = pd.read_parquet(args.catalog)
    if args.n and "perm" in df.columns:
        df = df[df.perm < args.n]
    print(f"[shortlist] {len(df):,} galaxies, {df.shape[1]} catalog columns")

    X, y = build_features(df)
    print(f"[shortlist] {X.shape[1]} candidate features after cleaning + colours\n")

    ranked = rank_features(X, y)
    print("=== feature ranking (by RF importance) ===")
    print(ranked.round(4).to_string())

    keep = decorrelate(X, ranked, args.corr)
    print(f"\n=== shortlist (top {args.top}, |corr| < {args.corr}) ===")
    for i, f in enumerate(keep[:args.top], 1):
        print(f"  {i:2d}. {f}")
    if args.n and args.n < 5000:
        print("\n(quick pass on a small sample — re-run with --n 5000 before locking features.)")
    print("\nStarting tabular feature set. Now do the detailed EDA on THESE only "
          "(distribution/skew, scatter vs z, missing). See KB · Preprocessing & features.")


if __name__ == "__main__":
    main()
