FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY config.py utils.py main.py ./
COPY crawler/ ./crawler/
COPY storage/ ./storage/
COPY search/ ./search/
COPY api/ ./api/

# Copy pre-crawled data (phải crawl trước khi build)
COPY data/ ./data/

EXPOSE 8000

CMD ["python", "main.py", "serve"]
