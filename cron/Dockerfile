FROM python:3.13-slim

WORKDIR /usr/src/cron

RUN apt-get update && apt-get install -y cron && apt-get clean

COPY cron/fetch_and_store_cron.py .

COPY backend/utils.py backend/config.py /usr/src/app/backend/

ENV PYTHONPATH=/usr/src/app

COPY cron/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cron/cronjob /etc/cron.d/monthly-cron
RUN chmod 0644 /etc/cron.d/monthly-cron
RUN crontab /etc/cron.d/monthly-cron

RUN touch /var/log/cron.log

CMD ["sh", "-c", "python fetch_and_store_cron.py && cron -f"]
