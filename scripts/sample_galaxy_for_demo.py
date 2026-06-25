# === shared setup: load catalog, clean -9999, build the 16 features ===
import json
import os
from pathlib import Path
from io import StringIO, BytesIO

import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import bz2
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.wcs import WCS, FITSFixedWarning
from astropy.coordinates import SkyCoord
from astroquery.sdss import SDSS
import astropy.units as u
import warnings
import argparse



"""
Need to change the CATALOG and HARD_PATH variables to point to the correct locations of your catalog and hard object IDs file.
The default stamp size is set to 64 pixels, but you can adjust it as needed.
The script will download stamps for a sample of galaxies and save them as .npy files in the current working directory.
"""
CATALOG = "/path/to/data_sample_v4.5_catalog_v4.parquet"
HARD_PATH = "/path/to/hard_objids.csv"
DEFAULT_STAMP_SIZE = 64

FEATS = [
    "dered_u", "dered_g", "dered_r", "dered_i", "dered_z",
    "log_expRad_r", "log_deVRad_r", "log_petroRad_r", "log_petroR50_r", "log_petroR90_r",
    "fracDeV_r", "u-g", "g-r", "r-i", "i-z", "conc_r"
]

BANDS = "ugriz"  # axis order → index 0=u, 1=g, 2=r, 3=i, 4=z

warnings.filterwarnings("ignore", category=FITSFixedWarning)


def build_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def load_features(path=CATALOG, n=None, seed=0):
    """Load catalog, clean the -9999 sentinel, build colors / log-sizes / conc.
    Returns (D, cat): D = features + redshift + objid (optionally subsampled), cat = full cleaned catalog.
    """
    cat = pd.read_parquet(path)

    num = cat.select_dtypes("number").columns
    cat.loc[:, num] = cat.loc[:, num].mask(cat.loc[:, num] <= -100)

    for a, b in [("u", "g"), ("g", "r"), ("r", "i"), ("i", "z")]:
        cat[f"{a}-{b}"] = (cat[f"dered_{a}"] - cat[f"dered_{b}"]).clip(-1, 4)

    for s in ["expRad_r", "deVRad_r", "petroRad_r", "petroR50_r", "petroR90_r"]:
        cat[f"log_{s}"] = np.log1p(cat[s].clip(lower=0))

    cat["conc_r"] = cat["petroR90_r"] / cat["petroR50_r"].replace(0, np.nan)
    D = cat[["objid", "redshift"] + FEATS].replace([np.inf, -np.inf], np.nan).dropna()

    if n is not None:
        D = D.sample(n, random_state=seed).reset_index(drop=True)

    for a in D.columns:
        if a[0:3] =='log':
            D = D.rename(columns={a:a[4:]})

    return D, cat


def load_hard_set(path=HARD_PATH):
    return set(pd.read_csv(path)["objid"])


def write_to_json(file_path, galaxy_df):
    """
    Convert a DF to JSON file to copy into website
    """
    if isinstance(galaxy_df, pd.DataFrame):
        records = galaxy_df.to_json(orient="records")
    else:
        raise TypeError("galaxy_df must be a DataFrame")

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        for record in eval(records):
            f.write(f"{record}\n".replace("'", '"'))

def round_radius_columns(df):
    df = df.copy()
    df = df.round(2)
    radius_cols = [
        c for c in ["expRad_r", "deVRad_r", "devRRad_r", "petroRad_r", "petroR50_r", "petroR90_r"]
        if c in df.columns
    ]
    if radius_cols:
        df.loc[:, radius_cols] = df.loc[:, radius_cols].round(1)
    return df


def smad(dz):
    return 1.4826 * np.median(np.abs(dz - np.median(dz)))


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    dz = (y_pred - y_true) / (1 + y_true)
    return {
        "MAE": round(float(np.mean(np.abs(y_pred - y_true))), 5),
        "sigma_MAD": round(float(smad(dz)), 5),
        "outlier_rate": round(float(np.mean(np.abs(dz) > 0.05)), 5),
    }


warnings.simplefilter('ignore', FITSFixedWarning)   # silence harmless WCS warnings

def cutout(ra, dec, band, size=64):
    print('yo iam')
    # 1. Define sky position
    pos_sky = SkyCoord(ra, dec, unit='deg')
    # 2. Get image from SDSS
    # Note: get_images returns a list of HDULists. We take the first one [0]
    try:
        hdu_list = SDSS.get_images(coordinates=pos_sky, band=band, radius=8*u.arcsec, data_release=17)
    except Exception as e:
        raise ValueError(f"Failed to fetch image from SDSS: {e}")

    if not hdu_list or len(hdu_list) == 0:
        raise ValueError("No images found for these coordinates.")

    hdu = hdu_list[0]
    data = hdu[0].data
    header = hdu[0].header

    # 3. Create WCS object
    w = WCS(header)

    # 4. Convert sky position to pixel coordinates explicitly
    # This returns (x, y) in pixel coordinates
    pix_pos_pre = w.world_to_pixel(pos_sky)
    pix_pos = [x.item() for x in pix_pos_pre]

    # 5. Create the cutout
    # Pass the pixel position directly.
    # Use limit_rounding_method='round' or 'floor'/'ceil' if needed, but explicit pixels usually avoid this.

    try:
        cutout_obj = Cutout2D(
            data=data,
            position=pix_pos,      # Explicit pixel coordinates (x, y)
            size=(size, size),     # Output size in pixels
            wcs=w,                 # Optional: preserves WCS info
            mode='partial',        # Allows partial overlap
            fill_value=0           # Value for pixels outside original image
        )
        return cutout_obj.data.astype('float32')

    except Exception as e:
        # If it still fails, it might be due to the position being completely outside the image
        raise ValueError(f"Failed to create cutout at pixel pos {pix_pos}: {e}")



def download_and_save_stamps(df, obj_ids, output_dir, size=DEFAULT_STAMP_SIZE, session=None):
    session = session or build_session()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for obj_id in obj_ids:
        try:
            ra = df[df['obj_id']==obj_id]['ra']
            dec = df[df['objid']==obj_id]['dec']
            stamp = np.stack([cutout(ra, dec, b) for b in 'ugriz'], axis=-1)   # -> (64, 64, 5)
            np.save(output_dir / f"{obj_id}_{size}.npy", stamp)

        except Exception as exc:
            print(f"Failed to download stamp for objID {obj_id}: {exc}")
            failed.append(obj_id)
            pass

    return failed

def main(catalog, hard):
    # TO DO: Add path to catalog & hard
    hard_ids = load_hard_set(HARD_PATH)
    print(f"hard set: {len(hard_ids)} galaxies")

    D, cat = load_features(n=93026, seed=0)
    sample_galaxy_df = D.sample(n=10)
    sample_galaxy_df = round_radius_columns(sample_galaxy_df)


    obj_ids = sample_galaxy_df["objid"].tolist()
    session = build_session()
    failed = download_and_save_stamps(sample_galaxy_df, obj_ids, output_dir=Path.cwd(), size=DEFAULT_STAMP_SIZE, session=session)

    if failed:
        print(f"{len(failed)} stamp downloads failed. Skipped in JSON download")
    else:
         print(f"Downloaded {len(obj_ids)} stamps successfully")

    if len(failed) > 0:
        sample_galaxy = sample_galaxy_df.set_index('objid', inplace=True).drop(failed, inplace=True)

    write_to_json(Path.cwd() / "sample_galaxies.json", sample_galaxy)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--hard', required=True)

    args = parser.parse_args()

    main(args.catalog, args.hard)
