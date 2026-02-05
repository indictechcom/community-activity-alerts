FROM python:3.13-slim

WORKDIR /usr/src/cron

RUN apt-get update && apt-get install -y cron && apt-get clean

COPY cron/fetch_and_store_cron.py .
COPY cron/fetch_and_store_editors_cron.py .

COPY backend/utils.py backend/config.py /usr/src/app/backend/
COPY backend/alerts /usr/src/app/backend/alerts/

ENV PYTHONPATH=/usr/src/app:/usr/src/app/backend
ENV DB_NAME=community_alerts

COPY cron/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cron/cronjob /etc/cron.d/monthly-cron
RUN chmod 0644 /etc/cron.d/monthly-cron

RUN touch /var/log/cron.log

# only run backfill if SKIP_BACKFILL is not set to "true"
CMD ["sh", "-c", "\
if [ \"$SKIP_BACKFILL\" != \"true\" ]; then \
  python fetch_and_store_cron.py --mode backfill && \
  python fetch_and_store_editors_cron.py --mode backfill; \
fi && \
python /usr/src/app/backend/alerts/community_alerts.py && \
python /usr/src/app/backend/alerts/editor_alerts.py && \
cron -f"]
