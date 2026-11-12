import os
import json
import urllib.error
import urllib.request

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:5001")

def _request(path, method="GET", payload=None):
    url = f"{PRODUCT_SERVICE_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            body = response.read().decode("utf-8")
            return (json.loads(body) if body else {}), response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return json.loads(body), exc.code
        except json.JSONDecodeError:
            return {"error": "Product Service HTTP error"}, exc.code
    except Exception as exc:
        return {"error": str(exc)}, 503

def fetch_product(product_id):
    return _request(f"/products/{product_id}")

def fetch_products():
    return _request("/products")

def create_product(payload):
    return _request("/products", method="POST", payload=payload)
