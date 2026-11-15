#!/usr/bin/env python3
"""
Posters for Gracenote's wide art. The Roku Channel's listings (and some Zap2it ones) carry Gracenote's wide 16:9 art
(p12345_b_h8_aa); Gracenote usually also has the show's portrait poster under the same number (b_v13 / b_v12 /
b_v9 / b_v8 …). Each one is found once (a few quick checks), remembered in a cache, and put into the guide.

Usage: python3 shelf/gracenote_posters.py out/guide.xml gracenote-posters.json
"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

guide, cache_path = sys.argv[1], sys.argv[2]
VARIANTS = ["b_v13_aa", "b_v12_aa", "b_v9_aa", "b_v8_aa", "b_v8_ab", "b_v11_aa", "b_v7_aa", "b_v6_aa", "b_v5_aa", "b_v4_aa"]
try: cache = json.load(open(cache_path))
except Exception: cache = {}
now = time.time()
xml = open(guide, encoding="utf-8").read()
wide = re.compile(r'https://(?:demo\.tmsimg\.com|images\.sr\.roku\.com/[^"\s]*?/gracenote)/assets/(p\d+)_[a-z]+_h\d+_[a-z]+\.jpg(?:\?[^"\s<]*)?')
ids = sorted(set(m.group(1) for m in wide.finditer(xml)))

def exists(url):
    for _ in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "shelf-guide/1.0"}), timeout=15) as r:
                return r.status == 200
        except urllib.error.HTTPError as e:
            if e.code == 404: return False
        except Exception: time.sleep(1)
    return None

def find(pid):
    for v in VARIANTS:
        ok = exists(f"https://demo.tmsimg.com/assets/{pid}_{v}.jpg")
        if ok: return pid, v
        if ok is None: return pid, None
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
    return f"https://demo.tmsimg.com/assets/{m.group(1)}_{v}.jpg"
xml = wide.sub(swap, xml)
open(guide, "w", encoding="utf-8").write(xml)
json.dump(cache, open(cache_path, "w"), sort_keys=True)
print(f"Gracenote wide art: {len(ids)} shows, checked now: {len(todo)}, with posters: {sum(1 for p in ids if cache.get(p, [''])[0])}; swapped: {n}")
