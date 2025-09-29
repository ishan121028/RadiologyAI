FROM pathwaycom/pathway:latest

WORKDIR /app

RUN apt-get update \
    && apt-get install -y python3-opencv tesseract-ocr-eng libgl1-mesa-dri libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY requirements.txt .
RUN pip install -U --no-cache-dir -r requirements.txt

COPY . .

ARG REST_PORT=49001
ARG MCP_PORT=8123
EXPOSE $REST_PORT $MCP_PORT

CMD ["python", "app.py"]