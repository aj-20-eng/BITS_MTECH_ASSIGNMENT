import os
from flask import Flask, request, jsonify
from database import init_db, get_db

app = Flask(__name__)
init_db()

@app.get("/health")
def health():
    return jsonify({"service": "product-service", "status": "UP"}), 200

@app.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}
    required = ["sku", "name"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    try:
        price = float(data.get("unit_price", 0))
        if price < 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "unit_price must be a non-negative number"}), 400

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO products (sku, name, description, unit_price) VALUES (?, ?, ?, ?)",
            (data["sku"], data["name"], data.get("description", ""), price)
        )
        db.commit()
        product_id = cur.lastrowid
        row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return jsonify(dict(row)), 201
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"error": "SKU already exists"}), 409
        return jsonify({"error": "Could not create product"}), 500
    finally:
        db.close()

@app.get("/products")
def list_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()
    db.close()
    return jsonify([dict(row) for row in rows]), 200

@app.get("/products/<int:product_id>")
def get_product(product_id):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    db.close()
    if row is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(dict(row)), 200


@app.put("/products/<int:product_id>")
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    allowed = {"sku", "name", "description", "unit_price"}
    updates = {key: data[key] for key in allowed if key in data}
    if not updates:
        return jsonify({"error": "Provide at least one field to update"}), 400
    if "unit_price" in updates:
        try:
            updates["unit_price"] = float(updates["unit_price"])
            if updates["unit_price"] < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify({"error": "unit_price must be a non-negative number"}), 400
    db = get_db()
    try:
        current = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if current is None:
            return jsonify({"error": "Product not found"}), 404
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values()) + [product_id]
        db.execute(f"UPDATE products SET {assignments} WHERE id = ?", values)
        db.commit()
        updated = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return jsonify(dict(updated)), 200
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"error": "SKU already exists"}), 409
        return jsonify({"error": "Could not update product"}), 500
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
