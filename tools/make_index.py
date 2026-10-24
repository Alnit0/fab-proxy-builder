"""Build a compact FAB card index (names, pitch, types, art stems) for the proxy builder."""
import json, sys, re
src = sys.argv[1]
d = json.load(open(f"{src}/card.json"))
fa = json.load(open(f"{src}/card-face-association.json"))
avn = {a["id"]: a["name"] for a in json.load(open(f"{src}/art-variation.json"))}

def stem(p):
    u = p.get("image_url") or ""
    return u.rsplit("/", 1)[-1].rsplit(".", 1)[0] if u else None

pstem = {}
for c in d:
    for p in c["printings"]:
        pstem[p["unique_id"]] = stem(p)

back_of = {}   # front stem -> back stem
back_stems = set()
for x in fa:
    f, b = pstem.get(x["front_unique_id"]), pstem.get(x["back_unique_id"])
    if f and b and (x["is_DFC"] or b.endswith("_BACK")):
        back_of[f] = b
        back_stems.add(b)

def pref(s, p):
    # lower is better: plain stem, then unlimited, then foil variants
    score = 0
    if s.startswith("U-"): score += 1
    if re.search(r"-(RF|CF|GF|MV)$", s.replace("_BACK", "")): score += 2
    return score

out = []
alias_for = {}  # back-face card name -> front index
cards_tmp = []
for c in d:
    arts = {}
    for p in c["printings"]:
        s = stem(p)
        if not s:
            continue
        key = (p["id"], tuple(p["art_variations"]))
        cand = (pref(s, p), s, p)
        if key not in arts or cand[0] < arts[key][0]:
            arts[key] = cand
    if not arts:
        continue
    stems_all = [v[1] for v in arts.values()]
    if all(s in back_stems for s in stems_all):
        cards_tmp.append(("BACKONLY", c, arts))
        continue
    # back-face images belong on the back, not in the list of front arts
    arts = {k: v for k, v in arts.items() if v[1] not in back_stems}
    cards_tmp.append(("CARD", c, arts))

name_to_idx = {}
for kind, c, arts in cards_tmp:
    if kind != "CARD":
        continue
    entries = []
    # keep data order (newest first), standard art before variants
    vals = list(arts.values())
    # standard art first, and single-sided printings before double-sided ones
    vals.sort(key=lambda v: (1 if v[2]["art_variations"] else 0, 1 if v[1] in back_of else 0))
    for _, s, p in vals:
        label = p["id"]
        if p["art_variations"]:
            label += " · " + ", ".join(avn.get(a, a) for a in p["art_variations"])
        e = [s, label, int(p["tcgplayer_product_id"]) if (p.get("tcgplayer_product_id") or "").isdigit() else 0]
        if s in back_of:
            e.append(back_of[s])
        entries.append(e)
    pitch = c.get("pitch") or ""
    out.append([c["name"], int(pitch) if pitch.isdigit() else 0, c.get("type_text") or "", entries, []])
    name_to_idx.setdefault(c["name"], len(out) - 1)

# aliases: back-face card names point at their front card
stem_to_idx = {}
for i, row in enumerate(out):
    for e in row[3]:
        if len(e) > 3:
            stem_to_idx[e[3]] = i
for kind, c, arts in cards_tmp:
    if kind == "BACKONLY":
        for v in arts.values():
            i = stem_to_idx.get(v[1])
            if i is not None and c["name"] not in out[i][4]:
                out[i][4].append(c["name"])
                break

out.sort(key=lambda r: (r[0].lower(), r[1]))
json.dump(out, open(sys.argv[2], "w"), separators=(",", ":"), ensure_ascii=False)
print(len(out), "cards;", sum(len(r[3]) for r in out), "arts;", sum(1 for r in out if r[4]), "with back faces")
