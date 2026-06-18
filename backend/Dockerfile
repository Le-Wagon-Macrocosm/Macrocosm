# TODO (task 12): containerize the API. Steps:
#   FROM a slim python base ; WORKDIR /app
#   COPY backend/requirements.txt and pip install it
#   COPY backend/ and BOTH models/*.pkl
#   ENV BASELINE_PATH / IMAGE_MODEL_PATH
#   EXPOSE 8000 ; CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ; RUN pip install -r requirements.txt
COPY backend/  and  models/baseline_stack.pkl  and  models/fake_image_model.pkl
ENV BASELINE_PATH=models/baseline_stack.pkl IMAGE_MODEL_PATH=models/fake_image_model.pkl
EXPOSE 8000 ; CMD ["uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
