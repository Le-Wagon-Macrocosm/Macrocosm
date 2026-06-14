#!/bin/bash
# VM startup script (runs on first boot via `make mlflow-create`).
# Installs Docker + compose so the stack can be brought up. Does NOT start the
# stack itself — that needs .env (secrets), done once by hand (see README).
set -e
apt-get update
apt-get install -y docker.io docker-compose-plugin git
systemctl enable --now docker
