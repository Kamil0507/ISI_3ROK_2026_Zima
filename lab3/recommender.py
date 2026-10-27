"""Lab 03 - collaborative filtering (user-based) na samych ocenach.

Nie czytamy opisów filmów. Szukamy osób o podobnym guście (człowiek <-> człowiek)
i przewidujemy oceny filmów, których użytkownik jeszcze nie ocenił.

Pipeline:
    ratings.csv -> macierz osoby x filmy -> centrowanie średnią osoby
    -> cosine odchyleń między osobami -> ważone głosy k sąsiadów
"""
from pathlib import Path

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

RATINGS_PATH = Path(__file__).resolve().with_name("ratings.csv")


def build_model(ratings):
    """Z tabeli (user, title, rating) liczy macierz, średnie i podobieństwa.

    Osobna funkcja, bo ten sam model przeliczamy na kopii danych
    (własna próba) i na macierzy z ukrytymi ocenami (evaluate).
    """
    # 1. Długa lista par -> macierz: wiersz = osoba, kolumna = film.
    #    NaN = brak oceny (kandydat do polecenia), a NIE ocena 0.
    matrix = ratings.pivot_table(index="user", columns="title", values="rating")
    return model_from_matrix(matrix)


def model_from_matrix(matrix):
    # 2. Centrowanie: od każdej oceny odejmujemy średnią TEJ osoby.
    #    mean(axis=1) liczy średnią wiersza i pomija NaN.
    means = matrix.mean(axis=1)
    #    Dopiero PO odjęciu średniej wstawiamy 0 za braki: 0 = "brak odchylenia",
    #    więc brak oceny nic nie wnosi do iloczynu skalarnego.
    centered = matrix.sub(means, axis=0).fillna(0)

    # 3. Cosine odchyleń każdy z każdym -> macierz 12 x 12, wartości od -1 do 1.
    sim = pd.DataFrame(cosine_similarity(centered),
                       index=matrix.index, columns=matrix.index)
    return matrix, means, sim


# Model z oryginalnego pliku, budowany raz przy imporcie (używa go app.py).
df = pd.read_csv(RATINGS_PATH)
matrix, means, sim = build_model(df)
MAX_K = len(matrix.index) - 1  # najwyżej 11 sąsiadów (wszyscy poza sobą)


def neighbors(user, k=3, model=None):
    """k osób najbardziej podobnych do user (bez niego samego), malejąco."""
    _, _, s = model or (matrix, means, sim)
    return s[user].drop(user).sort_values(ascending=False).head(k)


def similar_users(user, k=3, model=None):
    """Sąsiedzi jako lista słowników do JSON-a; None dla nieznanego usera."""
    m, _, _ = model or (matrix, means, sim)
    if user not in m.index:
        return None
    return [{"user": v, "similarity": round(float(w), 3)}
            for v, w in neighbors(user, k, model).items()]


def predict_all(user, k=3, model=None):
    """Przewidywana ocena każdego NIEOCENIONEGO filmu: {title: (ocena, because)}.

    predicted(u, f) = mean(u) + Σ sim(u,v)·(r(v,f) − mean(v)) / Σ |sim(u,v)|

    Sumy biegną tylko po sąsiadach, którzy ocenili film f. Dlatego dzielimy
    przez Σ|sim| tych osób, a nie przez k: nie każdy sąsiad widział każdy film.
    """
    m, mn, _ = model or (matrix, means, sim)
    nb = neighbors(user, k, model)
    predictions = {}
    for movie in m.columns:
        if not pd.isna(m.loc[user, movie]):
            continue  # film już oceniony -> nie przewidujemy, nie polecamy
        num, den, voters = 0.0, 0.0, []
        for other, weight in nb.items():
            rating = m.loc[other, movie]
            if pd.isna(rating) or weight == 0:
                continue  # sąsiad nie widział filmu albo nie ma wagi
            num += weight * (rating - mn[other])  # głos = waga · odchylenie sąsiada
            den += abs(weight)                    # |sim|: ujemna waga też normalizuje
            voters.append(other)
        if den > 0:  # żaden sąsiad nie ocenił filmu -> brak przewidywania
            pred = mn[user] + num / den
            # clamp: wzór może wyjść poza skalę gwiazdek, ucinamy do 1-5
            predictions[movie] = (max(1.0, min(5.0, pred)), voters)
    return predictions


def recommend(user, top_n=5, k=3, model=None):
    """Top-N nieocenionych filmów z przewidywaną oceną; None dla nieznanego usera."""
    m, _, _ = model or (matrix, means, sim)
    if user not in m.index:
        return None
    preds = predict_all(user, k, model)
    best = sorted(preds.items(), key=lambda x: x[1][0], reverse=True)[:top_n]
    # because = sąsiedzi, którzy ocenili film i mieli niezerową wagę w obliczeniu
    return [{"title": t, "predicted": round(float(p), 2), "because": voters}
            for t, (p, voters) in best]


def evaluate(user="Ania", hidden=None, k=3, seed=42):
    """Extra C: ukrywa 3 oceny usera, przelicza model BEZ nich i mierzy błąd.

    Średnie, centrowanie i sąsiedzi liczą się z macierzy po ukryciu, żeby
    testowe oceny nie przeciekły do modelu. Brak predykcji to nie zero:
    raportujemy pokrycie (ile ukrytych pozycji dostało wynik) osobno od MAE.
    """
    rated = matrix.loc[user].dropna()
    if hidden is None:
        hidden = rated.sample(3, random_state=seed).index.tolist()
    truth = {t: float(rated[t]) for t in hidden}

    masked = matrix.copy()
    masked.loc[user, hidden] = float("nan")       # chowamy oceny testowe
    model = model_from_matrix(masked)             # przeliczenie od zera
    preds = predict_all(user, k, model)

    predicted = {t: round(float(preds[t][0]), 2) if t in preds else None for t in hidden}
    errors = [abs(predicted[t] - truth[t]) for t in hidden if predicted[t] is not None]
    return {"user": user, "k": k, "hidden": truth, "predicted": predicted,
            "mae": round(float(sum(errors) / len(errors)), 3) if errors else None,
            "coverage": f"{len(errors)}/{len(hidden)}"}


if __name__ == "__main__":
    filled = matrix.count().sum() / matrix.size
    print(f"macierz {matrix.shape}, ocen {int(matrix.count().sum())}, wypełnienie {filled:.0%}")
    print(f"\nAnia: średnia {means['Ania']:.2f}, nieocenionych filmów "
          f"{int(matrix.loc['Ania'].isna().sum())}")
    print("sąsiedzi (k=3):", similar_users("Ania"))
    for rec in recommend("Ania"):
        print(f"  {rec['predicted']:.2f}  {rec['title']:<26} <- {', '.join(rec['because'])}")
    print("\nwpływ k:")
    for k in (1, 3, 10):
        print(f"  k={k:<2}", [(r["title"], r["predicted"]) for r in recommend("Ania", k=k)])
    print("\nevaluate:", evaluate())
