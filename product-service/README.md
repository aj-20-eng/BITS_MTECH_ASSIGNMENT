# Product Service

Owns product master data and its SQLite database.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Service listens on http://localhost:5001.

## APIs
- GET /health
- POST /products
- GET /products
- GET /products/{product_id}
