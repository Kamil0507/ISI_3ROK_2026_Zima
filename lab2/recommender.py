"""Lab 02 - content-based filtering: polecamy filmy o podobnych opisach (TF-IDF + cosine)."""
import difflib
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ścieżka względem pliku, żeby import działał z dowolnego katalogu roboczego.
df = pd.read_csv(Path(__file__).resolve().with_name("movies.csv"))
df["overview"] = df["overview"].fillna("")

# Każdy opis -> wektor wag słów. stop_words usuwa "the", "a", ... ze słownika.
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(df["overview"])  # (24 filmy, liczba słów)

# Podobieństwo każdy z każdym: macierz 24 x 24, przekątna = 1.
sim_matrix = cosine_similarity(tfidf_matrix)


def find_index(title):
    """Indeks filmu po tytule (bez względu na wielkość liter) albo None."""
    match = df.index[df["title"].str.lower() == title.strip().lower()]
    return match[0] if len(match) else None


def did_you_mean(title, n=3):
    """Podpowiedzi dla literówki: najbliższe tytuły według difflib."""
    lowered = {t.lower(): t for t in df["title"]}
    close = difflib.get_close_matches(title.strip().lower(), lowered, n=n, cutoff=0.5)
    return [lowered[c] for c in close]


def has_genre(genres, genre):
    """Czy napis 'sci-fi|thriller' zawiera dokładnie ten gatunek."""
    return genre.lower() in genres.lower().split("|")


def recommend(title, top_n=5, genre=None):
    """Top-N filmów najbardziej podobnych opisem; None, gdy tytułu nie ma w bazie."""
    idx = find_index(title)
    if idx is None:
        return None
    # Sortujemy malejąco po podobieństwie i pomijamy sam film z zapytania.
    ranked = sorted(enumerate(sim_matrix[idx]), key=lambda x: x[1], reverse=True)
    results = []
    for i, score in ranked:
        if i == idx:
            continue
        if genre and not has_genre(df.at[i, "genres"], genre):
            continue  # filtr gatunku działa przed obcięciem do top_n
        results.append({"title": df.at[i, "title"],
                        "genres": df.at[i, "genres"],
                        "rating": round(float(df.at[i, "rating"]), 1),
                        "score": round(float(score), 3)})
        if len(results) == top_n:
            break
    return results


def all_movies():
    return [{"title": r.title, "genres": r.genres, "rating": float(r.rating)}
            for r in df.itertuples()]


if __name__ == "__main__":
    print("filmy:", df.shape, "| TF-IDF:", tfidf_matrix.shape)
    for rec in recommend("Inception", top_n=5):
        print(f"  {rec['score']:.3f}  {rec['title']}  ({rec['genres']})")
