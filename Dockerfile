FROM python:3.13-alpine

RUN apk add --no-cache dcron tzdata && rm -rf /var/cache/apk/*

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

# Virtualenv
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Create empty log file
RUN touch /app/teleshake.log && chmod 666 /app/teleshake.log

# Crontab:
# 1. Appends new run first (never lose the latest output even if tail fails)
# 2. Truncate to last 1000 lines

RUN echo "0 * * * * echo \"=== \$(date) ===\" >> /app/teleshake.log; \\
          /app/venv/bin/python /app/main.py >> /app/teleshake.log 2>&1; \\
          tail -n 1000 /app/teleshake.log > /app/teleshake.tmp && mv /app/teleshake.tmp /app/teleshake.log" > /etc/crontabs/root

# Start cron in foreground
CMD ["crond", "-f", "-l", "2"]

# checks that the log was updated in the last 2 hours
HEALTHCHECK --interval=30s --timeout=5s \
    CMD find /app/teleshake.log -mmin -120 | grep . || exit 1