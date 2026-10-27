"""Lab 02 - API rekomendacji content-based. Logika ML siedzi w recommender.py."""
from flask import Flask, jsonify, request

from recommender import all_movies, did_you_mean, recommend

app = Flask(__name__)


@app.route("/api/recommend")
def api_recommend():
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify({"error": "podaj parametr ?title=..."}), 400

    # top_n: domyślnie 5; obecny, ale pusty/nieliczbowy/poza 1-10 -> 400.
    top_n = request.args.get("top_n", type=int) if "top_n" in request.args else 5
    if top_n is None or not 1 <= top_n <= 10:
        return jsonify({"error": "top_n musi być liczbą całkowitą od 1 do 10"}), 400

    genre = request.args.get("genre", "").strip() or None
    recs = recommend(title, top_n=top_n, genre=genre)
    if recs is None:
        return jsonify({"error": "nie znam takiego filmu",
                        "did_you_mean": did_you_mean(title)}), 404

    body = {"title": title, "count": len(recs), "recommendations": recs}
    if genre:
        body["genre"] = genre
    return jsonify(body)


@app.route("/api/movies")
def api_movies():
    movies = all_movies()
    return jsonify({"count": len(movies), "movies": movies})


if __name__ == "__main__":
    app.run(debug=True)
