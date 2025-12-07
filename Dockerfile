FROM python:3.13-alpine

RUN apk add --no-cache supervisor supervisor-openrc tzdata

ENV TZ=Asia/Ho_Chi_Minh
WORKDIR /app

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

COPY supervisor/supervisord.conf /etc/supervisord.conf
COPY supervisor/conf.d/ /etc/supervisor/conf.d/

# Create /tmp (required for childlogdir)
RUN mkdir -p /tmp && chmod 1777 /tmp

# Wrapper script
RUN echo '#!/bin/sh'                                          > /run-hourly.sh && \
    echo 'while :'                                            >> /run-hourly.sh && \
    echo 'do'                                                 >> /run-hourly.sh && \
    echo '  echo "=== $(date \"+%Y-%m-%d %H:%M:%S %Z\") ==="' >> /run-hourly.sh && \
    echo '  /app/venv/bin/python /app/main.py'                >> /run-hourly.sh && \
    echo '  echo "Cycle completed. Sleeping 3600s..."'        >> /run-hourly.sh && \
    echo '  sleep 3600'                                       >> /run-hourly.sh && \
    echo 'done'                                               >> /run-hourly.sh && \
    chmod +x /run-hourly.sh

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf", "-n"]