#!/usr/bin/env python3
"""
A wide 16:9 thumbnail for every show that can have one. Shows in the guide with no picture, or only a portrait
poster, are looked up by title on TVmaze (its "background" pictures; free, no key) and, when the TMDB_KEY secret is
set, on TMDB (backdrops); the thumbnail goes into the guide.
Answers are kept in a cache (published next to the guide) so each run only asks about titles it hasn't seen,
at most MAX_LOOKUPS a run, within TVmaze's limit of 20 requests per 10 seconds.

Usage: python3 shelf/fill_posters.py out/guide.xml posters-us.json
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request

guide, cache_path = sys.argv[1], sys.argv[2]
MAX = int(os.environ.get("MAX_LOOKUPS", "2500"))
TMDB = os.environ.get("TMDB_KEY", "").strip()
UA = {"User-Agent": "shelf-guide/1.0"}

try: cache = json.load(open(cache_path))
except Exception: cache = {}

def is_poster(u):
    return bool(re.search(r"tmsimg\.com/assets/[^/]*_v\d", u)) or "/poster.jpg" in u or "/w500/" in u or "/w342/" in u \
        or "medium_portrait" in u or "/3-4/" in u
def is_wide(u): return bool(u) and not is_poster(u) and "colorLogo" not in u

# Not shows: nothing to find (local slots, infomercials, news blocks, off-air)
JUNK = re.compile(r"^(local program|paid program|programa pagado|infomercial|sign ?off|off air|to be announced|tba|"
                  r"news\b|.*\bnews (at|@) \d|.*\bnewscast|movie|película|cine|programming|nfl football$|college football$|"
                  r"\w+ (football|basketball|baseball|hockey|soccer)$)", re.I)

def key(t): return re.sub(r"[^a-z0-9]", "", re.sub(r"^the\s+|\s*\(\d{4}\)$", "", t.lower()))

def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if e.code == 429: time.sleep(10); continue
            return None
        except Exception:
            time.sleep(2)
    return None

def tvmaze(title):
    time.sleep(0.55)
    d = get("https://api.tvmaze.com/search/shows?q=" + urllib.parse.quote(title)) or []
    for hit in d:
        s = hit.get("show") or {}
        if key(s.get("name", "")) != key(title): continue
        time.sleep(0.55)
        best, score = None, 1e9
        for im in get(f"https://api.tvmaze.com/shows/{s['id']}/images") or []:
            if im.get("type") != "background": continue
            o = (im.get("resolutions") or {}).get("original") or {}
            w = o.get("width") or 1280
            sc = abs(w - 1280) - (400 if im.get("main") else 0)
            if w >= 600 and o.get("url") and sc < score: best, score = o["url"], sc
        return best
    return None

def tmdb(title):
    if not TMDB: return None
    for kind, field in (("tv", "name"), ("movie", "title")):
        time.sleep(0.05)
        d = get(f"https://api.themoviedb.org/3/search/{kind}?api_key={TMDB}&query=" + urllib.parse.quote(title)) or {}
        for r in d.get("results", [])[:8]:
            if key(r.get(field, "")) == key(title) and r.get("backdrop_path"):
                return "https://image.tmdb.org/t/p/w780" + r["backdrop_path"]
    return None

xml = open(guide, encoding="utf-8").read()
prog_re = re.compile(r"<programme [^>]*>.*?</programme>", re.S)
need = {}
for m in prog_re.finditer(xml):
    p = m.group(0)
    icon = re.search(r'<icon src="([^"]*)"', p)
    if icon and is_wide(icon.group(1)): continue
    t = html.unescape(html.unescape(re.search(r"<title[^>]*>(.*?)</title>", p, re.S).group(1))).strip()
    if t and not JUNK.match(t): need[t] = need.get(t, 0) + 1

asked = 0
for t, _ in sorted(need.items(), key=lambda kv: -kv[1]):   # most-shown first
    if t in cache or asked >= MAX: continue
    asked += 1
    short = re.split(r":\s| - ", t)[0].strip()   # "Marriage Boot Camp: Reality Stars" → the show
    cache[t] = tvmaze(t) or tmdb(t) or (short != t and len(short) > 3 and (tvmaze(short) or tmdb(short))) or ""

found = 0
def fix(m):
    global found
    p = m.group(0)
    icon = re.search(r'<icon src="([^"]*)"', p)
    if icon and is_wide(icon.group(1)): return p
    t = html.unescape(html.unescape(re.search(r"<title[^>]*>(.*?)</title>", p, re.S).group(1))).strip()
    u = cache.get(t)
    if not u: return p
    found += 1
    u = html.escape(u, quote=True)
    if icon: return p.replace(icon.group(0), f'<icon src="{u}"', 1)
    return p.replace("</programme>", f'<icon src="{u}"/></programme>')

xml = prog_re.sub(fix, xml)
open(guide, "w", encoding="utf-8").write(xml)
json.dump(cache, open(cache_path, "w"), ensure_ascii=False, sort_keys=True)
hits = sum(1 for v in cache.values() if v)
print(f"titles needing a thumbnail: {len(need)}; looked up now: {asked}; known thumbnails: {hits} of {len(cache)} titles; "
      f"shows given a thumbnail: {found}")
