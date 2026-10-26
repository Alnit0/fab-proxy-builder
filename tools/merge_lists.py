"""Merge two card lists, keeping the first as the main source.

Cards from the second list are added only when the first list doesn't have them,
either as a card (same name and pitch) or as the back face of another card.

Usage: python3 merge_lists.py main.json extra.json out.json
"""
import json
import sys

main = json.load(open(sys.argv[1], encoding="utf-8"))
extra = json.load(open(sys.argv[2], encoding="utf-8"))

have = {(r[0].lower(), r[1]) for r in main}
names = {r[0].lower() for r in main}
aliases = {a.lower() for r in main for a in r[4]}

added = [r for r in extra
         if (r[0].lower(), r[1]) not in have
         and r[0].lower() not in aliases
         and not (r[1] == 0 and r[0].lower() in names)]
rows = main + added
rows.sort(key=lambda r: (r[0].lower(), r[1]))
json.dump(rows, open(sys.argv[3], "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print(f"{len(main)} from the main list + {len(added)} extra = {len(rows)} cards")
if added:
    print("Extra cards:", ", ".join(r[0] for r in added[:60]) + (" ..." if len(added) > 60 else ""))
