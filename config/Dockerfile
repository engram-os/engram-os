FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. A container escape or RCE vulnerability as root
# maps to host root on Linux — a non-root user breaks that escalation path.
#
# Pre-create volume mountpoints owned by engram so that Docker initialises
# named volumes (audit_data → /audit, audit_socket → /tmp/audit) with the
# correct ownership on first run, avoiding the need for user: root in compose.
RUN useradd --uid 1001 --no-create-home --shell /bin/false engram \
    && mkdir -p /audit /tmp/audit \
    && chown -R engram:engram /app /audit /tmp/audit
USER engram

CMD ["uvicorn", "core.brain:app", "--host", "0.0.0.0", "--port", "8000"]