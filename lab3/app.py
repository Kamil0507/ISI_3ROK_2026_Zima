"""Lab 03 - API rekomendacji collaborative filtering. Logika w recommender.py."""
from flask import Flask, jsonify, request

from recommender import MAX_K, matrix, recommend, similar_users

app = Flask(__name__)


def int_param(name, default, low, high):
    """Parametr całkowity z zakresu [low, high]; None, gdy obecny, ale błędny."""
    if name not in request.args:
        return default
    value = request.args.get(name, type=int)  # "abc" i "" -> None
    return value if value is not None and low <= value <= high else None


def unknown_user():
    return jsonify({"error": "nie znam takiego użytkownika",
                    "known_users": sorted(matrix.index.tolist())}), 404


@app.route("/api/recommend")
def api_recommend():
    user = request.args.get("user", "").strip()
    if not user:
        return jsonify({"error": "podaj parametr ?user=..."}), 400
    k = int_param("k", 3, 1, MAX_K)
    if k is None:
        return jsonify({"error": f"k musi być liczbą całkowitą od 1 do {MAX_K}"}), 400
    top_n = int_param("top_n", 5, 1, 10)
    if top_n is None:
        return jsonify({"error": "top_n musi być liczbą całkowitą od 1 do 10"}), 400

    recs = recommend(user, top_n=top_n, k=k)
    if recs is None:
        return unknown_user()
    return jsonify({"user": user, "k": k, "count": len(recs), "recommendations": recs})


@app.route("/api/users")
def api_users():
    users = sorted(matrix.index.tolist())
    return jsonify({"count": len(users), "users": users})


@app.route("/api/similar")
def api_similar():
    user = request.args.get("user", "").strip()
    if not user:
        return jsonify({"error": "podaj parametr ?user=..."}), 400
    similar = similar_users(user)
    if similar is None:
        return unknown_user()
    return jsonify({"user": user, "similar": similar})


if __name__ == "__main__":
    app.run(debug=True)
