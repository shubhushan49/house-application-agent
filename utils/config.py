import os

WG_USERNAME = os.getenv("WG_GESUCHT_USERNAME")
WG_PASSWORD = os.getenv("WG_GESUCHT_PASSWORD")
CITY = os.getenv("CITY")
WG_ZIMMER_INTRO = os.getenv("WG_ZIMMER_INTRO", "").replace("<nn>", "\n")
OTHER_INTRO = os.getenv("OTHER_INTRO", "").replace("<nn>", "\n")