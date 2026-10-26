"""Build the proxy builder's card list from Fabrary's published card data.

Reads dist/cards.js from the @flesh-and-blood/cards npm package as plain text
(the file is never executed) and writes a compact JSON list:

    [name, pitch, typeText, arts, aliases]
    arts = [[imageStem, label, tcgplayerId, backImageStem?], ...]

Usage: python3 fabrary_index.py path/to/cards.js out.json
"""
import json
import re
import sys

TREATMENTS = {"AB": "Alternate Border", "AA": "Alternate Art", "AT": "Alternate Text",
              "EA": "Extended Art", "FA": "Full Art"}


# ---------- a small reader for JavaScript object/array literals ----------
class Reader:
    def __init__(self, s, i):
        self.s, self.i = s, i

    def ws(self):
        s, n = self.s, len(self.s)
        while self.i < n and s[self.i] in " \t\r\n":
            self.i += 1

    def peek(self):
        self.ws()
        return self.s[self.i]

    def expect(self, ch):
        self.ws()
        if self.s[self.i] != ch:
            raise ValueError(f"expected {ch!r} at {self.i}: {self.s[self.i:self.i + 60]!r}")
        self.i += 1

    def value(self):
        c = self.peek()
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c == '"' or c == "'":
            return self.string(c)
        if c == "`":
            return self.template()
        if c == "!":
            self.i += 1
            v = self.value()
            return not v if isinstance(v, (bool, int, float)) else False
        if c == "-" or c.isdigit() or c == ".":
            m = re.compile(r"-?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?", re.I).match(self.s, self.i)
            self.i = m.end()
            t = m.group(0)
            return float(t) if any(x in t for x in ".eE") else int(t)
        m = re.compile(r"[A-Za-z_$][\w$]*").match(self.s, self.i)
        if not m:
            raise ValueError(f"unexpected {self.s[self.i:self.i + 60]!r} at {self.i}")
        self.i = m.end()
        word = m.group(0)
        if word == "true":
            return True
        if word == "false":
            return False
        if word in ("null", "undefined"):
            return None
        if word == "void":
            self.value()
            return None
        # enum member such as g.Illusionist or a["Some Name"]: keep the member name
        val = word
        while True:
            self.ws()
            if self.s.startswith(".", self.i) and not self.s.startswith("...", self.i):
                self.i += 1
                m = re.compile(r"[A-Za-z_$][\w$]*").match(self.s, self.i)
                self.i = m.end()
                val = m.group(0)
            elif self.s.startswith("[", self.i):
                self.i += 1
                val = self.value()
                self.expect("]")
            else:
                break
        return val

    def string(self, q):
        self.i += 1
        out, s = [], self.s
        while True:
            c = s[self.i]
            if c == "\\":
                nxt = s[self.i + 1]
                if nxt == "u":
                    if s[self.i + 2] == "{":
                        end = s.index("}", self.i)
                        out.append(chr(int(s[self.i + 3:end], 16)))
                        self.i = end + 1
                    else:
                        out.append(chr(int(s[self.i + 2:self.i + 6], 16)))
                        self.i += 6
                    continue
                if nxt == "x":
                    out.append(chr(int(s[self.i + 2:self.i + 4], 16)))
                    self.i += 4
                    continue
                out.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}.get(nxt, nxt))
                self.i += 2
                continue
            if c == q:
                self.i += 1
                return "".join(out)
            out.append(c)
            self.i += 1

    def template(self):
        self.i += 1
        out, s = [], self.s
        while True:
            c = s[self.i]
            if c == "\\":
                out.append(s[self.i + 1])
                self.i += 2
                continue
            if c == "$" and s[self.i + 1] == "{":
                raise ValueError("template expressions are not supported")
            if c == "`":
                self.i += 1
                return "".join(out)
            out.append(c)
            self.i += 1

    def key(self):
        c = self.peek()
        if c in "\"'":
            return self.string(c)
        if c == "[":
            self.i += 1
            k = self.value()
            self.expect("]")
            return str(k)
        m = re.compile(r"[\w$]+").match(self.s, self.i)
        self.i = m.end()
        return m.group(0)

    def obj(self):
        self.expect("{")
        d = {}
        while self.peek() != "}":
            k = self.key()
            self.expect(":")
            d[k] = self.value()
            if self.peek() == ",":
                self.i += 1
        self.i += 1
        return d

    def arr(self):
        self.expect("[")
        a = []
        while self.peek() != "]":
            if self.s.startswith("...", self.i):
                raise ValueError("spread inside data array")
            a.append(self.value())
            if self.peek() == ",":
                self.i += 1
        self.i += 1
        return a


def read_cards(path):
    s = open(path, encoding="utf-8").read()
    # Data arrays look like  R=[{artists:...},...]  and are combined at the end with L=[...R,...A].
    spread = re.search(r"(\w+)=\[((?:\.\.\.\w+,?)+)\];export\{\1 as cards\}", s)
    if not spread:
        raise SystemExit("Couldn't find the cards export. The package format may have changed.")
    names = re.findall(r"\.\.\.(\w+)", spread.group(2))
    cards = []
    for name in names:
        m = re.search(r"[,\s]" + re.escape(name) + r"=\[\{", s) or re.search(r"const " + re.escape(name) + r"=\[\{", s)
        if not m:
            raise SystemExit(f"Couldn't find data array {name}.")
        r = Reader(s, m.end() - 2)
        cards.extend(r.arr())
    return cards


# ---------- turn Fabrary cards into the page's compact list ----------
def build(cards):
    by_id = {c["cardIdentifier"]: c for c in cards}

    def is_back_stem(stem):
        return stem.endswith("_BACK")

    def foil_score(stem):
        # prefer the plain printing's image over foil or unlimited copies of the same art
        score = 0
        if stem.startswith("U-"):
            score += 1
        if re.search(r"-(RF|CF|GF|MV|TP)$", stem):
            score += 2
        return score

    rows, back_only = [], []
    for c in cards:
        printings = [p for p in c.get("printings", []) if p.get("image")]
        if not printings:
            continue
        all_images = {p["image"] for p in printings}
        if c.get("isCardBack"):
            back_only.append(c)
            continue
        arts = {}
        for p in printings:
            stem = p["image"]
            if is_back_stem(stem):
                continue
            treat = tuple(p.get("treatments") or [])
            key = (p.get("identifier") or stem, treat)
            back = p.get("oppositeImage")
            if not back and (stem + "_BACK") in all_images:
                back = stem + "_BACK"
            tcg = (p.get("tcgplayer") or {}).get("productId") or ""
            cand = (foil_score(stem), stem, p, back, int(tcg) if str(tcg).isdigit() else 0)
            if key not in arts or cand[0] < arts[key][0]:
                arts[key] = cand
        if not arts:
            back_only.append(c)
            continue
        vals = list(arts.values())
        # standard art first, then single-sided before double-sided, then newest printing first
        vals.sort(key=lambda v: (1 if v[2].get("treatments") else 0, 1 if v[3] else 0))
        entries = []
        for _, stem, p, back, tcg in vals:
            label = p.get("identifier") or stem
            if p.get("treatments"):
                label += " · " + ", ".join(TREATMENTS.get(t, t) for t in p["treatments"])
            e = [stem, label, tcg]
            if back:
                e.append(back)
            entries.append(e)
        pitch = c.get("pitch")
        rows.append([c["name"], pitch if isinstance(pitch, int) else 0, c.get("typeText") or "", entries, [], c["cardIdentifier"]])

    # back-face names become search aliases of the card they belong to
    row_by_id = {r[5]: r for r in rows}
    for c in back_only:
        for other in c.get("oppositeSideCardIdentifiers") or [c.get("oppositeSideCardIdentifier")]:
            r = row_by_id.get(other)
            if r and c["name"] not in r[4]:
                r[4].append(c["name"])

    for r in rows:
        r.pop()  # drop the identifier, the page doesn't need it
    rows.sort(key=lambda r: (r[0].lower(), r[1]))
    return rows


if __name__ == "__main__":
    cards = read_cards(sys.argv[1])
    rows = build(cards)
    json.dump(rows, open(sys.argv[2], "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print(f"{len(cards)} card faces read; {len(rows)} cards; {sum(len(r[3]) for r in rows)} arts; "
          f"{sum(1 for r in rows if any(len(e) > 3 for e in r[3]))} with double-sided printings")
