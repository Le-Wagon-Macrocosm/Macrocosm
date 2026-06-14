#!/bin/bash
# VM startup script (runs on first boot via `make mlflow-create`).
# Installs Docker + compose so the stack can be brought up. Does NOT start the
# stack itself — that needs .env (secrets), done once by hand (see README).
set -e
# Docker's official installer — includes the compose plugin. (Ubuntu's repo has
# docker.io but NOT docker-compose-plugin, which made the apt approach fail.)
curl -fsSL https://get.docker.com | sh
apt-get install -y git
systemctl enable --now docker
