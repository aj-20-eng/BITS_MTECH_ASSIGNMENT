FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5001 DB_PATH=/data/products.db
EXPOSE 5001
CMD ["python", "app.py"]
