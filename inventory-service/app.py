import os
from flask import Flask, request, jsonify, render_template
from database import init_db, get_db
from product_client import fetch_product, fetch_products, create_product

app = Flask(__name__)
init_db()


@app.get("/")
def dashboard():
    return render_template("index.html")

@app.get("/api/inventory")
def inventory_overview():
    products, status = fetch_products()
    if status != 200:
        return jsonify({"error": "Could not load products from Product Service", "details": products}), 503
    db = get_db()
    rows = db.execute("SELECT product_id, quantity FROM stock").fetchall()
    db.close()
    stock_by_product = {row["product_id"]: row["quantity"] for row in rows}
    result = []
    for product in products:
        product_id = product["id"]
        quantity = stock_by_product.get(product_id, 0)
        result.append({
            **product,
            "quantity": quantity,
            "stock_status": "OUT_OF_STOCK" if quantity == 0 else ("LOW_STOCK" if quantity <= 10 else "IN_STOCK")
        })
    return jsonify({
        "total_products": len(result),
        "total_units": sum(item["quantity"] for item in result),
        "low_stock_count": sum(1 for item in result if item["stock_status"] == "LOW_STOCK"),
        "out_of_stock_count": sum(1 for item in result if item["stock_status"] == "OUT_OF_STOCK"),
        "items": result
    }), 200

@app.post("/api/products")
def api_create_product():
    data = request.get_json(silent=True) or {}
    product, status = create_product(data)
    return jsonify(product), status

@app.get("/health")
def health():
    return jsonify({"service": "inventory-service", "status": "UP"}), 200

@app.post("/stock/receive")
def receive_stock():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    if product_id is None or quantity is None:
        return jsonify({"error": "product_id and quantity are required"}), 400
    try:
        product_id, quantity = int(product_id), int(quantity)
        if quantity <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "product_id and quantity must be positive integers"}), 400

    product, status = fetch_product(product_id)
    if status == 404:
        return jsonify({"error": "Product does not exist", "product_id": product_id}), 404
    if status != 200:
        return jsonify({"error": "Product Service is unavailable", "details": product}), 503

    db = get_db()
    try:
        db.execute("""
            INSERT INTO stock (product_id, quantity)
            VALUES (?, ?)
            ON CONFLICT(product_id) DO UPDATE SET quantity = quantity + excluded.quantity
        """, (product_id, quantity))
        db.execute(
            "INSERT INTO movements (product_id, movement_type, quantity) VALUES (?, 'RECEIVE', ?)",
            (product_id, quantity)
        )
        db.commit()
        row = db.execute("SELECT product_id, quantity FROM stock WHERE product_id = ?", (product_id,)).fetchone()
        return jsonify({"message": "Stock received", "product": product, "stock": dict(row)}), 201
    finally:
        db.close()

@app.post("/stock/issue")
def issue_stock():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    if product_id is None or quantity is None:
        return jsonify({"error": "product_id and quantity are required"}), 400
    try:
        product_id, quantity = int(product_id), int(quantity)
        if quantity <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "product_id and quantity must be positive integers"}), 400

    product, status = fetch_product(product_id)
    if status == 404:
        return jsonify({"error": "Product does not exist", "product_id": product_id}), 404
    if status != 200:
        return jsonify({"error": "Product Service is unavailable", "details": product}), 503

    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT quantity FROM stock WHERE product_id = ?", (product_id,)).fetchone()
        available = row["quantity"] if row else 0
        if available < quantity:
            db.rollback()
            return jsonify({"error": "Insufficient stock", "available_quantity": available}), 409
        db.execute("UPDATE stock SET quantity = quantity - ? WHERE product_id = ?", (quantity, product_id))
        db.execute(
            "INSERT INTO movements (product_id, movement_type, quantity) VALUES (?, 'ISSUE', ?)",
            (product_id, quantity)
        )
        db.commit()
        updated = db.execute("SELECT product_id, quantity FROM stock WHERE product_id = ?", (product_id,)).fetchone()
        return jsonify({"message": "Stock issued", "product": product, "stock": dict(updated)}), 200
    finally:
        db.close()

@app.get("/stock/<int:product_id>")
def get_stock(product_id):
    db = get_db()
    row = db.execute("SELECT product_id, quantity FROM stock WHERE product_id = ?", (product_id,)).fetchone()
    db.close()
    if row is None:
        return jsonify({"product_id": product_id, "quantity": 0}), 200
    return jsonify(dict(row)), 200

@app.get("/movements/<int:product_id>")
def get_movements(product_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, product_id, movement_type, quantity, created_at FROM movements WHERE product_id = ? ORDER BY id DESC",
        (product_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(row) for row in rows]), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5002")))
