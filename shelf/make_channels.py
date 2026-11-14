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
    return sorted(fs, key=lambda f: (0 if re.search(r"_us\.channels\.xml$", f) else 1 if "_all" in f else 2, f))

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

lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<channels>"]
for pid, (site, sid, lang, name) in sorted(chosen.items(), key=lambda kv: (SITES.index(kv[1][0]), kv[0])):
    lines.append(f'  <channel site="{site}" site_id="{escape(sid, {chr(34): "&quot;"})}" lang="{lang}" xmltv_id="{escape(pid, {chr(34): "&quot;"})}">{name}</channel>')
lines.append("</channels>")
open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")

counts = {}
for s, *_ in chosen.values():
    counts[s] = counts.get(s, 0) + 1
print(f"{len(chosen)} of {len(ids)} playlist channels have a guide source:", ", ".join(f"{s} {n}" for s, n in sorted(counts.items(), key=lambda kv: -kv[1])))
