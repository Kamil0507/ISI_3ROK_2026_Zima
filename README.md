# ISI: laby 1–3

| Katalog | Co jest w środku |
|---|---|
| `lab1/` | product-service: katalog 5 produktów przez API (Flask) |
| `lab2/` | rekomendacje po opisach filmów (TF-IDF + cosine) |
| `lab3/` | rekomendacje po ocenach ludzi (collaborative filtering) |
| `check_all.py` | testy wszystkich endpointów |

## Jak uruchomić

CMD:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd lab3
python recommender.py
python app.py
```

W PowerShellu wpisuj polecenia osobno, bez `&&`. Aktywację można pominąć: `..\venv\Scripts\python.exe app.py`.

Serwer działa pod http://127.0.0.1:5000. Testy uruchamiasz z katalogu głównego: `python check_all.py` (86/86 PASS).

## Moduł 01: rekomendacje (lab 3)

`recommender.py` robi cztery kroki:

1. Zamienia `ratings.csv` (182 oceny) w macierz 12 osób × 24 filmy. Brak oceny to brak danych, a nie zero.
2. Od ocen każdej osoby odejmuje jej średnią (centrowanie).
3. Liczy podobieństwo kosinusowe między osobami.
4. `recommend(user, top_n=5, k=3)` przewiduje oceny filmów nieocenionych na podstawie k najbardziej podobnych osób:

```
predicted = mean(u) + Σ sim·(ocena sąsiada − jego średnia) / Σ |sim|
```

Wynik jest obcięty do skali 1–5. Pole `because` mówi, którzy sąsiedzi ocenili film.

| Endpoint | Wynik |
|---|---|
| `/api/recommend?user=Ania` | top 5 z `title`, `predicted`, `because` |
| `&k=` | liczba sąsiadów 1–11, domyślnie 3; inna wartość daje 400 |
| brak `user` / nieznany user | 400 / 404 z listą `known_users` |
| `/api/users` | 12 osób |
| `/api/similar?user=Ania` | 3 najbardziej podobne osoby |

**Przykładowa odpowiedź** `GET /api/recommend?user=Ania`:

```json
{
  "user": "Ania", "k": 3, "count": 5,
  "recommendations": [
    {"title": "Fight Club", "predicted": 4.31, "because": ["Celina", "Jacek", "Kasia"]},
    {"title": "Forrest Gump", "predicted": 3.08, "because": ["Celina"]},
    {"title": "Toy Story", "predicted": 2.37, "because": ["Celina", "Jacek", "Kasia"]},
    {"title": "The Shawshank Redemption", "predicted": 2.24, "because": ["Kasia"]},
    {"title": "Spirited Away", "predicted": 2.13, "because": ["Celina", "Jacek", "Kasia"]}
  ]
}
```

Sąsiedzi Ani: Celina 0.511, Jacek 0.433, Kasia 0.204. Ania oceniła 19 z 24 filmów, więc lista ma najwyżej 5 pozycji.

**Porównanie k** (Ania):

| k | Wynik |
|---|---|
| 1 | Fight Club 4.08, Forrest Gump 3.08, Toy Story 3.08, Spirited Away 2.08 (tylko 4 pozycje: sama Celina nie widziała Shawshank) |
| 3 | Fight Club 4.31, Forrest Gump 3.08, Toy Story 2.37, Shawshank 2.24, Spirited Away 2.13 |
| 10 | Fight Club 3.85, Forrest Gump 2.95, Shawshank 2.60, Toy Story 2.52, Spirited Away 2.31 |

Większe k nie przesuwa wyników w jedną stronę, bo dochodzą osoby mniej podobne albo o przeciwnym guście.

**Ewaluacja** (`evaluate()`): ukrywa 3 oceny Ani i przelicza model bez nich. MAE wynosi 0.607, pokrycie 3/3.

## Własna próba

Ania zmienia ocenę *Parasite* z 5 na 2. Liczy to `lab3/wlasna_proba.py` na kopii danych, więc `ratings.csv` się nie zmienia.

**Moje przewidywanie (przed uruchomieniem):** _do uzupełnienia_

| | Przed | Po |
|---|---|---|
| Średnia Ani | 3.368 | 3.211 |
| Sąsiedzi | Celina 0.511, Jacek 0.433, Kasia 0.204 | Celina 0.542, **Bartek 0.377**, Jacek 0.305 |
| Top 5 | Fight Club 4.31, Forrest Gump 3.08, Toy Story 2.37, Shawshank 2.24, Spirited Away 2.13 | Fight Club 4.11, Forrest Gump 2.92, Toy Story 2.39, Spirited Away 2.11 |

**Dlaczego:** średnia Ani spada, więc zmieniają się wszystkie jej odchylenia. Parasite z „hitu” (+1.63) staje się „rozczarowaniem” (−1.21). Jacek i Kasia lubili Parasite, więc są teraz mniej podobni do Ani. Bartek go nie lubił, więc staje się bardziej podobny (0.150 → 0.377) i zastępuje Kasię. Shawshank oceniła tylko Kasia, więc po jej wypadnięciu nikt z sąsiadów nie ma zdania o tym filmie i znika on z listy.

## Laby 1 i 2 w skrócie

- **Lab 1:** `/api/health`, `/api/products`, `/api/products/<id>` (404 gdy brak), filtr `?max_price=` (błędna wartość daje 400) oraz POST z walidacją (201, błędne dane dają 400).
- **Lab 2:** `/api/recommend?title=Inception` z `top_n` 1–10 i filtrem `?genre=`. Nieznany tytuł daje 404 z podpowiedzią `did_you_mean`. `/api/movies` zwraca listę filmów. Dla Inception wychodzi Blade Runner 2049 (0.091) i The Dark Knight (0.063).
