#!/usr/bin/env python3
"""So What? step 1 for the cloud routine: take the candidates GitHub Actions fetched (data/inbox/candidates.json)
and copy them to work/candidates.json if they are fresh (< 12 h). Exit code 2 = stale/missing, 3 = empty."""
import json, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
src = ROOT / "data" / "inbox" / "candidates.json"
if not src.exists(): print("inbox missing"); sys.exit(2)
d = json.loads(src.read_text())
age = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(d["generated"])).total_seconds() / 3600
if age > 12: print(f"inbox is old ({age:.1f} h)"); sys.exit(2)
seen_p = ROOT / "data" / "seen.json"
seen = set(json.loads(seen_p.read_text())) if seen_p.exists() else set()
d["items"] = [x for x in d["items"] if x["id"] not in seen]   # never score a story twice
d["count"] = len(d["items"])
(ROOT / "work").mkdir(exist_ok=True)
(ROOT / "work" / "candidates.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
print(f"inbox ok: {d['count']} stories, fetched {age:.1f} h ago")
if not d["items"]: sys.exit(3)
