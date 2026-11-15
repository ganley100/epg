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

# Best first: Zap2it (Gracenote, the data cable boxes use) has a poster for every show on cable channels;
# Pluto and Plex give pictures for their own channels; TV Guide and TV Passport fill in the rest.
# tvtv.us is left out: it refuses GitHub's servers.
SITES = ["zap2it.com", "pluto.tv", "plex.tv", "tvguide.com", "tvpassport.com", "xumo.tv", "distro.tv"]
# Another country's list: SHELF_SITES="sky.com,freeview.co.uk,..." (best first) and SHELF_COUNTRY="uk".
import os
if os.environ.get("SHELF_SITES"):
    SITES = [x.strip() for x in os.environ["SHELF_SITES"].split(",") if x.strip()]
COUNTRY = os.environ.get("SHELF_COUNTRY", "us")

# Zap2it lists channels by Gracenote code (no channel IDs): these are the names they stand for.
ZAP = {
    "AMC": "amc", "AETV": "ae aande", "BET": "bet", "BRAVO": "bravo", "FREEFRM": "freeform", "CMTV": "cmt",
    "CNBC": "cnbc", "CNN": "cnn", "HLN": "hln", "CNNI": "cnninternational", "COMEDY": "comedycentral",
    "TRUTV": "trutv", "CSPAN": "cspan", "CSPAN2": "cspan2", "DISN": "disneychannel", "DXD": "disneyxd",
    "DJCH": "disneyjunior", "ESPN": "espn", "ESPN2": "espn2", "ESPNU": "espnu", "ESPNEWS": "espnews",
    "ESPND": "espndeportes", "EWTN": "ewtn", "GALA": "galavision", "HSN": "hsn", "LIFE": "lifetime",
    "LMN": "lifetimemovies lifetimemovienetwork", "MSG": "msg", "MTV": "mtv", "MTV2": "mtv2", "E": "e eentertainment",
    "NESN": "nesn", "NIK": "nickelodeon", "NICJR": "nickjr", "NIKTON": "nicktoons", "TNCK": "teennick",
    "INSP": "insp", "QVC": "qvc", "SYFY": "syfy", "UNI": "univision", "DSC": "discovery discoverychannel",
    "DFC": "discoveryfamily", "DEST": "destinationamerica", "SCIENCE": "sciencechannel science",
    "ID": "investigationdiscovery", "TLC": "tlc", "TNT": "tnt", "TRAV": "travelchannel travel",
    "WEATH": "theweatherchannel weatherchannel", "USA": "usanetwork usa", "VH1": "vh1", "HALL": "hallmarkchannel hallmark",
    "HMYSHD": "hallmarkmystery hallmarkmoviesmysteries", "HFM": "hallmarkfamily", "TBS": "tbs", "TOON": "cartoonnetwork",
    "BOOM": "boomerang", "FOOD": "foodnetwork", "COOK": "cookingchannel", "TCM": "turnerclassicmovies tcm",
    "FX": "fx", "FXX": "fxx", "FXM": "fxm fxmovies", "HGTV": "hgtv", "HISTORY": "history historychannel",
    "AHC": "americanheroeschannel", "NGC": "nationalgeographic natgeo", "NGWILD": "natgeowild nationalgeographicwild",
    "APL": "animalplanet", "OXYGEN": "oxygen", "WE": "wetv we", "GSN": "gameshownetwork gsn", "NFLNET": "nflnetwork",
    "NBATV": "nbatv", "MLBN": "mlbnetwork", "NHLNET": "nhlnetwork", "GOLF": "golfchannel golf", "TENNIS": "tennischannel",
    "FS1": "foxsports1 fs1", "FS2": "foxsports2 fs2", "FNC": "foxnews foxnewschannel", "FBN": "foxbusiness foxbusinessnetwork",
    "MSNBC": "msnbc msnow", "BIGTEN": "bigtennetwork btn", "SEC": "secnetwork", "ACC": "accnetwork", "CBSSN": "cbssportsnetwork",
    "OWN": "own oprahwinfreynetwork", "TVLAND": "tvland", "PAR": "paramountnetwork", "LOGO": "logo", "IFC": "ifc",
    "SUNDANC": "sundancetv", "REELZ": "reelz", "BBCA": "bbcamerica", "AXSTV": "axstv axs", "OUTD": "outdoorchannel",
    "SNY": "sny", "YES": "yesnetwork yes", "MASN": "masn", "NEWSMX": "newsmax newsmaxtv", "NEWSNTN": "newsnation",
    "BLOOM": "bloombergtv bloomberg", "CNBCWLD": "cnbcworld", "UP": "uptv", "BYUTV": "byutv", "TBNHD": "tbn",
    "FYISD": "fyi", "VICE": "viceland vice", "POPSD": "poptv pop", "OVATION": "ovation", "GRIT": "grit", "COZITV": "cozitv",
    "METVN": "metv", "BOUNCE": "bounce", "JTV": "jtv", "SHOPHQ": "shophq", "TUDNU": "tudn", "WILLOW2": "willow",
    "HBO": "hbo", "MAX": "cinemax", "STARZ": "starz", "PARSHO": "showtime", "FLIX": "flix", "TMC": "themoviechannel",
    "MGMHD": "mgm mgmplus", "HDNETMV": "hdnetmovies", "LAFF": "laff", "CLEOHD": "cleotv", "TVONEHD": "tvone",
    "RVLTHD": "revolt", "FUSEHD": "fuse", "SCIHD": "sciencechannel", "HSTRYHD": "history", "IONDHD": "ion",
    "MAGN": "magnolia magnolianetwork", "NGMUNDO": "natgeomundo", "FXDEP": "fxdeportes", "GOLTV": "goltv",
    "NHK1HD": "nhkworld", "I24NWEN": "i24news", "RFDHD": "rfdtv", "FETV": "fetv", "WORD": "thewordnetwork",
    "UKIDS": "universalkids", "BABY1": "babyfirst", "CMDTVHD": "comedytv", "JUST": "justiceentral",
}

text = open(PLAYLIST).read() if not PLAYLIST.startswith("http") else urllib.request.urlopen(PLAYLIST, timeout=60).read().decode("utf-8", "replace")
ids = {i for i in re.findall(r'tvg-id="([^"]+)"', text) if i}
by_base = {}
for i in sorted(ids):
    by_base.setdefault(i.split("@")[0], []).append(i)

def files(site):
    fs = sorted(glob.glob(f"sites/{site}/*.channels.xml"))
    # The US list first, then the rest (English entries are preferred below anyway).
    codes = {"us": ("us",), "uk": ("uk", "gb")}.get(COUNTRY, (COUNTRY,))
    mine = lambda f: any(re.search(rf"_{c}\.channels\.xml$", f) for c in codes)
    return sorted(fs, key=lambda f: (0 if mine(f) else 1 if "_all" in f else 2, f))

chosen = {}  # playlist id -> (site, site_id, lang, name)

def compact(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

def norm_name(n):
    s = (n or "").lower()
    s = re.sub(r"[(\[][^)\]]*[)\]]", " ", s)
    s = re.sub(r"\b(hd|sd|fhd|uhd|4k|east|west|feed|tv|channel|united states|usa)\b", " ", s)
    return compact(s)

# Playlist channels by name and by their ID's first part (AMC.us@East -> amc), for Zap2it's codes.
by_name = {}
for m in re.finditer(r'#EXTINF[^\n]*?tvg-id="([^"]+)"[^\n]*,([^\n]+)', text):
    pid, name = m.group(1), re.sub(r"\s*\((\d{3,4}p|\d+k)\)|\s*\[[^\]]*\]", "", m.group(2)).strip()
    for k in {norm_name(name), compact(pid.split("@")[0].split(".")[0])}:
        if k: by_name.setdefault(k, set()).add(pid)

for site in SITES:
    if site == "zap2it.com":
        seen_codes = set()
        for f in files(site):
            for m in re.finditer(r'<channel ([^>]*)>([^<]*)</channel>', open(f, encoding="utf-8").read()):
                attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
                code = m.group(2).strip()
                base = re.sub(r"(HDP|HD|P)$", "", code) if code not in ZAP else code
                if base not in ZAP or base in seen_codes:
                    continue
                seen_codes.add(base)
                for key in ZAP[base].split():
                    for pid in sorted(by_name.get(key, ())):
                        # Zap2it's lineup is the main (East) feed: not West, Spanish or special-event feeds.
                        feed = pid.split("@")[1].lower() if "@" in pid else ""
                        if feed not in ("", "sd", "hd", "east", "easthd", "us", "national"):
                            continue
                        if pid not in chosen:
                            chosen[pid] = (site, attrs["site_id"], "en", code)  # Zap2it's list says "es"; it's English
        continue
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

# Second pass: playlist channels still without a guide, found by channel NAME on the sites (their own lists often
# have no or different IDs). Only lists for this country: i.mjh.nz's "Plex/ca#..." is skipped for the US.
NAME_SITES = [x.strip() for x in os.environ.get("SHELF_NAME_SITES", "").split(",") if x.strip()] or SITES
codes = {"us": ("us",), "uk": ("uk", "gb")}.get(COUNTRY, (COUNTRY,))
def name_key(n):
    s = re.sub(r"\s*\((\d{3,4}p|\d+k)\)|\s*\[[^\]]*\]|\s*\((united states|usa|us)\)", "", (n or "").lower())
    s = re.sub(r"\s+(usa|us|america|east|national)$", "", s.strip())
    s = re.sub(r"\b(hd|tv|channel|network|the)\b", " ", s)
    return compact(s)
wanted = {}
for m in re.finditer(r'#EXTINF[^\n]*?tvg-id="([^"]+)"[^\n]*,([^\n]+)', text):
    if m.group(1) not in chosen:
        k = name_key(m.group(2))
        if len(k) >= 3: wanted.setdefault(k, set()).add(m.group(1))
by_name_found = 0
for site in NAME_SITES:
    for f in files(site):
        country = re.search(r"_([a-z]{2})\.channels\.xml$", f)
        if country and country.group(1) not in codes: continue
        for m in re.finditer(r'<channel ([^>]*)>([^<]*)</channel>', open(f, encoding="utf-8").read()):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            sid = attrs.get("site_id", "")
            c = re.match(r"^[^#]*/([a-z]{2})#", sid)
            if c and c.group(1) not in codes: continue   # another country's feed
            if attrs.get("lang", "en") not in ("en", ""): continue
            for pid in sorted(wanted.get(name_key(m.group(2)), ())):
                if pid not in chosen:
                    chosen[pid] = (site, sid, "en", m.group(2)); by_name_found += 1
print(f"found by name: {by_name_found}")

# Third: a network's local carriers ("Roar.us@KOKITV", "StoryTelevision.us@WCIUTV") show the network's national
# schedule: they share the listing of another feed of that network. Not PBS or local news (their own schedules),
# and not West/Pacific feeds (three hours later).
shared = 0
for pid in sorted(ids):
    if pid in chosen: continue
    base, _, feed = pid.partition("@")
    if base.split(".")[0].lower().startswith(("pbs", "news12", "abc", "cbs", "nbc", "fox", "cw")) or re.search(r"west|pacific|mountain", feed, re.I):
        continue
    sib = next((o for o in by_base.get(base, []) if o in chosen and not re.search(r"west|pacific|mountain", o.partition("@")[2], re.I)), None)
    if sib:
        chosen[pid] = chosen[sib]; shared += 1
print(f"network carriers sharing a feed's listing: {shared}")

# Pictures first: Gracenote (zap2it) stays for cable and premium channels. Every other channel that got a guide
# without pictures (TV Guide, TV Passport, DirecTV, Plex…) or none moves to the free services that have pictures
# for it, best first: the Roku Channel (Gracenote's wide art), Pluto, Samsung TV Plus, WhaleTV+, Distro.
PIC_ORDER = ["roku", "pluto.tv", "pluto", "samsung", "watch.whaletvplus.com", "distro.tv"]
KEEP = {"zap2it.com", "sky.com", "pluto.tv"}
def source_of(site, sid):
    if site != "i.mjh.nz": return site
    t = sid.split("/")[0].lower()
    return "roku" if t.startswith("roku") else "pluto" if t.startswith("pluto") else "samsung" if t.startswith("samsung") else t
pic_index = {}  # key -> (rank, site, sid, name)
for site in ("i.mjh.nz", "pluto.tv", "watch.whaletvplus.com", "distro.tv"):
    for f in files(site):
        country = re.search(r"_([a-z]{2})\.channels\.xml$", f)
        if country and country.group(1) not in codes and site != "i.mjh.nz": continue
        for m in re.finditer(r'<channel ([^>]*)>([^<]*)</channel>', open(f, encoding="utf-8").read()):
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            sid = attrs.get("site_id", "")
            c = re.match(r"^[^#]*/([a-z]{2})#", sid)
            if c and c.group(1) not in codes: continue
            src = source_of(site, sid)
            if src not in PIC_ORDER or (src == "roku" and COUNTRY != "us"): continue   # Roku's guide is the US one
            rank = PIC_ORDER.index(src)
            for k in {name_key(m.group(2)), "id:" + attrs.get("xmltv_id", "").split("@")[0]}:
                if len(k) < 4 or k == "id:": continue
                if k not in pic_index or rank < pic_index[k][0]:
                    pic_index[k] = (rank, site, sid, m.group(2))
pl_names = {m.group(1): m.group(2) for m in re.finditer(r'#EXTINF[^\n]*?tvg-id="([^"]+)"[^\n]*,([^\n]+)', text)}
moved = 0
for pid in sorted(ids):
    cur = chosen.get(pid)
    if cur and (cur[0] in KEEP or source_of(cur[0], cur[1]) in ("roku", "pluto", "samsung")): continue
    hit = pic_index.get("id:" + pid.split("@")[0]) or pic_index.get(name_key(pl_names.get(pid, "")))
    if hit:
        chosen[pid] = (hit[1], hit[2], "en", hit[3]); moved += 1
print(f"moved to a free service with pictures: {moved}")

lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<channels>"]
ORDER = SITES + [x for x in NAME_SITES if x not in SITES]
for pid, (site, sid, lang, name) in sorted(chosen.items(), key=lambda kv: (ORDER.index(kv[1][0]), kv[0])):
    lines.append(f'  <channel site="{site}" site_id="{escape(sid, {chr(34): "&quot;"})}" lang="{lang}" xmltv_id="{escape(pid, {chr(34): "&quot;"})}">{name}</channel>')
lines.append("</channels>")
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

counts = {}
for s, *_ in chosen.values():
    counts[s] = counts.get(s, 0) + 1
print(f"{len(chosen)} of {len(ids)} playlist channels have a guide source:", ", ".join(f"{s} {n}" for s, n in sorted(counts.items(), key=lambda kv: -kv[1])))
