# ISI: Inteligentne Systemy Internetowe, laby 1–3

Repozytorium z rozwiązaniami labów 1–3 i materiałami na checkpoint CP-1 (moduł 01: rekomendacje).

| Katalog | Co zawiera |
|---|---|
| `lab1/app.py` | product-service: katalog 5 produktów przez REST API (Flask) |
| `lab2/` | content-based: `movies.csv` (24 filmy), `recommender.py` (TF-IDF + cosine), `app.py` (API) |
| `lab3/` | collaborative filtering: `ratings.csv` (182 oceny), `recommender.py`, `app.py`, `wlasna_proba.py` |
| `check_all.py` | sprawdza kontrakt API wszystkich labów (Flask `test_client`, bez serwera) |
| `prezentacja/` | slajdy CP-1 (`CP1_rekomendacje.pptx`) i skrypt, który je buduje |

## Jak uruchomić (Windows CMD)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

W PowerShellu zamiast `activate` użyj `.\venv\Scripts\Activate.ps1`. Jeśli execution policy blokuje skrypt, najpierw wpisz `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Każdy lab uruchamiasz z jego katalogu. Serwer wstaje na http://127.0.0.1:5000:

```bat
cd lab3
python recommender.py   & rem szybki test silnika bez serwera
python app.py           & rem serwer API
```

Testy z katalogu głównego:

```bat
python check_all.py
```

`check_all.py` uruchamia też oryginalne `test_lab01.py` i `test_lab03.py` z kursu, jeśli obok leży katalog `_kurs-referencja/`. Do tego potrzebny jest `pip install pytest` (narzędzie deweloperskie, spoza `requirements.txt`).

## Lab 1: product-service

| Endpoint | Odpowiedź |
|---|---|
| `GET /api/health` | `200 {"status": "ok"}` |
| `GET /api/products` | `200`, lista 5 produktów |
| `GET /api/products?max_price=200` | produkty z ceną ≤ 200; brak liczby, liczba ujemna, `nan` lub `inf` dają `400` z JSON-em |
| `GET /api/products/<id>` | `200` produkt; `404 {"error": "not found"}`; `/api/products/abc` daje 404 już w routerze |
| `POST /api/products` | `201` i produkt z id nadanym przez serwer; błędne wejście daje `400 {"error": ...}` bez zmiany katalogu |

Walidacja POST: ciało musi być obiektem JSON (tablica, `null` i niepoprawny JSON dają 400) i nie może zawierać `id`. `nazwa`, `kategoria` i `opis` muszą być niepustymi napisami, a `cena` skończoną liczbą ≥ 0, która nie jest napisem ani boolem.

## Moduł 01: rekomendacje (laby 2 i 3)

### Lab 2: content-based (film ↔ film)

`recommender.py` zamienia opisy filmów w wektory TF-IDF (`TfidfVectorizer(stop_words="english")`, macierz 24 × 237) i liczy między nimi podobieństwo kosinusowe (24 × 24). `recommend(title, top_n=5, genre=None)` zwraca najbardziej podobne filmy, bez filmu z zapytania.

| Endpoint | Odpowiedź |
|---|---|
| `GET /api/recommend?title=Inception` | `200`, top 5 z polami `title`, `genres`, `rating`, `score` |
| `&top_n=` | tylko liczba całkowita 1–10; `0`, `11`, pusty i `abc` dają `400` |
| `&genre=action` | wyniki tylko z tego gatunku (bez względu na wielkość liter) |
| brak `title` | `400` |
| nieznany tytuł | `404` z listą `did_you_mean` (difflib), np. `Incepton` daje `["Inception"]` |
| `GET /api/movies` | lista 24 filmów |

Kontrola: `?title=Inception&top_n=2` zwraca Blade Runner 2049 (0.091) i The Dark Knight (0.063).

### Lab 3: collaborative filtering (człowiek ↔ człowiek)

`recommender.py` nie czyta opisów, tylko oceny:

1. **pivot**: `ratings.csv` zamieniamy w macierz 12 osób × 24 filmy. Wypełnienie wynosi 63%, a NaN oznacza brak oceny, nie zero.
2. **centrowanie**: od ocen każdej osoby odejmujemy jej średnią, a dopiero potem braki zamieniamy na 0.
3. **cosine odchyleń** między osobami daje macierz podobieństw 12 × 12.
4. **głosowanie k sąsiadów** dla każdego filmu, którego użytkownik nie ocenił:

```
predicted(u, f) = mean(u) + Σ sim(u,v)·(r(v,f) − mean(v)) / Σ |sim(u,v)|
```

Sumy biegną tylko po sąsiadach, którzy ocenili film, więc dzielimy przez ich Σ|sim|, a nie przez k. Wynik obcinamy do skali 1–5. Pole `because` pokazuje sąsiadów, którzy brali udział w obliczeniu.

| Endpoint | Odpowiedź |
|---|---|
| `GET /api/recommend?user=Ania` | `200`, top 5 nieocenionych filmów: `title`, `predicted`, `because` |
| `&k=` | liczba sąsiadów, domyślnie 3, dozwolone 1–11; inna wartość daje `400` |
| `&top_n=` | 1–10, domyślnie 5 |
| brak `user` | `400` |
| nieznany user | `404` z listą `known_users` |
| `GET /api/users` | 12 użytkowników |
| `GET /api/similar?user=Ania` | 3 najbardziej podobne osoby z podobieństwem |

**Przykładowa odpowiedź** `GET /api/recommend?user=Ania`:

```json
{
  "count": 5,
  "k": 3,
  "recommendations": [
    {"because": ["Celina", "Jacek", "Kasia"], "predicted": 4.31, "title": "Fight Club"},
    {"because": ["Celina"], "predicted": 3.08, "title": "Forrest Gump"},
    {"because": ["Celina", "Jacek", "Kasia"], "predicted": 2.37, "title": "Toy Story"},
    {"because": ["Kasia"], "predicted": 2.24, "title": "The Shawshank Redemption"},
    {"because": ["Celina", "Jacek", "Kasia"], "predicted": 2.13, "title": "Spirited Away"}
  ],
  "user": "Ania"
}
```

`GET /api/recommend?user=Zzz` zwraca `404`:

```json
{"error": "nie znam takiego użytkownika", "known_users": ["Ania", "Bartek", "Celina", "Daria", "Ewa", "Filip", "Gosia", "Hubert", "Iga", "Jacek", "Kasia", "Leon"]}
```

Ania oceniła 19 z 24 filmów, więc lista nigdy nie będzie dłuższa niż 5 pozycji.

**Wyzwanie: wpływ k** (Ania, wynik `python recommender.py`):

| k | top rekomendacje |
|---|---|
| 1 | Fight Club 4.08, Forrest Gump 3.08, Toy Story 3.08, Spirited Away 2.08 (tylko 4: sama Celina nie oceniła Shawshank) |
| 3 | Fight Club 4.31, Forrest Gump 3.08, Toy Story 2.37, Shawshank 2.24, Spirited Away 2.13 |
| 10 | Fight Club 3.85, Forrest Gump 2.95, Shawshank 2.60, Toy Story 2.52, Spirited Away 2.31 |

Większe k nie musi przesuwać wyników w jedną stronę. Dochodzą sąsiedzi o niższej lub ujemnej wadze i innych odchyleniach.

**Extra C: ewaluacja.** `evaluate("Ania")` ukrywa 3 losowe oceny Ani (`seed=42`), przelicza średnie, centrowanie i podobieństwa na macierzy BEZ nich, a potem porównuje przewidywania z prawdą:

| Ukryty film | Prawda | Przewidywanie |
|---|---|---|
| A Quiet Place | 4 | 4.61 |
| Inception | 4 | 4.03 |
| The Dark Knight | 3 | 4.18 |

MAE = 0.607, pokrycie 3/3. Brakującej predykcji nie liczymy jako zera: obniża ona pokrycie, a nie wpływa na MAE.

## Własna próba (lab 3)

**Zmiana:** Ania zmienia ocenę *Parasite* z 5 na 2. Przeliczenie robi `lab3/wlasna_proba.py` na kopii danych w pamięci, więc `ratings.csv` się nie zmienia (sprawdzone sumą md5 przed i po). Pełny wynik jest w `lab3/wlasna_proba.json`.

**Moje przewidywanie (przed uruchomieniem):** _do uzupełnienia własnoręcznie_

| | Przed (Parasite = 5) | Po (Parasite = 2) |
|---|---|---|
| Średnia Ani | 3.368 | 3.211 |
| Sąsiedzi (k=3) | Celina 0.511, Jacek 0.433, Kasia 0.204 | Celina 0.542, **Bartek 0.377**, Jacek 0.305 |
| Top 1 | Fight Club 4.31 (Celina, Jacek, Kasia) | Fight Club 4.11 (Celina, Jacek) |
| Top 2 | Forrest Gump 3.08 (Celina) | Forrest Gump 2.92 (Celina) |
| Top 3 | Toy Story 2.37 (Celina, Jacek, Kasia) | Toy Story 2.39 (Celina, Jacek) |
| Top 4 | The Shawshank Redemption 2.24 (Kasia) | Spirited Away 2.11 (Celina, Jacek) |
| Top 5 | Spirited Away 2.13 (Celina, Jacek, Kasia) | (brak: nikt z sąsiadów nie ocenił Shawshank) |

**Dlaczego tak wyszło:**

1. **Zmienia się średnia.** Ania ma 19 ocen, więc spadek o 3 punkty obniża jej średnią o 3/19 ≈ 0.158 (3.368 → 3.211).
2. **Zmieniają się odchylenia.** Odchylenie przy Parasite spada z +1.63 do −1.21. Odchylenia przy pozostałych 18 filmach rosną o 0.158, bo odejmujemy mniejszą średnią. Zmienia się więc cały wektor Ani, a nie jedna liczba.
3. **Zmieniają się podobieństwa i skład sąsiadów.** Jacek (odchylenie przy Parasite +1.24) i Kasia (+0.87) lubili Parasite bardziej niż zwykle. Wcześniej zgadzało się to z Anią, teraz jest przeciwnie, więc ich podobieństwo spada (0.433 → 0.305, 0.204 → 0.101). Bartek ocenił Parasite poniżej swojej średniej (−0.92), więc teraz zgadza się z Anią i jego podobieństwo rośnie z 0.150 do 0.377. Bartek wchodzi do trójki, a Kasia z niej wypada. Celina nie oceniła Parasite, ale jej podobieństwo i tak lekko rośnie (0.511 → 0.542), bo zmieniła się średnia Ani i norma jej wektora.
4. **Zmieniają się rekomendacje.** Wszystkie przewidywania startują od niższej średniej Ani. *Fight Club* traci głos Kasi, a Bartek go nie ocenił, więc wynik spada z 4.31 do 4.11. *The Shawshank Redemption* oceniła tylko Kasia, więc po jej wypadnięciu nikt z sąsiadów nie ma oceny: Σ|sim| = 0 i film znika z listy. Ania nadal ma 5 nieocenionych filmów, ale model przewiduje tylko 4. *Toy Story* lekko rośnie (2.37 → 2.39), bo zniknął niski głos Kasi (2 przy średniej 3.13).

## Narzędzia

Python 3.13, Flask, pandas, scikit-learn i numpy (wersje w `requirements.txt`). Prezentację buduje `prezentacja/build_slides.py` (`pip install python-pptx`).
