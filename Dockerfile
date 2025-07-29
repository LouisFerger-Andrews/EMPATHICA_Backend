FROM python:3.11-slim

WORKDIR /app

# System deps if needed (sqlite, faiss CPU libs, etc.)
RUN apt-get update && apt-get install -y build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Copy python deps file(s)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy code + data
COPY . .

# Default port your API listens on
ENV PORT=8000

# Start command (adjust to your app)
# Example for FastAPI:
CMD ["python", "src/app/main.py"]
# or: CMD ["uvicorn", "src.app.api:app", "--host", "0.0.0.0", "--port", "8000"]
