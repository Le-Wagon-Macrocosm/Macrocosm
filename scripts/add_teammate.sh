#!/usr/bin/env bash
# Add teammate(s) to the Macrocosm GCP project as Editor.
#
# Usage:  ./scripts/add_teammate.sh alice@gmail.com [bob@gmail.com ...]
# Needs:  gcloud authed as an Owner/Editor of the project (the team lead).
#
# Editor lets them use GCS / Artifact Registry / Cloud Run on the shared project.
# (It's a 2-week throwaway project, so broad-but-simple beats fine-grained here.)
set -euo pipefail

PROJECT="${PROJECT:-macrocosm-lewagon}"
ROLE="${ROLE:-roles/editor}"

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <email> [email2 ...]"
  echo "  Adds each Google account as ${ROLE} on project ${PROJECT}."
  exit 1
fi

for email in "$@"; do
  # cheap sanity check
  if [[ "$email" != *@*.* ]]; then
    echo "  ✗ skipping '$email' — doesn't look like an email"; continue
  fi
  echo "→ adding ${email} as ${ROLE} on ${PROJECT} ..."
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="user:${email}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet >/dev/null
  echo "  ✓ ${email}"
done

echo
echo "Current ${ROLE} members on ${PROJECT}:"
gcloud projects get-iam-policy "$PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.role=${ROLE}" \
  --format="value(bindings.members)" | sort -u | sed 's/^/  /'
