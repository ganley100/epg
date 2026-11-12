#!/usr/bin/env python3
"""
Builds shelf/us.channels.xml: every channel of the iptv-org US playlist that one of the grabber's
sites can give a guide for, with one site per channel (the one with the best data, pictures first).
The playlist's own tvg-id is used as the guide ID, so Shelf (and any player) matches it straight away.

Usage: python3 shelf/make_channels.py [playlist-url-or-file] [output]
"""
import glob, re, sys, urllib.request
from xml.sax.saxutils import escape

PLAYLIST = sys.argv[1] if len(sys.argv) > 1 else "https://iptv-org.github.io/iptv/countries/us.m3u"
OUT = sys.argv[2] if len(sys.argv) > 2 else "shelf/us.channels.xml"

# Best first: Pluto and Plex give show pictures; TV Guide and TV Passport cover cable channels.
# tvtv.us is left out: it refuses GitHub's servers.
SITES = ["pluto.tv", "plex.tv", "tvguide.com", "tvpassport.com", "xumo.tv", "distro.tv"]

text = open(PLAYLIST).read() if not PLAYLIST.startswith("http") else urllib.request.urlopen(PLAYLIST, timeout=60).read().decode("utf-8", "replace")
ids = {i for i in re.findall(r'tvg-id="([^"]+)"', text) if i}
by_base = {}
for i in sorted(ids):
    by_base.setdefault(i.split("@")[0], []).append(i)

def files(site):
    fs = sorted(glob.glob(f"sites/{site}/*.channels.xml"))
    # The US list first, then the rest (English entries are preferred below anyway).
    return sorted(fs, key=lambda f: (0 if re.search(r"_us\.channels\.xml$", f) else 1 if "_all" in f else 2, f))

chosen = {}  # playlist id -> (site, site_id, lang, name)
for site in SITES:
    entries = []
    for f in files(site):
        for m in re.finditer(r'<channel ([^>]*)>([^<]*)</channel>', open(f, encoding="utf-8").read()):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            if "xmltv_id" in attrs and "site_id" in attrs:
                entries.append((attrs, m.group(2)))
    entries.sort(key=lambda e: 0 if e[0].get("lang", "en") == "en" else 1)  # English first
    for attrs, name in entries:
        x = attrs["xmltv_id"]
        targets = [x] if x in ids else by_base.get(x.split("@")[0], [])
        for pid in targets:
            if pid not in chosen:
                chosen[pid] = (site, attrs["site_id"], attrs.get("lang", "en"), name)

lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<channels>"]
for pid, (site, sid, lang, name) in sorted(chosen.items(), key=lambda kv: (SITES.index(kv[1][0]), kv[0])):
    lines.append(f'  <channel site="{site}" site_id="{escape(sid, {chr(34): "&quot;"})}" lang="{lang}" xmltv_id="{escape(pid, {chr(34): "&quot;"})}">{name}</channel>')
lines.append("</channels>")
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

counts = {}
for s, *_ in chosen.values():
    counts[s] = counts.get(s, 0) + 1
print(f"{len(chosen)} of {len(ids)} playlist channels have a guide source:", ", ".join(f"{s} {n}" for s, n in sorted(counts.items(), key=lambda kv: -kv[1])))
