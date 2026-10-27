"""Sprawdza kontrakt API labów 1-3 przez Flask test_client (bez uruchamiania serwera).

Uruchom z katalogu głównego repo:  python check_all.py
Jeśli obok leży _kurs-referencja/, dodatkowo odpala oryginalne test_lab01.py
i test_lab03.py z kursu przeciwko plikom z lab1/ i lab3/.
"""
import importlib
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # polskie znaki także przy przekierowaniu do pliku
ROOT = Path(__file__).resolve().parent
passed = failed = 0


def check(label, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}  {extra}")


def load(lab):
    """Importuje lab/app.py; czyści cache, bo lab2 i lab3 mają moduły o tych samych nazwach."""
    for name in ("app", "recommender"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(ROOT / lab))
    try:
        return importlib.import_module("app"), importlib.import_module("recommender") \
            if (ROOT / lab / "recommender.py").exists() else None
    finally:
        sys.path.pop(0)


# ------------------------------------------------------------------ LAB 1
print("LAB 1 - product-service")
app1, _ = load("lab1")
c = app1.app.test_client()

r = c.get("/api/health")
check("GET /api/health -> 200 {status: ok}", r.status_code == 200 and r.get_json() == {"status": "ok"})
r = c.get("/api/products")
check("GET /api/products -> 5 produktów", r.status_code == 200 and len(r.get_json()) == 5)
r = c.get("/api/products/3")
check("GET /api/products/3 -> 200, id 3", r.status_code == 200 and r.get_json()["id"] == 3)
r = c.get("/api/products/99")
check("GET /api/products/99 -> 404 {error: not found}",
      r.status_code == 404 and r.get_json() == {"error": "not found"})
check("GET /api/products/abc -> 404 (router)", c.get("/api/products/abc").status_code == 404)

r = c.get("/api/products?max_price=200")
check("?max_price=200 -> 2 produkty <= 200",
      r.status_code == 200 and len(r.get_json()) == 2 and all(p["cena"] <= 200 for p in r.get_json()))
check("?max_price=0 -> 200, pusta lista", c.get("/api/products?max_price=0").get_json() == [])
for bad in ("abc", "", "-5", "nan", "NaN", "inf", "-inf"):
    r = c.get(f"/api/products?max_price={bad}")
    check(f"?max_price={bad!r} -> 400 JSON", r.status_code == 400 and r.is_json and "error" in r.get_json())

before = c.get("/api/products").get_json()
valid = {"nazwa": "Kabel HDMI", "kategoria": "akcesoria", "cena": 49.0, "opis": "2 m"}
bad_bodies = {
    "tablica zamiast obiektu": [valid],
    "pusty obiekt": {},
    "null": None,
    "id od klienta": {**valid, "id": 1},
    "brak pola opis": {k: v for k, v in valid.items() if k != "opis"},
    "pusta nazwa": {**valid, "nazwa": "   "},
    "kategoria nie napis": {**valid, "kategoria": 5},
    "pusty opis": {**valid, "opis": ""},
    "cena ujemna": {**valid, "cena": -1},
    "cena jako napis": {**valid, "cena": "10"},
    "cena bool": {**valid, "cena": True},
    "cena NaN": {**valid, "cena": float("nan")},
    "cena inf": {**valid, "cena": float("inf")},
    "cena null": {**valid, "cena": None},
}
for label, body in bad_bodies.items():
    r = c.post("/api/products", json=body)
    check(f"POST {label} -> 400 JSON", r.status_code == 400 and r.is_json, r.status_code)
r = c.post("/api/products", data="{", content_type="application/json")
check("POST błędny JSON -> 400 JSON", r.status_code == 400 and r.is_json)
r = c.post("/api/products", data="nazwa=x", content_type="text/plain")
check("POST bez JSON-a -> 400 JSON", r.status_code == 400 and r.is_json)
check("błędne POST-y nie zmieniły katalogu", c.get("/api/products").get_json() == before)

r = c.post("/api/products", json=valid)
check("POST poprawny -> 201, id 6 nadane przez serwer",
      r.status_code == 201 and r.get_json()["id"] == 6 and r.get_json()["nazwa"] == "Kabel HDMI")
check("GET /api/products/6 po POST -> 200", c.get("/api/products/6").status_code == 200)
r = c.post("/api/products", json={**valid, "cena": 0})
check("POST cena 0 (int) -> 201, id 7", r.status_code == 201 and r.get_json()["id"] == 7)

# ------------------------------------------------------------------ LAB 2
print("\nLAB 2 - content-based")
app2, rec2 = load("lab2")
c = app2.app.test_client()

check("movies.csv ma 24 filmy", len(rec2.df) == 24)
check("TF-IDF ma kształt (24, 237)", rec2.tfidf_matrix.shape == (24, 237), rec2.tfidf_matrix.shape)
r = c.get("/api/recommend?title=Inception&top_n=2")
recs = r.get_json()["recommendations"]
check("Inception top_n=2 -> Blade Runner 2049 0.091, The Dark Knight 0.063",
      r.status_code == 200 and [(x["title"], x["score"]) for x in recs]
      == [("Blade Runner 2049", 0.091), ("The Dark Knight", 0.063)], recs)
r = c.get("/api/recommend?title=Inception")
check("domyślnie 5 wyników, bez samego Inception",
      r.get_json()["count"] == 5 and all(x["title"] != "Inception" for x in r.get_json()["recommendations"]))
check("tytuł bez względu na wielkość liter", c.get("/api/recommend?title=inception").status_code == 200)
check("brak title -> 400", c.get("/api/recommend").status_code == 400)
check("pusty title -> 400", c.get("/api/recommend?title=%20").status_code == 400)
r = c.get("/api/recommend?title=Incepton")
check("nieznany tytuł -> 404 z did_you_mean",
      r.status_code == 404 and "Inception" in r.get_json().get("did_you_mean", []), r.get_json())
for n, code in (("1", 200), ("10", 200), ("0", 400), ("11", 400), ("", 400), ("abc", 400), ("-1", 400), ("2.5", 400)):
    check(f"top_n={n!r} -> {code}", c.get(f"/api/recommend?title=Inception&top_n={n}").status_code == code)
r = c.get("/api/recommend?title=Inception&genre=action&top_n=3")
recs = r.get_json()["recommendations"]
check("?genre=action -> 3 wyniki, każdy z gatunkiem action",
      r.status_code == 200 and len(recs) == 3 and all("action" in x["genres"].split("|") for x in recs))
r = c.get("/api/recommend?title=Inception&genre=Horror")
check("?genre=Horror (wielkość liter bez znaczenia)",
      all("horror" in x["genres"].split("|") for x in r.get_json()["recommendations"]))
r = c.get("/api/movies")
check("GET /api/movies -> 24 filmy", r.status_code == 200 and r.get_json()["count"] == 24)

# ------------------------------------------------------------------ LAB 3
print("\nLAB 3 - collaborative filtering")
app3, rec3 = load("lab3")
c = app3.app.test_client()

m = rec3.matrix
check("macierz 12 x 24, 182 oceny", m.shape == (12, 24) and int(m.count().sum()) == 182)
check("wypełnienie 63%", round(m.count().sum() / m.size * 100) == 63)
check("sim symetryczna, przekątna 1",
      all(math.isclose(rec3.sim.loc[u, u], 1.0) for u in m.index)
      and (rec3.sim - rec3.sim.T).abs().max().max() < 1e-12)
check("sąsiedzi Ani k=3: Celina 0.511, Jacek 0.433, Kasia 0.204",
      rec3.similar_users("Ania") == [{"user": "Celina", "similarity": 0.511},
                                     {"user": "Jacek", "similarity": 0.433},
                                     {"user": "Kasia", "similarity": 0.204}],
      rec3.similar_users("Ania"))

r = c.get("/api/recommend?user=Ania")
data = r.get_json()
recs = data["recommendations"]
check("/api/recommend?user=Ania -> 200, top-1 Fight Club 4.31",
      r.status_code == 200 and recs[0]["title"] == "Fight Club" and recs[0]["predicted"] == 4.31, recs[:1])
check("Ania ma 5 nieocenionych -> dokładnie 5 wyników",
      int(m.loc["Ania"].isna().sum()) == 5 and data["count"] == 5)
check("k domyślnie 3", data["k"] == 3)
check("każda pozycja ma title/predicted/because", all({"title", "predicted", "because"} <= set(x) for x in recs))
check("polecamy tylko nieocenione",
      all(math.isnan(m.loc["Ania", x["title"]]) for x in recs))
check("wynik malejąco", [x["predicted"] for x in recs] == sorted((x["predicted"] for x in recs), reverse=True))
check("Ania top_n=10 nadal 5 (więcej nieocenionych nie ma)",
      c.get("/api/recommend?user=Ania&top_n=10").get_json()["count"] == 5)
check("because ⊆ sąsiedzi, którzy ocenili film",
      all(set(x["because"]) <= {"Celina", "Jacek", "Kasia"}
          and all(not math.isnan(m.loc[v, x["title"]]) for v in x["because"]) for x in recs))
check("wszyscy użytkownicy: przewidywania w skali 1-5",
      all(1 <= x["predicted"] <= 5 for u in m.index for k in (1, 3, 11)
          for x in rec3.recommend(u, top_n=24, k=k)))

for k, code in (("1", 200), ("11", 200), ("0", 400), ("12", 400), ("", 400), ("abc", 400), ("-3", 400)):
    check(f"k={k!r} -> {code}", c.get(f"/api/recommend?user=Ania&k={k}").status_code == code)
check("k=10 -> 200 i k w odpowiedzi", c.get("/api/recommend?user=Ania&k=10").get_json()["k"] == 10)
check("brak user -> 400", c.get("/api/recommend").status_code == 400)
check("pusty user -> 400", c.get("/api/recommend?user=").status_code == 400)
r = c.get("/api/recommend?user=Zzz")
check("nieznany user -> 404 z known_users (12)",
      r.status_code == 404 and len(r.get_json()["known_users"]) == 12 and "Ania" in r.get_json()["known_users"])

r = c.get("/api/users")
check("/api/users -> 12 osób", r.status_code == 200 and r.get_json()["count"] == 12)
r = c.get("/api/similar?user=Ania")
check("/api/similar?user=Ania -> Celina pierwsza", r.status_code == 200 and r.get_json()["similar"][0]["user"] == "Celina")
check("/api/similar bez user -> 400", c.get("/api/similar").status_code == 400)
check("/api/similar?user=Zzz -> 404", c.get("/api/similar?user=Zzz").status_code == 404)

ev = rec3.evaluate("Ania")
check("evaluate: 3 ukryte oceny, MAE >= 0, pokrycie x/3",
      len(ev["hidden"]) == 3 and ev["mae"] is not None and ev["mae"] >= 0 and ev["coverage"].endswith("/3"), ev)
check("evaluate: ukryte to prawdziwe oceny Ani",
      all(m.loc["Ania", t] == v for t, v in ev["hidden"].items()))
check("evaluate nie zmienia oryginalnej macierzy", int(rec3.matrix.count().sum()) == 182)

# --------------------------------------------- ORYGINALNE TESTY Z KURSU
REF = ROOT / "_kurs-referencja"
if REF.exists():
    print("\nORYGINALNE TESTY KURSU (na kopii w katalogu tymczasowym)")
    with tempfile.TemporaryDirectory() as tmp:
        t1 = Path(tmp, "lab1")
        t1.mkdir()
        shutil.copy(REF / "lab1" / "test_lab01.py", t1)
        # test_lab01 ładuje app.py (starter) i rozwiazanie.py: oba to nasz plik
        shutil.copy(ROOT / "lab1" / "app.py", t1 / "app.py")
        shutil.copy(ROOT / "lab1" / "app.py", t1 / "rozwiazanie.py")
        p = subprocess.run([sys.executable, "test_lab01.py"], cwd=t1, capture_output=True, text=True)
        check("test_lab01.py", p.returncode == 0, p.stdout + p.stderr)

        t3 = Path(tmp, "lab3")
        t3.mkdir()
        for f in ("app.py", "recommender.py", "ratings.csv"):
            shutil.copy(ROOT / "lab3" / f, t3)
        shutil.copy(REF / "lab3" / "test_lab03.py", t3)
        p = subprocess.run([sys.executable, "-m", "pytest", "test_lab03.py", "-q", "-p", "no:cacheprovider"],
                           cwd=t3, capture_output=True, text=True)
        last = (p.stdout.strip().splitlines() or ["brak pytest"])[-1]
        check(f"test_lab03.py ({last})", p.returncode == 0, p.stdout[-800:] + p.stderr[-400:])

print(f"\nWYNIK: {passed} PASS, {failed} FAIL")
sys.exit(1 if failed else 0)
