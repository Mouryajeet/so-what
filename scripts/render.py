#!/usr/bin/env python3
"""So What? step 4: turn data/latest.json into the static pages Hostinger serves.
Writes site/<path>/: index.html, one page per day (YYYY-MM-DD/index.html), feed.xml, sitemap.xml and the assets.
Plain HTML first: every word is in the page; the CSS/JS only style and filter it.
Config lives in site.json (path, noindex for the preview, signup endpoint). Usage: python3 scripts/render.py"""
import json, html, shutil, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "site.json").read_text())
SITE, PATH = CFG["site_url"].rstrip("/"), "/" + CFG["path"].strip("/") + "/"
OUT = ROOT / "site" / CFG["path"].strip("/")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
NOW = datetime.datetime.now(IST)
E = lambda s: html.escape(str(s or ""), quote=True)
CATS = ["Meta ads", "Google ads", "SEO & AI search", "Social & creators", "Brand & campaigns", "D2C & retail", "Industry news"]
INDS = ["Restaurants & cafés", "Salons & beauty", "Fashion", "Clinics", "Real estate", "Hospitality", "D2C"]
HELP = {"Meta ads": "How we run Meta ads", "Google ads": "How we run Google ads", "SEO & AI search": "How we handle SEO",
        "Social & creators": "How we run social media", "Brand & campaigns": "How we build brands", "D2C & retail": "How we grow D2C brands",
        "Industry news": "How we work"}

def day_label(d):
    dd = datetime.date.fromisoformat(d); today = NOW.date()
    if dd == today: return "Today", dd.strftime("%a %-d %b")
    if dd == today - datetime.timedelta(days=1): return "Yesterday", dd.strftime("%a %-d %b")
    return dd.strftime("%a %-d %b"), dd.strftime("%Y")

def story(p, i):
    bars = "".join(f'<i class="{"on" if k <= p["impact"] else ""}"></i>' for k in range(1, 6))
    pub = datetime.datetime.fromisoformat(p["date"]).astimezone(IST)
    lens = '<span class="lens">India</span>' if p.get("india_lens") else ""
    return f'''<li class="story" id="s-{E(p["id"])}" data-cat="{E(p["category"])}" data-ind="{E("|".join(p.get("industries", [])))}" data-imp="{p["impact"]}" data-india="{1 if p.get("india_lens") else 0}">
  <div class="meta"><span class="bars" role="img" aria-label="Impact {p["impact"]} of 5">{bars}</span><span class="cat">{E(p["category"])}</span>{lens}</div>
  <div>
    <p class="src">{E(p["source"])} · <time datetime="{E(p["date"])}">{pub.strftime("%-d %b")}</time></p>
    <h3><a href="{E(p["url"])}" target="_blank" rel="noopener">{E(p["title"])}<span class="sr"> (opens {E(p["source"])} in a new tab)</span></a></h3>
    {f'<p class="ex">{E(p["excerpt"])}</p>' if p.get("excerpt") else ""}
    <p class="take pro"><b>For you</b>{E(p["take"])}</p>
    <p class="take cafe"><b>For you</b>{E(p["take_cafe"])}</p>
    <a class="more" href="{E(p.get("link", "/services/"))}">{E(HELP.get(p["category"], "How we work"))} →</a>
  </div>
</li>'''

def signal(items):
    """The signal line: one peak per story of the day, oldest left; taller peak = bigger impact.
    Server-rendered and complete without JS. so-what.js animates it (pulse run, peaks rising, scroll sync)."""
    if not items: return ""
    top_id = max(items, key=lambda p: p["impact"])["id"]
    items = sorted(items, key=lambda p: p["date"])
    W, VH, base, n = 1600, 190, 150, len(items)
    xs = [int(160 + (W - 320) * (i + 0.5) / n) for i in range(n)]
    pts, dots = [f"M0 {base}"], []
    for x, p in zip(xs, items):
        h = 22 + p["impact"] * 22
        pts += [f"L{x-26} {base}", f"L{x} {base-h}", f"L{x+26} {base}"]
        cls = "peak" + (" hot" if p["impact"] >= 4 else "") + (" top" if p["id"] == top_id else "") + (" l" if x < W * .18 else " r" if x > W * .82 else "")
        dots.append(f'<button class="{cls}" type="button" data-for="s-{E(p["id"])}" data-x="{x}" data-h="{h}" style="left:{x / W * 100:.3f}%;top:{(base - h) / VH * 100:.3f}%" aria-label="Go to: {E(p["title"])}"><span class="tip" aria-hidden="true"><b>{E(p["category"])} · impact {p["impact"]}</b>{E(p["title"])}</span></button>')
    pts.append(f"L{W} {base}")
    d = " ".join(pts)
    return f'''<div class="signal" data-w="{W}" data-vh="{VH}" data-base="{base}"><svg viewBox="0 0 {W} {VH}" preserveAspectRatio="none" aria-hidden="true" focusable="false">
<defs><linearGradient id="sg" gradientUnits="userSpaceOnUse" x1="0" x2="{W}" y1="0" y2="0"><stop offset="0" stop-color="#8b3ffa" stop-opacity=".15"/><stop offset=".55" stop-color="#b98cff"/><stop offset="1" stop-color="#fb5225" stop-opacity=".5"/></linearGradient>
<linearGradient id="sp" gradientUnits="userSpaceOnUse" x1="-600" x2="-300" y1="0" y2="0"><stop offset="0" stop-color="#fb5225" stop-opacity="0"/><stop offset=".8" stop-color="#ffb724" stop-opacity=".95"/><stop offset=".9" stop-color="#fff"/><stop offset=".96" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<path class="glow" d="{d}" fill="none" stroke="url(#sg)" stroke-width="6" vector-effect="non-scaling-stroke"/><path class="line" d="{d}" fill="none" stroke="url(#sg)" stroke-width="2" vector-effect="non-scaling-stroke"/><path class="spark" d="{d}" fill="none" stroke="url(#sp)" stroke-width="3" vector-effect="non-scaling-stroke"/></svg>
<div class="dots" role="group" aria-label="Today's stories as a signal: the taller the peak, the bigger the impact. Pick one to jump to it.">{''.join(dots)}<span class="head" aria-hidden="true"></span></div></div>'''

def page(days, title, desc, canon, single=False):
    latest = days[0]["items"] if days else []
    total_today = len(latest)
    updated = datetime.datetime.fromisoformat(days[0]["published"]).astimezone(IST).strftime("%-d %b, %H:%M IST") if days else ""
    blocks = []
    for di, d in enumerate(days):
        big, small = day_label(d["date"])
        lis = "\n".join(story(p, i) for i, p in enumerate(d["items"]))
        hint = '<p class="label swipehint">Swipe for more →</p>' if di == 0 else ""
        blocks.append(f'''<section class="day{" today" if di == 0 else ""}" aria-labelledby="d-{d["date"]}">
<div class="dayhead"><h2 id="d-{d["date"]}">{E(big)}</h2><span class="label">{E(small)}</span></div>{hint}
<ol class="list">{lis}</ol><p class="empty" hidden>Nothing here matches your filters. Try "All".</p></section>''')
    cat_btns = '<button class="chip" type="button" data-cat-btn="all" aria-pressed="true">All</button>' + "".join(f'<button class="chip" type="button" data-cat-btn="{E(c)}" aria-pressed="false">{E(c)}</button>' for c in CATS)
    ind_btns = '<button class="chip" type="button" data-ind-btn="all" aria-pressed="true">Every business</button>' + "".join(f'<button class="chip" type="button" data-ind-btn="{E(c)}" aria-pressed="false">{E(c)}</button>' for c in INDS)
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": canon, "description": desc,
              "publisher": {"@type": "Organization", "name": "Brandmizer", "url": SITE + "/"},
              "mainEntity": {"@type": "ItemList", "numberOfItems": total_today, "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "item": {"@type": "NewsArticle", "headline": p["title"], "url": p["url"], "datePublished": p["date"],
                   "publisher": {"@type": "Organization", "name": p["source"]}, "abstract": p["take"]}} for i, p in enumerate(latest)]}}
    robots = '<meta name="robots" content="noindex,nofollow">' if CFG.get("noindex") else '<meta name="robots" content="index,follow,max-image-preview:large">'
    pixel = f'''<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','{CFG["pixel_id"]}');fbq('track','PageView');</script>''' if CFG.get("pixel_id") else ""
    ga4 = f'''<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{CFG["ga4_id"]}');addEventListener('load',function(){{setTimeout(function(){{var s=document.createElement('script');s.async=1;s.src='https://www.googletagmanager.com/gtag/js?id={CFG["ga4_id"]}';document.head.appendChild(s)}},1200)}});</script>''' if CFG.get("ga4_id") else ""
    nav_links = [("Work", "/city/"), ("Services", "/services/"), ("How we work", "/how-we-work/"), ("So What?", PATH), ("About", "/about/"), ("Consult", "/consult/"), ("Brief", "/brief/")]
    nl = "".join(f'<a href="{h}"{" aria-current=page" if h == PATH else ""}>{t}</a>' for t, h in nav_links)
    return f'''<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">{robots}
<link rel="canonical" href="{E(canon)}"><link rel="alternate" type="application/rss+xml" title="So What? by Brandmizer" href="{PATH}feed.xml">
<meta property="og:type" content="website"><meta property="og:site_name" content="Brandmizer"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{E(canon)}"><meta property="og:image" content="{SITE}/og.jpg"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/icon.png"><link rel="preload" href="{PATH}bricolage.woff2" as="font" type="font/woff2" crossorigin>
<script>try{{if(!matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('motion')}}catch(e){{}}</script>
<link rel="stylesheet" href="{PATH}so-what.css?v={CFG["asset_version"]}">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>{pixel}{ga4}
</head>
<body>
<a class="skip" href="#stories">Skip to the stories</a>
<header class="nav"><div class="wrap"><a class="brand" href="/"><img src="{PATH}mark.png" alt="" width="24" height="24">BRANDMIZER</a>
<nav class="links" aria-label="Pages">{nl}<a class="cta" href="/brief/">Start a project</a></nav>
<details class="menu"><summary aria-label="Menu">Menu</summary><nav class="drawer" aria-label="Pages (menu)">{nl}<a href="/brief/">Start a project</a></nav></details></div></header>
<main id="main">
<section class="hero"><div class="wrap">
<div class="hero-top"><div><p class="label kicker">Marketing news for Indian business owners</p>
<h1>So <em>what?</em></h1>
<p class="sub">The news, then the only question that matters: what it means for your business, in plain English.</p></div>
<p class="label stamp"><b>{total_today} stories {"today" if not single else "this day"}</b>Updated {E(updated)}</p></div>
{signal(latest)}</div></section>
<div class="controls" role="region" aria-label="Filters"><div class="wrap">
<span class="dial" aria-hidden="true"></span><div class="chips" role="group" aria-label="Category">{cat_btns}</div>
<label class="imp-ctl label" for="min">Min impact <input id="min" type="range" min="3" max="5" step="1" value="3"> <span id="minval">3+</span></label>
</div><div class="wrap"><div class="chips" role="group" aria-label="Business type">{ind_btns}</div>
<button class="sw" id="lens" type="button" aria-pressed="false"><i></i>Bhopal / India lens</button>
<button class="sw" id="cafe" type="button" aria-pressed="false"><i></i>Explain it like I run a café</button></div></div>
<div class="wrap days" id="stories"><div class="countrow"><p class="label" aria-live="polite" id="count"></p><button class="clear" id="clear" type="button" hidden>Clear filters</button></div>
{''.join(blocks) if blocks else '<p class="empty">Today’s stories are on their way. Check back after 7 am.</p>'}
<section class="signup" aria-labelledby="mon"><div><p class="label kicker">Every Monday</p><h2 class="h2" id="mon">The week, <em>in one message.</em></h2>
<p>The five stories that mattered most, with what to do about each. On WhatsApp or by email, once a week. Nothing else.</p></div>
<form id="signup" data-endpoint="{E(CFG.get("signup_endpoint", ""))}" data-wa="{E(CFG["whatsapp"])}" novalidate>
<div class="row2"><label class="f" for="nm">Your name<input id="nm" name="name" type="text" autocomplete="name" required></label>
<label class="f" for="ct">WhatsApp number or email<input id="ct" name="contact" type="text" autocomplete="email" required></label></div>
<label class="consent"><input type="checkbox" name="consent" value="yes"> Send me So What? every Monday. I can stop it any time.</label>
<button class="btn" type="submit">Send it to me →</button><p class="status" id="status" role="status"></p></form></section>
<p class="note">Headlines and short excerpts belong to their publishers and link to the full story. The “For you” notes are Brandmizer’s own, written with AI help each morning and checked against our rules. Nothing here promises results.</p>
</div></main>
<footer class="foot"><div class="wrap"><div><p class="big">Bring the problem.<br>Leave with a plan.</p></div>
<div><nav aria-label="Footer">{nl.replace(' aria-current=page', '')}<a href="/privacy/">Privacy</a><a href="{PATH}feed.xml">RSS</a></nav><p class="small">Audit | Strategy | Direction | Growth · © {NOW.year} Brandmizer</p></div></div></footer>
<script src="{PATH}so-what.js?v={CFG["asset_version"]}" defer></script>
</body></html>'''

def rss(days):
    items = []
    for d in days[:3]:
        for p in d["items"]:
            pub = datetime.datetime.fromisoformat(p["date"]).strftime("%a, %d %b %Y %H:%M:%S %z")
            items.append(f'<item><title>{E(p["title"])}</title><link>{E(p["url"])}</link><guid isPermaLink="false">sowhat-{E(p["id"])}</guid><pubDate>{pub}</pubDate><category>{E(p["category"])}</category><description>{E("For you: " + p["take"] + " (Source: " + p["source"] + ")")}</description></item>')
    return f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>So What? by Brandmizer</title><link>{SITE}{PATH}</link><description>Marketing news for Indian business owners, with what it means for you.</description><language>en-in</language><lastBuildDate>{NOW.strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>{"".join(items)}</channel></rss>'''

def main():
    data = json.loads((ROOT / "data" / "latest.json").read_text())
    days = [d for d in data["days"] if d.get("items") is not None]
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for f, dst in (("so-what.css", "so-what.css"), ("so-what.js", "so-what.js"), ("BricolageGrotesque-latin-variable.woff2", "bricolage.woff2"), ("OFL-BricolageGrotesque.txt", "OFL-Bricolage.txt"), ("mark.png", "mark.png")):
        shutil.copy(ROOT / "assets" / f, OUT / dst)
    desc = "Today's marketing news for Indian business owners, with a plain-English note on what each story means for you. Updated every morning by Brandmizer, Bhopal."
    (OUT / "index.html").write_text(page(days[:7], "So What? Marketing news, and what it means for your business | Brandmizer", desc, SITE + PATH))
    urls = [SITE + PATH]
    for d in days:
        sub = OUT / d["date"]; sub.mkdir()
        big, small = day_label(d["date"])
        dl = datetime.date.fromisoformat(d["date"]).strftime("%-d %B %Y")
        (sub / "index.html").write_text(page([d], f"So What? {dl}: marketing news for business owners | Brandmizer",
                                              f"The marketing stories that mattered on {dl}, with what each means for an Indian business owner.", f"{SITE}{PATH}{d['date']}/", single=True))
        urls.append(f"{SITE}{PATH}{d['date']}/")
    (OUT / "feed.xml").write_text(rss(days))
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{NOW.date().isoformat()}</lastmod></url>" for u in urls) + "</urlset>")
    (OUT / "robots-note.txt").write_text("noindex preview\n" if CFG.get("noindex") else "public\n")
    print(f"render: {len(days)} day(s), {sum(len(d['items']) for d in days)} stories → site/{CFG['path']}/ (noindex={CFG.get('noindex')})")

if __name__ == "__main__":
    main()
