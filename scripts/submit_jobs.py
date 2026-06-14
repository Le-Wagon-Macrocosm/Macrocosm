#!/usr/bin/env python3
"""Submit the dataset build as SciServer Compute Jobs — the sanctioned way to run
long batch work (browser-independent, queue-managed, more resources per job than
an interactive container). Run this FROM an interactive container (submitting is
light); the heavy cutting runs as queued Jobs.

`prepare_data.py` is reused unchanged — each job just runs that CLI for one shard.

Typical sequence:
    # 1. discover the jobs domain + exact image / data-volume names
    python scripts/submit_jobs.py --discover

    # 2. confirm a job can reach GCS (uses check_gcs.py) — do this ONCE
    python scripts/submit_jobs.py --test-gcs --image "<image>" --data-volume "<vol>"

    # 3. submit one job per shard for your range (idempotent: built shards skip)
    python scripts/submit_jobs.py --first 0 --last 99 --image "<image>" --data-volume "<vol>"
"""
import argparse
from SciServer import Jobs

CATALOG = "gs://macrocosm-lewagon/data/sample_v1/catalog_v1.parquet"
DEPS = "astropy google-cloud-storage gcsfs pyarrow"


def discover():
    domains = Jobs.getDockerComputeDomains()
    if not domains:
        print("No job-capable compute domains available to you.")
        return
    for d in domains:
        print("DOMAIN:", d.get("name"))
        print("  job images :", [i.get("name") for i in d.get("images", [])])
        print("  data vols  :", [v.get("name") for v in d.get("volumes", [])])
        print("  user vols  :", [v.get("name") for v in d.get("userVolumes", [])])
    print("\nPick the SDSS data volume + an image name from above, pass them as "
          "--data-volume / --image to --test-gcs and the real submit.")


def shard_cmd(repo, key, i, K, workers, sas):
    return (f"pip install --user -q {DEPS} && cd {repo} && "
            f"python -u scripts/prepare_data.py --catalog {CATALOG} "
            f"--key {key} --of {K} --shard {i} --workers {workers} --sas '{sas}'")


def test_cmd(repo, key):
    return (f"pip install --user -q google-cloud-storage && cd {repo} && "
            f"python -u scripts/check_gcs.py {key}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--persist", default="/home/idies/workspace/Storage/zhhrozhh/persistent",
                    help="your persistent volume base (repo + key live here)")
    ap.add_argument("--discover", action="store_true", help="list domains/images/volumes and exit")
    ap.add_argument("--test-gcs", action="store_true", help="submit ONE job that probes GCS write")
    ap.add_argument("--first", type=int, help="first shard to submit")
    ap.add_argument("--last", type=int, help="last shard to submit (inclusive)")
    ap.add_argument("--of", type=int, default=100, help="total shards K (default 100)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--domain", default=None, help="jobs domain name (default: first available)")
    ap.add_argument("--image", default=None, help="job docker image name (see --discover)")
    ap.add_argument("--data-volume", default="SDSS SAS", help="SDSS data volume name (see --discover)")
    ap.add_argument("--sas", default="/home/idies/workspace/SDSS SAS",
                    help="SAS mount path INSIDE the job (UI shows it when you tick the volume)")
    args = ap.parse_args()

    if args.discover:
        discover(); return

    repo = args.persist.rstrip("/") + "/Macrocosm"
    key = args.persist.rstrip("/") + "/sciserver-uploader.json"
    domains = Jobs.getDockerComputeDomains()
    domain = (Jobs.getDockerComputeDomainFromName(args.domain, domains)
              if args.domain else domains[0])
    uv = [{"name": "persistent", "needsWriteAccess": True}]
    dv = [{"name": args.data_volume}]

    if args.test_gcs:
        jid = Jobs.submitShellCommandJob(test_cmd(repo, key), domain, args.image, uv, dv,
                                         "", "gcs-egress-test")
        print(f"submitted GCS-egress test job {jid}; waiting...")
        Jobs.waitForJob(jid, verbose=True)
        print("final status:", Jobs.getJobStatus(jid))
        print("Check the job's log for 'GCS WRITE OK'. If present, jobs can push to GCS.")
        return

    if args.first is None or args.last is None:
        ap.error("give --first and --last (or --discover / --test-gcs)")
    for i in range(args.first, args.last + 1):
        jid = Jobs.submitShellCommandJob(shard_cmd(repo, key, i, args.of, args.workers, args.sas),
                                         domain, args.image, uv, dv, "", f"build-shard-{i}")
        print(f"shard {i} -> job {jid}")
    print(f"\nSubmitted {args.last - args.first + 1} jobs. Track: "
          f"Jobs.getJobsList() or the Compute Jobs UI. Already-built shards skip themselves.")


if __name__ == "__main__":
    main()
