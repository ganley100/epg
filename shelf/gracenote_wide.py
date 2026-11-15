#!/usr/bin/env python3
"""
Cable channels' wide thumbnails from Gracenote (the guide data cable boxes use). Zap2it lists each show's portrait
poster (p12345_b_v13_aa); Gracenote usually also has the show's 16:9 title art under the same number (b_h8 / b_h10:
with the title, i_h8 / i_h10: the picture alone). Each poster's wide version is found once (a few quick checks),
remembered in a cache, and put into the guide in place of the poster (640 wide).

Usage: python3 shelf/gracenote_wide.py out/guide.xml gracenote-wide.json
"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

guide, cache_path = sys.argv[1], sys.argv[2]
VARIANTS = ["b_h8_aa", "b_h10_aa", "b_h8_ab", "b_h10_ab", "i_h8_aa", "i_h10_aa"]
try: cache = json.load(open(cache_path))
except Exception: cache = {}
now = time.time()

xml = open(guide, encoding="utf-8").read()
# Gracenote posters, also as the Roku Channel serves them (images.sr.roku.com/…/gracenote/assets/p…_v…).
poster = re.compile(r'https://(?:demo\.tmsimg\.com|images\.sr\.roku\.com/[^"\s]*?/gracenote)/assets/(p\d+)_[a-z]+_v\d+_[a-z]+\.jpg(?:\?[^"\s<]*)?')
ids = sorted(set(m.group(1) for m in poster.finditer(xml)))

def exists(url):
    for _ in range(2):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "shelf-guide/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r: return r.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 404: return False
        except Exception: time.sleep(1)
    return None

def find(pid):
    for v in VARIANTS:
        ok = exists(f"https://demo.tmsimg.com/assets/{pid}_{v}.jpg")
        if ok: return pid, v
        if ok is None: return pid, None   # trouble: ask again next run
    return pid, ""

todo = [p for p in ids if p not in cache or (cache[p][0] == "" and now - cache[p][1] > 7 * 86400)]
with ThreadPoolExecutor(16) as ex:
    for pid, v in ex.map(find, todo):
        if v is not None: cache[pid] = [v, now]

n = 0
def swap(m):
    global n
    v = cache.get(m.group(1), [""])[0]
    if not v: return m.group(0)
    n += 1
    return f"https://demo.tmsimg.com/assets/{m.group(1)}_{v}.jpg?w=640"
xml = poster.sub(swap, xml)
open(guide, "w", encoding="utf-8").write(xml)
json.dump(cache, open(cache_path, "w"), sort_keys=True)
print(f"Gracenote shows: {len(ids)}, checked now: {len(todo)}, with wide art: {sum(1 for p in ids if cache.get(p, [''])[0])}; pictures swapped: {n}")
