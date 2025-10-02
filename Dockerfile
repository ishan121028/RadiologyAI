FROM pathwaycom/pathway:latest

WORKDIR /app

RUN apt-get update \
    && apt-get install -y python3-opencv tesseract-ocr-eng libgl1-mesa-dri libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

COPY requirements.txt .
# Install packages one by one with force-reinstall to bypass conflicts
RUN pip install pathway==0.26.2 && \
    pip install agentic-doc==0.3.3 && \
    pip install sentence-transformers python-dotenv pydantic litellm openai pytest

COPY . .

ARG REST_PORT=49001
ARG MCP_PORT=8123
EXPOSE $REST_PORT $MCP_PORT

CMD ["python", "app.py"]