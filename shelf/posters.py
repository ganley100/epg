#!/usr/bin/env python3
"""
Makes every show picture in the guide a poster:
- Gracenote (Zap2it) posters: their listed image host (zap2it.tmsimg.com) no longer exists; the same images
  are served by demo.tmsimg.com.
- Pluto TV: the square "tile" picture becomes the show's 2:3 poster.
- Sky (UK): the 16:9 still becomes the show's portrait (3:4) poster, which Sky has for every show.

Usage: python3 shelf/posters.py out/guide.xml
"""
import re, sys

path = sys.argv[1]
xml = open(path, encoding="utf-8").read()
n_gn = xml.count("zap2it.tmsimg.com")
xml = xml.replace("https://zap2it.tmsimg.com/", "https://demo.tmsimg.com/")
pluto = re.compile(r'(https?://images\.pluto\.tv/(?:series|channels)/[0-9a-f]+)/tile[^"/?]*\.(?:jpg|png)(?:\?[^"]*)?')
xml, n_pl = pluto.subn(r'\1/poster.jpg?fm=jpg&amp;q=75&amp;w=600&amp;h=900', xml)
sky = re.compile(r'(https?://images\.metadata\.sky\.com/pd-image/[0-9a-f-]+)/16-9/\d+')
xml, n_sky = sky.subn(r'\1/3-4/600', xml)
open(path, "w", encoding="utf-8").write(xml)
print(f"Gracenote posters: {n_gn}, Pluto posters: {n_pl}, Sky posters: {n_sky}")
