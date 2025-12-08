FROM python:3.13-alpine

# Only tzdata needed
RUN apk add --no-cache tzdata

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

# Create virtualenv
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Copy and make script executable
COPY scripts/teleshake.sh /app/scripts/teleshake.sh
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /app/scripts/teleshake.sh /entrypoint.sh

# Default loop: 1 hour
ENV LOOP_SECONDS=3600

# Run our simple entrypoint
ENTRYPOINT ["/entrypoint.sh"]