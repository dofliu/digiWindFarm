# ── Backend Dockerfile ──
# Python FastAPI backend + Wind Farm Simulator
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (caching layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY run.py .
COPY wind_model.py .
COPY common_types.py .
COPY server/ server/
COPY simulator/ simulator/

# Default environment
ENV BACKEND_PORT=8100
ENV BACKEND_HOST=0.0.0.0
ENV MODBUS_PORT=5020

EXPOSE 8100 5020

CMD ["python", "run.py"]
