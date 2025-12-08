FROM python:3.13-alpine

# OpenRC + tools
RUN apk add --no-cache openrc tzdata && \
    rm -rf /var/cache/apk/*

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

# Virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy service files
COPY scripts/teleshake.sh /app/scripts/teleshake.sh
COPY init.d/teleshake     /etc/init.d/teleshake
COPY entrypoint.sh        /entrypoint.sh

# Make executable
RUN chmod +x /app/scripts/teleshake.sh \
             /etc/init.d/teleshake \
             /entrypoint.sh

# OpenRC runtime dirs
RUN mkdir -p /run/openrc && touch /run/openrc/softlevel

# Default loop interval (can be overridden at runtime)
ENV LOOP_SECONDS=3600

ENTRYPOINT ["/entrypoint.sh"]