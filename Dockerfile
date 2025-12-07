FROM python:3.13-alpine

# Only supervisord (no dumb-init needed anymore)
RUN apk add --no-cache supervisor tzdata

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

# Virtualenv
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Copy file supervisord.conf
COPY supervisord.conf /etc/supervisord.conf

# Start supervisord in foreground
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf", "-n"]