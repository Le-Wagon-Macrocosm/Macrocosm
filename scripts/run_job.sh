#!/usr/bin/env bash
# One-line entrypoint for a SciServer Compute Job.
# Bundles the pip install + the build so the Job "Command" only needs the shard
# range, K, and your persistent path:
#
#   bash <persist>/Macrocosm/scripts/run_job.sh <first> <last> <K> <persist>
#
# e.g. (in the Compute Job "Command" box):
#   bash /home/idies/workspace/Storage/zhhrozhh/persistent/Macrocosm/scripts/run_job.sh \
#        0 7 100 /home/idies/workspace/Storage/zhhrozhh/persistent
#
# Teammates change only: the range (0 7), and their own <persist> (their username).
# Optional 5th/6th args override workers and the SAS mount.
set -euo pipefail

FIRST=${1:?first shard (e.g. 0)}
LAST=${2:?last shard inclusive (e.g. 7)}
K=${3:?total shards K (e.g. 100)}
PERSIST=${4:?persistent base, e.g. /home/idies/workspace/Storage/<you>/persistent}
WORKERS=${5:-16}
SAS=${6:-/home/idies/workspace/SDSS SAS}   # SAS mount path INSIDE a Compute Job

echo "[run_job] installing deps ..."
# A Compute Job's base python (mambaforge 3.10) lacks pandas, so install it
# explicitly — unlike the interactive SciServer Essentials env which bundles it.
pip install --user -q numpy pandas astropy google-cloud-storage gcsfs pyarrow

cd "$PERSIST/Macrocosm"
echo "[run_job] building shards ${FIRST}..${LAST} of ${K}  (persist=${PERSIST})"
bash scripts/build_shards.sh "$FIRST" "$LAST" "$K" \
  "$PERSIST/sciserver-uploader.json" "$WORKERS" "$SAS"
