# Shelf guide

A TV guide for the channels of the [iptv-org US playlist](https://iptv-org.github.io/iptv/countries/us.m3u),
built with this repository's grabber by `.github/workflows/shelf-guide.yml` three times a day and published at:

    https://raw.githubusercontent.com/ganley100/epg/shelf-guide/guide.xml.gz

`make_channels.py` lists the playlist's channels that a guide site covers, one site per channel: Zap2it
(Gracenote, the data cable boxes use, with a poster for every show) for cable channels, Pluto and Plex for
their own channels, then TV Guide and TV Passport, using the playlist's own channel IDs so players match them
directly. `posters.py` makes every show picture a poster (Gracenote's posters, Pluto's 2:3 posters). Run by hand with Actions → Shelf guide → Run workflow.
