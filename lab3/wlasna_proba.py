"""Własna próba (lab 3): Ania zmienia ocenę Parasite z 5 na 2.

Liczymy na KOPII danych w pamięci; ratings.csv na dysku się nie zmienia.
Uruchom: python wlasna_proba.py  (wynik trafia też do wlasna_proba.json)
"""
import json
import sys
from pathlib import Path

from recommender import build_model, df, recommend

sys.stdout.reconfigure(encoding="utf-8")
USER, MOVIE, NEW_RATING = "Ania", "Parasite", 2


def snapshot(model):
    matrix, means, sim = model
    return {
        "mean": round(float(means[USER]), 3),
        "neighbors": [{"user": v, "similarity": round(float(w), 3)}
                      for v, w in sim[USER].drop(USER).sort_values(ascending=False).head(3).items()],
        "all_similarities": {v: round(float(w), 3) for v, w in sim[USER].drop(USER).items()},
        "top5": recommend(USER, top_n=5, k=3, model=model),
    }


copy = df.copy()  # kopia: oryginalna tabela zostaje nietknięta
row = (copy["user"] == USER) & (copy["title"] == MOVIE)
old_rating = int(copy.loc[row, "rating"].iloc[0])
copy.loc[row, "rating"] = NEW_RATING

before, after = snapshot(build_model(df)), snapshot(build_model(copy))
result = {"change": {"user": USER, "title": MOVIE, "from": old_rating, "to": NEW_RATING},
          "before": before, "after": after}

for name, snap in (("PRZED", before), ("PO", after)):
    print(f"== {name}: średnia {USER} = {snap['mean']:.3f}")
    print("   sąsiedzi:", ", ".join(f"{n['user']} {n['similarity']:.3f}" for n in snap["neighbors"]))
    for r in snap["top5"]:
        print(f"   {r['predicted']:.2f}  {r['title']:<26} <- {', '.join(r['because'])}")
print("\nzmiana podobieństwa do Ani (przed -> po):")
for v in sorted(before["all_similarities"], key=lambda v: -after["all_similarities"][v]):
    print(f"   {v:<8} {before['all_similarities'][v]:+.3f} -> {after['all_similarities'][v]:+.3f}")

Path(__file__).with_name("wlasna_proba.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
