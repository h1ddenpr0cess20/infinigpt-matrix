FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1

CMD ["infinigpt-matrix", "--config", "config.json", "--log-level", "INFO"]

