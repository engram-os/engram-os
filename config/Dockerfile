FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. A container escape or RCE vulnerability as root
# maps to host root on Linux — a non-root user breaks that escalation path.
RUN useradd --uid 1001 --no-create-home --shell /bin/false engram \
    && chown -R engram:engram /app
USER engram

CMD ["uvicorn", "core.brain:app", "--host", "0.0.0.0", "--port", "8000"]