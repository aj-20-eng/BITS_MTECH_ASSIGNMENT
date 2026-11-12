# Inventory Management System – SE ZG583

Two independently deployable Flask microservices:
- `product-service`: product catalogue and `products.db`
- `inventory-service`: stock balances/movements and `inventory.db`

Inventory Service synchronously calls Product Service over REST to validate products before stock movements.

## Local setup
Use two terminals. Install each service's requirements separately.

Terminal 1:
```bash
cd product-service
pip install -r requirements.txt
python app.py
```

Terminal 2:
```bash
cd inventory-service
pip install -r requirements.txt
# Set PRODUCT_SERVICE_URL=http://localhost:5001
python app.py
```

## Sample API sequence
1. POST `http://localhost:5001/products`
```json
{"sku":"SKU-001","name":"Industrial Bearing","description":"Warehouse item","unit_price":1250}
```
2. POST `http://localhost:5002/stock/receive`
```json
{"product_id":1,"quantity":100}
```
3. GET `http://localhost:5002/stock/1`
4. POST `http://localhost:5002/stock/issue`
```json
{"product_id":1,"quantity":15}
```
5. GET `http://localhost:5002/movements/1`

Use your actual returned product ID rather than assuming it is 1.

## Inventory dashboard (MVP)
Start both services, then open http://localhost:5002 in your browser.
The dashboard supports product creation, stock receiving, stock issuing, stock overview, low-stock highlighting (10 units or fewer), and recent movement history.

Additional inventory endpoint:
- GET `/api/inventory` – combined product catalogue and stock summary.

The Inventory Service proxies product creation through POST `/api/products` so the browser dashboard can remain on one origin.
