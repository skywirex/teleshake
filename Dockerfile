FROM python:3.13-alpine

# Only supervisor + tzdata
RUN apk add --no-cache supervisor tzdata

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

# Virtualenv
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy supervisord configs (clean & readable)
COPY supervisor/supervisord.conf /etc/supervisord.conf
COPY supervisor/conf.d/ /etc/supervisor/conf.d/

# Create the hourly wrapper script
RUN echo '#!/bin/sh'                                          > /run-hourly.sh && \
    echo 'while true; do'                                      >> /run-hourly.sh && \
    echo '  echo "=== $(date \"+%Y-%m-%d %H:%M:%S %Z\") ==="' >> /run-hourly.sh && \
    echo '  /app/venv/bin/python /app/main.py'                >> /run-hourly.sh && \
    echo '  echo "Next run in 1 hour..."'                     >> /run-hourly.sh && \
    echo '  sleep 3600'                                        >> /run-hourly.sh && \
    echo 'done'                                                >> /run-hourly.sh && \
    chmod +x /run-hourly.sh

# Start supervisord in foreground
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf", "-n"]