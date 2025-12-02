FROM python:3.13.7-slim

WORKDIR /usr/src/app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV ENV=dev
ENV SECRET_KEY=changeme123
ENV BASE_URL=http://localhost:5000
ENV FRONTEND_URL=http://localhost:5173

ENV MWO_BASE_URL=https://meta.wikimedia.org/w
ENV CONSUMER_KEY=2c0cadd0de785d972762c3bed8665043
ENV CONSUMER_SECRET=325f89a61315b162c120b17a34a26865d58ffbb3

CMD ["python", "app.py"]