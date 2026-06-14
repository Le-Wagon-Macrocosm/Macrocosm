#!/usr/bin/env bash
# Build a RANGE of dataset shards on SciServer and push them to GCS.
# All-hands distributed build: each teammate runs a different shard range on
# their own SciServer container; everyone writes to the same bucket. Shards are
# idempotent (already-uploaded ones are skipped), so just rerun if interrupted.
#
# Usage:
#   ./scripts/build_shards.sh <first> <last> <K> <key.json> [workers]
#
#   first,last  inclusive shard range YOU were assigned (e.g. 0 19)
#   K           total number of shards the catalog is split into (same for everyone!)
#   key.json    path to sciserver-uploader.json on your persistent volume
#   workers     parallel processes (default 48; I/O-bound, so > cores is fine)
#
# Run it detached so it survives the browser closing:
#   nohup ./scripts/build_shards.sh 0 19 100 ~/workspace/Storage/<you>/persistent/sciserver-uploader.json 48 > build.log 2>&1 &
#   tail -f build.log
set -euo pipefail

FIRST=${1:?first shard}; LAST=${2:?last shard}; K=${3:?total shards K}
KEY=${4:?path to sciserver-uploader.json}; WORKERS=${5:-16}
CATALOG="gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet"

echo "building shards ${FIRST}..${LAST} of ${K}  (workers=${WORKERS})"
for i in $(seq "$FIRST" "$LAST"); do
  echo "================ shard ${i}/${K} ================"
  python -u scripts/prepare_data.py \
    --catalog "$CATALOG" --key "$KEY" \
    --of "$K" --shard "$i" --workers "$WORKERS"
done
echo "ALL DONE — your range ${FIRST}..${LAST} is built."
echo "Overall progress:  gcloud storage ls gs://macrocosm-lewagon/data/sample_v1/ | grep -c images_"
