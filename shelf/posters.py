#!/usr/bin/env python3
"""
Makes every show picture in the guide a wide 16:9 thumbnail where the source has one:
- Gracenote (Zap2it) posters: their listed image host (zap2it.tmsimg.com) no longer exists; the same images
  are served by demo.tmsimg.com.
- Pluto TV: the square tile / poster becomes a wide 16:9 thumbnail (the episode's still, or the show's featured image).
- Sky (UK): its 16:9 still is kept (a portrait poster from an older run goes back to 16:9).

Usage: python3 shelf/posters.py out/guide.xml
"""
import re, sys

path = sys.argv[1]
xml = open(path, encoding="utf-8").read()
n_gn = xml.count("zap2it.tmsimg.com")
xml = xml.replace("https://zap2it.tmsimg.com/", "https://demo.tmsimg.com/")
pluto = re.compile(r'(https?://images\.pluto\.tv/(series|episodes)/[0-9a-f]+)/(?:tile|poster|featuredImage)[^"/?]*\.(?:jpg|png)(?:\?[^"]*)?')
def wide(m):
    return m.group(1) + ("/screenshot16_9.jpg" if m.group(2) == "episodes" else "/featuredImage.jpg") + "?fm=jpg&amp;q=75&amp;w=640&amp;h=360"
xml, n_pl = pluto.subn(wide, xml)
sky = re.compile(r'(https?://images\.metadata\.sky\.com/pd-image/[0-9a-f-]+)/(?:3-4|16-9)/\d+')
xml, n_sky = sky.subn(r'\1/16-9/640', xml)
open(path, "w", encoding="utf-8").write(xml)
print(f"Gracenote host fixed: {n_gn}, Pluto thumbnails: {n_pl}, Sky thumbnails: {n_sky}")
