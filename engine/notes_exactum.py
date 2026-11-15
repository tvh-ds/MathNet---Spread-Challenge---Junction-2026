# Dealer-note reader from the EX-ACTUM team's public repository, used unchanged under its MIT licence:
# https://github.com/KasperiBlomberg/EX-ACTUM-BAHN (spread_bot/notes.py)
#
# MIT License
#
# Copyright (c) 2026 Kasperi Blomberg
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Dealer-note reader (fi/sv/en), port of src/notes.js. Follows RULES.md:
days count from arrival; weekday names mean 2..6 days ahead; digits are 24h unless am/pm;
hours in words are working hours 9..17 ("two" = 14:00, "half three" = 14:30); corrections win;
denied times ("not 3pm") are ignored.

The JS regexes use \\p{L} (any letter) next to ASCII-only \\w and \\b. Python's `re` has no \\p{L},
so L below stands for one letter, AW for one ASCII word character, and the boundaries WB/WE for
"not next to a letter or digit"."""
from __future__ import annotations

import re
from typing import Optional

N_DAY = 1440
L = r"[^\W\d_]"          # one letter (JS \p{L})
AW = r"[A-Za-z0-9_]"     # one ASCII word character (JS \w)
WB = r"(?<![^\W_])"      # not after a letter or digit (JS (?<![\p{L}\d]))
WE = r"(?![^\W_])"       # not before a letter or digit

WEEKDAYS_RX = [
    (rf"maanantai{AW}*|måndag{AW}*|monday|mån|mon", 0), (rf"tiistai{AW}*|tisdag{AW}*|tuesday|tues|tue|tis", 1),
    (rf"keskiviik{AW}*|onsdag{AW}*|wednesday|wed|ons", 2), (rf"torstai{AW}*|trostai{AW}*|torsdag{AW}*|thursday|thurs|thur|thu|tors", 3),
    (rf"perjantai{AW}*|fredag{AW}*|friday|fri|fre", 4), (rf"lauantai{AW}*|lördag{AW}*|saturday|sat|lör", 5),
    (rf"sunnuntai{AW}*|söndag{AW}*|sunday|sun|sön", 6),
]
FI_SHORT = {"ma": 0, "ti": 1, "ke": 2, "to": 3, "pe": 4, "la": 5, "su": 6}
REL_DAYS = [
    (rf"day after tomorrow|ylihuomen{L}*|i\s?övermorgon|overmorrow", 2),
    (rf"huo?m+en+a{L}*|hom+en+a{L}*|huomena|i\s?morgon|tomorrow|tomorow|tommorow|tmrw|tmrrw|tmr|2moro", 1),
    (r"tänään|idag|i dag|today|tdy", 0),
]
NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "yksi": 1, "yhdeltä": 1, "yhteen": 1, "kaksi": 2, "kahdelta": 2, "kahteen": 2, "kolme": 3, "kolmelta": 3, "kolmeen": 3, "neljä": 4, "neljältä": 4, "neljään": 4,
    "viisi": 5, "viideltä": 5, "viiteen": 5, "yhdeksän": 9, "yhdeksältä": 9, "kymmenen": 10, "kymmeneltä": 10, "kymmeneen": 10, "yksitoista": 11,
    "yhdeltätoista": 11, "kaksitoista": 12, "kahdeltatoista": 12, "yhdestä": 1, "kahdesta": 2, "kolmesta": 3, "neljästä": 4, "viidestä": 5, "kuusi": 6, "kuudelta": 6, "kuuteen": 6, "kuudesta": 6, "seitsemän": 7, "seitsemältä": 7, "seitsemään": 7, "seitsemästä": 7, "kahdeksan": 8, "kahdeksalta": 8, "kahdeksaan": 8, "kahdeksasta": 8, "yhdeksään": 9, "yhdeksästä": 9, "kymmenestä": 10, "yhdestätoista": 11, "kahdestatoista": 12, "sju": 7, "åtta": 8, "ett": 1, "två": 2, "tre": 3, "fyra": 4, "fem": 5, "nio": 9, "tio": 10, "elva": 11, "tolv": 12,
}
TIME_CUES = r"klo|kl\.?|klockan|at|@|by|before|after|until|till|til|from|ennen|jälkeen|asti|saakka|mennessä|alkaen|lähtien|viimeistään|aikaisintaan|före|efter|innan|från|senast|tidigast|not|ei|inte|ej|but|vaan|utan|men|or|tai|eller|around|noin|ca\.?|cirka|ready|valmis|klar"
DAY_CUES = r"huo?m+en+a|tänään|ylihuomenna|tomorrow|today|idag|imorgon|morgon|maanantaina|tiistaina|keskiviikkona|torstaina|perjantaina|på måndag|på tisdag|på onsdag|på torsdag|på fredag|monday|tuesday|wednesday|thursday|friday|vasta|först|alkaen"
CUE_BEFORE = re.compile(rf"{WB}(?:{TIME_CUES}|{DAY_CUES})\s*$")
UNITS = re.compile(rf"^\s*(?:km|%|€|eur|e(?!{AW})|autoa|auto|cars?|bilar|bil|kpl|st(?!{AW})|min|h(?!{AW})|tuntia|timmar|hours?|pv|days?|päivä)")
NEG = re.compile(rf"{WB}(?:not|ei|inte|ej|no)\s+(?:klo\s+|kl\.?\s+|klockan\s+|at\s+|on\s+|på\s+)?$")
K = {
    "payment": rf"maksu{L}*|maksa{L}*|maksettu|payment|paid|pay(?!{L})|betalning|betald|betalat|invoice|lasku",
    "ready": rf"valmi{L}*|ready|klar(?!{L})|färdig|available|saatavilla|noudettavissa|vapautuu|frigörs",
    "pickup": rf"nouto{L}*|nouda{L}*|noudet{L}*|haku|haett?av{L}*|hakea|pick\s?-?up|pick\s+up|collect{L}*|hämt{L}*|avhämt{L}*|luovutus{L}*|överlämn{L}*|handover|hand-over",
    "site": rf"vastaanot{L}*|receiv{L}*|reception|deliveries\s+(?:until|till)|mottag{L}*|open(?!{L})|auki|öppe{L}*|close{L}*|closing|suljet{L}*|sulke{L}*|sulkeu{L}*|stäng{L}*|kiinni",
    "deadline": rf"perill{L}*|perille|destination|framme|deliver(?:ed|y)?\s+by|must\s+be|oltava|pitää\s+olla|täytyy|needed|tarvitaan|behövs|deadline|latest|viimeistään|senast|mennessä|arrive{L}*|saapu{L}*|toimit{L}*|lever{L}*",
}
DEST = re.compile(r"kohde|vastaanot|receiv|mottag|destination|perill|perille|leverans|framme|määränpää")
KRX = {k: re.compile(v) for k, v in K.items()}
REL_BEFORE = re.compile(r"before|until|till|by|ennen|asti|saakka|mennessä|viimeistään|före|innan|senast|latest")
REL_AFTER = re.compile(r"after|from|jälkeen|alkaen|lähtien|aikaisintaan|earliest|efter|från|tidigast|not\s+before|ei\s+ennen|inte\s+före|ej\s+före|först")
F_MANUAL = re.compile(rf"manuaali{L}*|käsivaiht{L}*|manual(?!{L})|manuell{L}*|stick\s?shift|kopplingspedal")
F_AUTO_NEG = re.compile(r"(?:not|ei|inte|ej)\s+(?:a\s+)?(?:manuaali|manual|manuell)")
F_PLATES = re.compile(rf"no\s+(?:licen[cs]e\s+)?pla+tes|trade\s+pla+tes|pla+tes\s+removed|no\s+reg(?:istration)?\s+pla+tes|without\s+plates|plates?\s+missing|needs?\s+(?:transfer\s+)?plates|unregistered|ei\s+kilpi{L}*|ilman\s+kilpi{L}*|kilvet{L}*|kilpiä\s+ei|kilvet\s+puuttu{L}*|rekisteröimät{L}*|siirtokilp{L}*|koekilp{L}*|koenumer{L}*|inga\s+skyltar|utan\s+skyltar|saknar\s+skyltar|avställd|provskylt{L}*|transfer\s+plates")
F_SUMMER = re.compile(r"kesärenkailla|kesärenkaat\s+alla|kesärenkaat\s+vielä|vielä\s+kesärenkaat|(?:on|still\s+(?:has|on|with))\s+summer\s+t[iy]res|summer\s+t[iy]res\s+(?:on|still|fitted)|på\s+sommardäck|har\s+sommardäck|sommardäck\s+på|fortfarande\s+sommardäck")
DIGIT_RE = re.compile(r"(?<![\d.:])(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?(?:\s*-\s*(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?)?(?!\d)")
WORD_RE = re.compile(WB + r"(?:(half|puoli|halv)\s+)?(" + "|".join(sorted(NUM_WORDS, key=len, reverse=True)) + ")" + WE)
REL_DAY_RX = [(re.compile(WB + "(?:" + rx + ")"), delta) for rx, delta in REL_DAYS]
WEEKDAY_RX = [(re.compile(WB + "(?:" + rx + ")" + WE + r"\.?"), w) for rx, w in WEEKDAYS_RX]
FI_SHORT_RX = re.compile(WB + r"(ma|ti|ke|to|pe|la|su)\.?(?=\s*(?:klo|kl(?!" + AW + r")|$|,)|\.\s*\d)")
SENTENCE_FI_SHORT = re.compile(WB + r"(ma|ti|ke|to|pe|la|su)\.")
NORMALISE = [(re.compile(rf"(?<!{L})viim\."), "viimeistään"), (re.compile(rf"(?<!{L})huom\."), "huom"),
             (re.compile(rf"(?<!{L})n\.(?=\s*\d)"), "noin"), (re.compile(rf"(?<!{L})esim\."), "esim")]


def word_hour(n: int) -> int:
    return n if 9 <= n <= 12 else n + 12


def ampm(h: int, a: Optional[str]) -> int:
    if not a:
        return h
    a = a.replace(".", "")
    if a == "am":
        return 0 if h == 12 else h
    return h if h == 12 else h + 12


def last_pos(rx: "re.Pattern", s: str) -> int:
    pos = -1
    for m in rx.finditer(s):
        pos = m.start()
    return pos


def find_times(s: str) -> list:
    out = []
    for m in DIGIT_RE.finditer(s):
        h0, mi, ap, h2, mi2, ap2 = m.groups()
        h, prefix = int(h0), s[: m.start()]
        cue = bool(CUE_BEFORE.search(prefix[-25:]))
        if UNITS.match(s[m.end():]) and not mi and not ap:
            continue
        if not (mi or ap or cue or h2):
            continue
        if h > 23 or (mi and int(mi) > 59):
            continue
        tod = ampm(h, ap or ap2) * 60 + (int(mi) if mi else 0)
        tod2 = None
        if h2 is not None:
            if int(h2) > 23:
                continue
            tod2 = ampm(int(h2), ap2) * 60 + (int(mi2) if mi2 else 0)
        out.append({"start": m.start(), "end": m.end(), "tod": tod, "tod2": tod2, "denied": bool(NEG.search(prefix))})
    for m in WORD_RE.finditer(s):
        half, word = m.group(1), m.group(2)
        prefix = s[: m.start()]
        if not half and not CUE_BEFORE.search(prefix[-25:]):
            continue
        if UNITS.match(s[m.end():]):
            continue
        n = NUM_WORDS[word]
        tod = (word_hour(n) - 1) * 60 + 30 if half else word_hour(n) * 60
        out.append({"start": m.start(), "end": m.end(), "tod": tod, "tod2": None, "denied": bool(NEG.search(prefix))})
    return sorted(out, key=lambda x: x["start"])


def find_days(s: str, arrival_day: int) -> list:
    """[(position, absolute day, denied)] for each day the sentence names."""
    found, taken = [], []

    def free(i: int) -> bool:
        return not any(a <= i < b for a, b in taken)

    def w_abs(w: int) -> int:
        d = (w - arrival_day % 7) % 7
        if d < 2:
            d += 7
        return arrival_day + d

    for rx, delta in REL_DAY_RX:
        for m in rx.finditer(s):
            if not free(m.start()):
                continue
            taken.append((m.start(), m.end()))
            found.append((m.start(), arrival_day + delta, bool(NEG.search(s[: m.start()]))))
    for rx, w in WEEKDAY_RX:
        for m in rx.finditer(s):
            if not free(m.start()):
                continue
            taken.append((m.start(), m.end()))
            found.append((m.start(), w_abs(w), bool(NEG.search(s[: m.start()]))))
    for m in FI_SHORT_RX.finditer(s):
        if not free(m.start()):
            continue
        found.append((m.start(), w_abs(FI_SHORT[m.group(1)]), bool(NEG.search(s[: m.start()]))))
    return sorted(found, key=lambda x: x[0])


def sentences(t: str) -> list:
    t = re.sub(r"(\d)\.(\d)", r"\1§\2", t)
    t = SENTENCE_FI_SHORT.sub(r"\1¤", t)
    parts = (p.replace("§", ".").replace("¤", ".").strip() for p in re.split(r"[.!?;\n]+", t))
    return [p for p in parts if p]


def classify(sentence: str, tm: dict):
    pre, post = sentence[: tm["start"]], sentence[tm["end"]: tm["end"] + 20]
    window = pre + " " + post
    obj, best = None, -1
    for name, rx in KRX.items():
        p = last_pos(rx, pre)
        if p < 0:
            p = -1 if last_pos(rx, post) < 0 else 0
        if p > best:
            best, obj = p, name
    if KRX["payment"].search(sentence):
        obj = "payment"
    pb, pa = last_pos(REL_BEFORE, window), last_pos(REL_AFTER, window)
    rel = "after" if (pa >= 0 and pa >= pb) else "before" if pb >= 0 else None
    return obj, rel


def parse_note(text: Optional[str], arrival_minute: int) -> dict:
    f: dict = {"ready_at": None, "release_at": None, "deadline_at": None, "pickup_open": None, "pickup_close": None,
               "delivery_close": None, "manual": False, "plates": False, "summer": False, "trace": []}
    if not text:
        return f
    t = text.lower()
    t = re.sub(r"[–—]", "-", t).replace("’", "'")
    t = re.sub(r"\s+", " ", t)
    for rx, rep in NORMALISE:
        t = rx.sub(rep, t)
    t = t.replace("klo.", "klo")
    f["manual"] = bool(F_MANUAL.search(t)) and not F_AUTO_NEG.search(t)
    f["plates"] = bool(F_PLATES.search(t))
    f["summer"] = bool(F_SUMMER.search(t))
    a_day = arrival_minute // N_DAY
    last = None
    for s in sentences(t):
        days = [d for d in find_days(s, a_day) if not d[2]]
        times = find_times(s)
        for tm in times:
            if tm["denied"]:
                continue
            before = [d for d in days if d[0] <= tm["start"]]
            after = [d for d in days if d[0] > tm["start"]]
            explicit_day = before[-1][1] if before else after[0][1] if after else None
            obj, rel = classify(s, tm)
            dest = bool(DEST.search(s))
            if tm["tod2"] is not None:                       # a range is opening hours
                fld = "delivery_close" if dest else "pickup_close"
            elif obj == "site":                              # "liike kiinni klo 16.30"
                fld = "delivery_close" if dest else "pickup_close"
            elif obj == "payment":
                fld = "release_at"
            elif obj == "ready":
                fld = "ready_at"
            elif obj == "pickup":
                fld = "ready_at" if rel == "after" else "pickup_close"
            elif obj == "deadline":
                fld = "deadline_at"
            elif rel == "after":
                fld = "ready_at"
            else:
                fld = last
            if not fld:
                continue
            inherited = f[fld] // N_DAY if (explicit_day is None and fld == last and f[fld] is not None and fld.endswith("_at")) else None
            day = explicit_day if explicit_day is not None else inherited if inherited is not None else a_day
            absolute = day * N_DAY + tm["tod"]
            if fld in ("pickup_close", "delivery_close"):
                if tm["tod2"] is not None:
                    if fld == "pickup_close":
                        f["pickup_open"] = tm["tod"]
                    f[fld] = tm["tod2"]
                else:
                    f[fld] = tm["tod"]
            else:
                f[fld] = absolute
            f["trace"].append(f"{fld}<-{s}")
            last = fld
        if not times and days:
            d = days[-1][1]
            if KRX["ready"].search(s) or KRX["payment"].search(s):
                f["ready_at"] = d * N_DAY + 8 * 60
                last = "ready_at"
            elif KRX["deadline"].search(s):
                f["deadline_at"] = d * N_DAY + 20 * 60
                last = "deadline_at"
    return f
