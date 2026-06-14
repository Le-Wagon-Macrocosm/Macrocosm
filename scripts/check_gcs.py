#!/usr/bin/env python3
"""Tiny GCS write probe — used to confirm a SciServer Compute Job can reach GCS.

Compute Jobs run on different infrastructure than interactive containers, and
their outbound-network policy isn't documented. Before mass-submitting build
jobs, run THIS as a one-off job: if it prints 'GCS WRITE OK', jobs can push to
the bucket and we're clear to go.

Usage (inside a job, or interactively):
    python scripts/check_gcs.py /path/to/sciserver-uploader.json
"""
import sys
from google.cloud import storage

key = sys.argv[1]
c = storage.Client.from_service_account_json(key)
blob = c.bucket("macrocosm-lewagon").blob("data/sample_v1/_jobs_egress_test.txt")
blob.upload_from_string("hello from a SciServer compute job")
print("GCS WRITE OK")
blob.delete()
print("cleanup OK")
