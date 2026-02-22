FROM python:3.11-slim

# Install system dependencies
# poppler-utils is required for pdftotext
RUN apt-get update && apt-get install -y \
    poppler-utils \
    nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Gunicorn usually runs on 8000, but we map it)
EXPOSE 5000

ENV FLASK_APP=run.py

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
