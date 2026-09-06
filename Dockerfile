FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /workspace

COPY requirements.txt .

RUN uv pip install --system -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

CMD ["pytest", "tests/", "-v"]
