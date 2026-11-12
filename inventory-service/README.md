# Inventory Service

Owns stock balances and stock movement history. Calls Product Service over REST to validate product IDs.

## Run locally
Start Product Service first on port 5001, then:
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell:
$env:PRODUCT_SERVICE_URL="http://localhost:5001"
python app.py
```
Service listens on http://localhost:5002.

## APIs
- GET /health
- POST /stock/receive
- POST /stock/issue
- GET /stock/{product_id}
- GET /movements/{product_id}

## Dashboard
Start Product Service and Inventory Service, then open http://localhost:5002. Dashboard is served by Inventory Service.
