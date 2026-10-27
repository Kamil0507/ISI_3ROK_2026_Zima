"""Lab 01 - product-service: katalog produktów wystawiony przez REST API (Flask)."""
import math

from flask import Flask, jsonify, request

app = Flask(__name__)

# Katalog trzymamy w pamięci procesu: restart serwera przywraca 5 rekordów.
PRODUCTS = [
    {"id": 1, "nazwa": "Klawiatura mechaniczna", "kategoria": "akcesoria",
     "cena": 349.99, "opis": "Przełączniki hot-swap, podświetlenie RGB"},
    {"id": 2, "nazwa": "Mysz bezprzewodowa", "kategoria": "akcesoria",
     "cena": 129.00, "opis": "Ciche przyciski, 4000 DPI"},
    {"id": 3, "nazwa": "Monitor 27 cali", "kategoria": "monitory",
     "cena": 1099.00, "opis": "Matryca IPS, 144 Hz"},
    {"id": 4, "nazwa": "Słuchawki nauszne", "kategoria": "audio",
     "cena": 449.00, "opis": "ANC, 40 h pracy na baterii"},
    {"id": 5, "nazwa": "Hub USB-C", "kategoria": "akcesoria",
     "cena": 199.00, "opis": "HDMI, 3x USB-A, czytnik SD"},
]

TEXT_FIELDS = ("nazwa", "kategoria", "opis")


def bad_request(message):
    return jsonify({"error": message}), 400


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/products", methods=["GET"])
def products():
    # Zadanie A: sprawdzamy obecność klucza, bo get(..., type=float) zwraca None
    # zarówno przy braku parametru, jak i przy błędzie konwersji.
    if "max_price" not in request.args:
        return jsonify(PRODUCTS)
    try:
        max_price = float(request.args["max_price"])
    except ValueError:
        return bad_request("max_price musi być liczbą")
    # float() przyjmuje "nan" i "inf" - takie limity też odrzucamy.
    if not math.isfinite(max_price) or max_price < 0:
        return bad_request("max_price musi być skończoną liczbą >= 0")
    return jsonify([p for p in PRODUCTS if p["cena"] <= max_price])


@app.route("/api/products/<int:product_id>")
def product(product_id):
    # <int:...> odrzuca nieliczby już w routerze (404 bez wejścia do funkcji).
    item = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if item is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)


@app.route("/api/products", methods=["POST"])
def create_product():
    # Zadanie C: silent=True zwraca None przy błędnym JSON-ie zamiast HTML-owego 400.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return bad_request("oczekiwano obiektu JSON")
    if "id" in data:
        return bad_request("id nadaje serwer")
    missing = [f for f in (*TEXT_FIELDS, "cena") if f not in data]
    if missing:
        return bad_request(f"brak pól: {', '.join(missing)}")
    for field in TEXT_FIELDS:
        if not isinstance(data[field], str) or not data[field].strip():
            return bad_request(f"{field} musi być niepustym napisem")
    price = data["cena"]
    # bool jest podklasą int w Pythonie, więc wykluczamy go jawnie.
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return bad_request("cena musi być liczbą")
    if not math.isfinite(price) or price < 0:
        return bad_request("cena musi być skończoną liczbą >= 0")

    # Rekord budujemy dopiero po pełnej walidacji, więc błąd nie zmienia katalogu.
    new = {"id": max((p["id"] for p in PRODUCTS), default=0) + 1,
           **{f: data[f].strip() for f in TEXT_FIELDS},
           "cena": price}
    PRODUCTS.append(new)
    return jsonify(new), 201


if __name__ == "__main__":
    app.run(debug=True)
