FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ gdb \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/data

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=9000
EXPOSE ${PORT}

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
