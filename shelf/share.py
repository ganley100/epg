#!/usr/bin/env python3
"""
Channels that share one listing (BBC One's regions, +1 and HD copies): the grabber saves the listing once,
under one of their IDs. This copies it to every playlist ID that uses the same site listing.

Usage: python3 shelf/share.py shelf/uk.channels.xml out/guide-uk.xml
"""
import re, sys

chans, guide = sys.argv[1], sys.argv[2]
groups = {}
for m in re.finditer(r'<channel ([^>]*)>', open(chans, encoding="utf-8").read()):
    a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    groups.setdefault((a["site"], a["site_id"]), []).append(a["xmltv_id"].replace("&amp;", "&"))

xml = open(guide, encoding="utf-8").read()
progs = {}
for m in re.finditer(r'<programme [^>]*channel="([^"]*)".*?</programme>', xml, re.S):
    progs.setdefault(m.group(1), []).append(m.group(0))
chan_el = {m.group(1): m.group(0) for m in re.finditer(r'<channel id="([^"]*)">.*?</channel>', xml, re.S)}

def q(s): return s.replace("&", "&amp;")
extra_c, extra_p, n = [], [], 0
for ids in groups.values():
    src = next((i for i in ids if q(i) in progs), None)
    if not src: continue
    for i in ids:
        if q(i) in progs: continue
        n += 1
        if q(src) in chan_el: extra_c.append(chan_el[q(src)].replace(f'id="{q(src)}"', f'id="{q(i)}"', 1))
        extra_p += [p.replace(f'channel="{q(src)}"', f'channel="{q(i)}"', 1) for p in progs[q(src)]]

if n:
    first_prog = xml.find("<programme ")
    xml = xml[:first_prog] + "".join(extra_c) + "\n" + xml[first_prog:]
    xml = xml.replace("</tv>", "".join(extra_p) + "\n</tv>")
    open(guide, "w", encoding="utf-8").write(xml)
print(f"Shared listings copied to {n} more channels")
