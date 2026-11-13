#!/usr/bin/env python3
"""So What? step 1: fetch every feed in sources.json, clean, de-duplicate, keep the last 72 h,
drop anything already published, and write work/candidates.json for Claude to score.
Standard library only. Usage: python3 scripts/ingest.py"""
import json, re, html, hashlib, datetime, email.utils, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; BrandmizerSoWhat/1.0; +https://brandmizer.com/so-what/)"}
A = "{http://www.w3.org/2005/Atom}"
NOW = datetime.datetime.now(datetime.timezone.utc)

def text(el, *tags):
    for t in tags:
        e = el.find(t)
        if e is not None:
            if e.text and e.text.strip(): return e.text.strip()
            if t == A + "link" and e.get("href"): return e.get("href").strip()
    return ""

def when(s):
    if not s: return None
    try: d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)

def clean(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s*(The post .* appeared first on .*|Continue reading.*|Read more.*)$", "", s)
    return s

def excerpt(s, n=25):
    w = clean(s).split()
    return " ".join(w[:n]) + ("…" if len(w) > n else "")

def norm_title(t):
    return set(re.sub(r"[^a-z0-9 ]", " ", t.lower()).split()) - {"the", "a", "an", "and", "of", "to", "in", "for", "on", "with", "is", "its", "via"}

def similar(a, b):
    return len(a & b) / max(1, len(a | b)) >= 0.6

def main():
    cfg = json.loads((ROOT / "sources.json").read_text())
    seen_path = ROOT / "data" / "seen.json"
    seen = set(json.loads(seen_path.read_text())) if seen_path.exists() else set()
    log, items = [], []
    for src in cfg["sources"]:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(src["url"], headers=UA), timeout=25).read()
            root = ET.fromstring(raw)
        except Exception as e:
            log.append({"source": src["name"], "ok": False, "error": str(e)[:120]}); continue
        entries = root.findall(".//item") or root.findall(".//" + A + "entry")
        kept = 0
        for it in entries:
            title = re.sub(r"\s+via\s+@\w+(,\s*@\w+)*\s*$", "", clean(text(it, "title", A + "title")))
            link = text(it, "link", A + "link", "guid")
            d = when(text(it, "pubDate", "{http://purl.org/dc/elements/1.1/}date", A + "published", A + "updated"))
            if not title or not link.startswith("http") or not d: continue
            if (NOW - d).total_seconds() > cfg["max_age_hours"] * 3600: continue
            link = re.sub(r"[?#].*$", "", link) if "utm_" in link else link
            iid = hashlib.sha1(link.encode()).hexdigest()[:12]
            if iid in seen: continue
            desc = text(it, "description", A + "summary", "{http://purl.org/rss/1.0/modules/content/}encoded", A + "content")
            items.append({"id": iid, "source": src["name"], "region": src["region"], "weight": src.get("weight", 1),
                          "title": title, "url": link, "date": d.astimezone(datetime.timezone.utc).isoformat(),
                          "excerpt": excerpt(desc)})
            kept += 1
        log.append({"source": src["name"], "ok": True, "entries": len(entries), "fresh_new": kept})
    # de-duplicate: same URL or near-identical titles (keep the higher-weight / earlier source)
    items.sort(key=lambda x: (-x["weight"], x["date"]))
    out, sets = [], []
    for x in items:
        t = norm_title(x["title"])
        if any(x["url"] == y["url"] or similar(t, s) for y, s in zip(out, sets)): continue
        out.append(x); sets.append(t)
    out.sort(key=lambda x: x["date"], reverse=True)
    # at most N per source, so one busy feed can't crowd out the rest
    per, capped = {}, []
    for x in out:
        per[x["source"]] = per.get(x["source"], 0) + 1
        if per[x["source"]] <= cfg.get("max_per_source", 12): capped.append(x)
    out = capped[: cfg["max_candidates"]]
    (ROOT / "work").mkdir(exist_ok=True)
    (ROOT / "work" / "candidates.json").write_text(json.dumps({"generated": NOW.isoformat(), "count": len(out), "items": out}, ensure_ascii=False, indent=1))
    (ROOT / "work" / "ingest-log.json").write_text(json.dumps(log, indent=1))
    ok = sum(1 for l in log if l["ok"])
    print(f"ingest: {len(out)} candidates from {ok}/{len(log)} feeds")
    for l in log:
        if not l["ok"]: print("  feed failed:", l["source"], "-", l["error"])

if __name__ == "__main__":
    main()
