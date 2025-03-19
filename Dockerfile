FROM python:3.13-alpine

WORKDIR /app

RUN python -m venv /app/venv

# Enable venv
ENV PATH="/app/venv/bin:$PATH"

COPY . .

ENV PATH="/app/venv/bin:$PATH"

RUN pip install -r requirements.txt


CMD  ["python", "./main.py"]

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s CMD ps aux | grep '[p]ython' || exit 1