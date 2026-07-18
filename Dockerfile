FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY app ./app
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["mlguard"]
