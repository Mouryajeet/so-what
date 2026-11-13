#!/usr/bin/env python3
"""So What? step 3: check Claude's work/takes.json against the rules, merge it with work/candidates.json,
pick the day's stories (impact >= 3, top 15) and write:
  data/days/YYYY-MM-DD.json   the day (IST date)
  data/latest.json            the last 10 days, what the website reads
  data/queue.json             impact-5 stories waiting for a human write-up
  data/seen.json              every scored id, so nothing is scored twice
  data/runs.log               one line per run
Exits non-zero (and publishes nothing) if takes.json breaks the rules. Usage: python3 scripts/publish.py"""
import json, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
NOW = datetime.datetime.now(IST)
CATEGORIES = ["Meta ads", "Google ads", "SEO & AI search", "Social & creators", "Brand & campaigns", "D2C & retail", "Industry news"]
INDUSTRIES = ["Restaurants & cafés", "Salons & beauty", "Fashion", "Clinics", "Real estate", "Hospitality", "D2C"]
# where each category points on brandmizer.com (internal links)
LINKS = {"Meta ads": "/services/", "Google ads": "/services/", "SEO & AI search": "/services/", "Social & creators": "/services/",
         "Brand & campaigns": "/services/", "D2C & retail": "/services/", "Industry news": "/how-we-work/"}
BANNED = re.compile(r"(?i)\b(guarantee[ds]?|guaranteed|100% results|double your (sales|revenue)|get rich|overnight success)\b")
MAX_PUBLISH, MIN_ALERT = 15, 3

def words(s): return len((s or "").split())

def fail(msg):
    with open(ROOT / "data" / "runs.log", "a") as f: f.write(f"{NOW.isoformat()} FAILED {msg}\n")
    print("publish FAILED:", msg); sys.exit(1)

def main():
    cand = json.loads((ROOT / "work" / "candidates.json").read_text())
    try: takes = json.loads((ROOT / "work" / "takes.json").read_text())
    except Exception as e: fail(f"work/takes.json unreadable: {e}")
    byid = {c["id"]: c for c in cand["items"]}
    errors, scored = [], {}
    for t in takes.get("items", []):
        i = t.get("id")
        if i not in byid: errors.append(f"unknown id {i}"); continue
        if t.get("category") not in CATEGORIES: errors.append(f"{i}: bad category {t.get('category')}")
        if any(x not in INDUSTRIES for x in t.get("industries", [])): errors.append(f"{i}: bad industry {t.get('industries')}")
        if not isinstance(t.get("impact"), int) or not 1 <= t["impact"] <= 5: errors.append(f"{i}: impact must be 1-5")
        if t.get("impact", 0) >= 3 and not t.get("dup_of"):
            if not (12 <= words(t.get("take")) <= 70): errors.append(f"{i}: take must be 12-70 words")
            if not (6 <= words(t.get("take_cafe")) <= 45): errors.append(f"{i}: take_cafe must be 6-45 words")
            if words(t.get("impact_reason")) > 25: errors.append(f"{i}: impact_reason over 25 words")
        for f in ("take", "take_cafe", "impact_reason"):
            if BANNED.search(t.get(f) or ""): errors.append(f"{i}: banned promise wording in {f}")
        scored[i] = t
    missing = [i for i in byid if i not in scored]
    if missing: errors.append(f"{len(missing)} candidates not scored, e.g. {missing[:3]}")
    if errors: fail("; ".join(errors[:12]))

    picks = []
    for i, t in scored.items():
        if t["impact"] < 3 or t.get("dup_of"): continue
        c = byid[i]
        picks.append({"id": i, "title": c["title"], "url": c["url"], "source": c["source"], "region": c["region"],
                      "date": c["date"], "excerpt": c["excerpt"], "category": t["category"], "industries": t.get("industries", []),
                      "impact": t["impact"], "impact_reason": t.get("impact_reason", ""), "india_lens": bool(t.get("india_lens")),
                      "take": t["take"].strip(), "take_cafe": t["take_cafe"].strip(), "link": LINKS[t["category"]], "_w": c["weight"]})
    picks.sort(key=lambda p: (-p["impact"], -p["_w"], -datetime.datetime.fromisoformat(p["date"]).timestamp()))
    picks = picks[:MAX_PUBLISH]
    for p in picks: p.pop("_w")
    day = NOW.strftime("%Y-%m-%d")
    (ROOT / "data" / "days").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "days" / f"{day}.json").write_text(json.dumps({"date": day, "published": NOW.isoformat(), "items": picks}, ensure_ascii=False, indent=1))

    days = sorted((ROOT / "data" / "days").glob("*.json"), reverse=True)[:10]
    latest = {"updated": NOW.isoformat(), "mode": "claude", "days": [json.loads(p.read_text()) for p in days]}
    (ROOT / "data" / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=1))

    qpath = ROOT / "data" / "queue.json"
    queue = json.loads(qpath.read_text()) if qpath.exists() else []
    known = {q["id"] for q in queue}
    queue += [{"id": p["id"], "date": day, "title": p["title"], "url": p["url"], "status": "waiting"} for p in picks if p["impact"] == 5 and p["id"] not in known]
    qpath.write_text(json.dumps(queue, ensure_ascii=False, indent=1))

    spath = ROOT / "data" / "seen.json"
    seen = json.loads(spath.read_text()) if spath.exists() else []
    seen = (seen + [i for i in scored if i not in seen])[-3000:]
    spath.write_text(json.dumps(seen))
    msg = f"{NOW.isoformat()} OK scored={len(scored)} published={len(picks)} impact5={sum(p['impact']==5 for p in picks)}"
    if len(picks) < MIN_ALERT: msg += " LOW-COUNT"
    with open(ROOT / "data" / "runs.log", "a") as f: f.write(msg + "\n")
    print("publish:", msg)

if __name__ == "__main__":
    main()
