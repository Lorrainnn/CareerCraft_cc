FROM python:3.12-slim

WORKDIR /workspace

# System deps for some rendering/ocr libs (kept minimal for now).
# Further libs for PDF/DOCX can be added in later migration steps.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

