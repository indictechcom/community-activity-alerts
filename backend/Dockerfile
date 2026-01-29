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

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]