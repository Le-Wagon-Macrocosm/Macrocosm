# MLflow tracking server (GCP VM)

Shared MLflow server, gated by **GitHub-org login**. Stack: `Caddy (auto-HTTPS) → oauth2-proxy (GitHub org) → mlflow`. Full guide: KB **MCM-A-14 "MLflow tracking server"**.

## One-time setup
```bash
# from Macrocosm/ — reserve static IP + create the VM + open 80/443
make mlflow-create
make mlflow-url           # note the https://<ip>.sslip.io URL

# create a NEW GitHub OAuth App in the org:
#   Homepage:  https://<ip>.sslip.io
#   Callback:  https://<ip>.sslip.io/oauth2/callback
# then on the VM:
gcloud compute ssh macrocosm-mlflow --zone europe-west1-b
sudo git clone https://github.com/Le-Wagon-Macrocosm/Macrocosm.git
cd Macrocosm/mlflow
sudo cp .env.example .env && sudo nano .env      # fill GH_*, COOKIE_SECRET, HOST
sudo docker compose up -d
```
The VM's service account writes artifacts to `gs://macrocosm-lewagon/mlflow` (no key needed).

## Daily
```bash
make mlflow-start    # start the VM; containers auto-restart (~a few min to be ready)
make mlflow-stop     # stop the VM (compute billing pauses; IP + run data kept)
```

## Use it (Colab / local)
```python
import os; os.environ["MLFLOW_TRACKING_URI"] = "https://<ip>.sslip.io"
# browser opens GitHub login on first use; only org members get in
```

## Before deleting the VM
Back up the run database (artifacts are already in GCS):
```bash
sudo docker run --rm -v mlflow_mlflow-data:/d -v /tmp:/out alpine cp /d/mlflow.db /out/
gcloud storage cp /tmp/mlflow.db gs://macrocosm-lewagon/mlflow/mlflow.db
```
View later with no server: `mlflow ui --backend-store-uri sqlite:///mlflow.db`.
