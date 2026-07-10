"""One-off/rescue harvester: python3 scripts/harvest_subset.py p40 p100"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import db
from observatory import cardmap, ingest_prices

keys = set(sys.argv[1:])
orig = cardmap.load_catalog
cardmap.load_catalog = lambda: [c for c in orig() if c["key"] in keys]
db.init()
print(ingest_prices.run())
