#!/usr/bin/env python3
"""slop-lock: flag AI tells in a draft, then prove the rewrite kept every number, citation and link.

  python slop_lock.py check FILE            AI-tell sweep (from phuryn/work-humanizer, MIT)
  python slop_lock.py diff BEFORE AFTER     content lock (from heise3/academic-deai, MIT)

Standard library only. Flags are prompts to look, not verdicts.
"""
import argparse
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter

# ---------- check: AI-tell sweep ----------
AI_WORDS = ("delve bolster illuminate elucidate transcend intertwine espouse exemplify "
            "underpin underscore tapestry synergy beacon interplay intricacies intricate "
            "symphony kaleidoscope myriad plethora advancements vibrant meticulous "
            "cutting-edge game-changing unparalleled commendable indelible poignant "
            "tireless unwavering unyielding timeless ever-evolving").split()
AI_PHRASES = ["shed light on", "grapple with", "important to note", "stands as a testament",
              "navigate the complexities", "key takeaway", "paving the way", "look no further",
              "that being said", "in today's fast-paced", "ever-changing landscape",
              "harness the power", "thrilled to announce", "excited to announce"]
MARKETING = ["empower", "unlock", "elevate", "seamless", "streamline", "revolutioniz",
             "supercharge", "next-level", "best-in-class", "world-class", "game-changer"]
TRANSITIONS = ["Additionally", "Furthermore", "Moreover", "However", "Importantly", "Critically",
               "Notably", "Ultimately", "Therefore", "In fact", "In conclusion", "Lastly",
               "That said", "Needless to say", "In other words"]
POINTING = [r"here'?s (the thing|what|why)", r"let me (be clear|explain)", r"let'?s (break|dive)",
            r"^[A-Z][^.:!?\n]{2,40}: [a-z]", r"notice how", r"as you can see", r"this means that",
            r"what do you think\?", r"\bthoughts\?\s*$", r"the bottom line", r"let that sink in",
            r"it'?s not (just )?(about )?[^.]{1,40}[,.;] it'?s", r"\bnot just\b[^.]{1,60}\bbut\b"]
HEDGES = ["arguably", "it's worth noting", "it is worth noting", "could potentially",
          "it's important to note", "it is important to note"]
OPENER_WORDS = {"the", "it's", "that's", "this", "you", "it", "these"}

# compiled once; a plain substring test runs first so absent words never reach the regex engine
_WORD_RE = [(w, re.compile(r"\b" + re.escape(w))) for w in AI_WORDS]
_TRANS_RE = [(t, re.compile(r"(^|[.!?]\s+|\n)" + t + r"\b")) for t in TRANSITIONS]
_POINT_RE = [re.compile(p, re.I | re.M) for p in POINTING]
_DASH_RE = re.compile(r" – | -- ")
_BOLD_RE = re.compile(r"^\s*\*\*[^*]{1,60}(?:\*\*[.:]|[.:]\*\*)", re.M)
_SENT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def sentences(text):
    return [p.strip() for p in _SENT_RE.split(text) if len(p.strip().split()) >= 2]


def check(text):
    low, out = text.lower(), []

    def flag(label, hits):
        if hits:
            out.append(f"{label}: {hits}")

    flag("em/en dashes", text.count("—") + len(_DASH_RE.findall(text)))
    flag("semicolons", text.count(";"))
    flag("AI words", [w for w, r in _WORD_RE if w in low and r.search(low)])
    flag("AI phrases", [p for p in AI_PHRASES if p in low])
    flag("marketing words", [w for w in MARKETING if w in low])
    flag("filler transitions", [t for t, r in _TRANS_RE if t in text and r.search(text)])
    flag("pause-and-point / closers / contrasts", [m.group(0)[:50] for r in _POINT_RE for m in r.finditer(text)])
    flag("filler hedges", [h for h in HEDGES if h in low])
    flag("bold-label starts", len(_BOLD_RE.findall(text)))
    flag("exclamation marks", text.count("!"))
    sents = sentences(text)
    lens = [len(s.split()) for s in sents]
    if len(lens) >= 4:
        med, mean = statistics.median(lens), statistics.mean(lens)
        band = sum(1 for x in lens if abs(x - med) <= 5) / len(lens)
        note = (" (uniform: merge short ones)" if mean < 11 else " (uniform: vary)") if band >= 0.7 else ""
        out.append(f"sentences: {len(lens)}, mean {mean:.1f} words, {band:.0%} within 5 words of the median{note}")
        share = sum(1 for s in sents if s.split()[0].lower().strip('"\'') in OPENER_WORDS) / len(sents)
        if share >= 0.4:
            out.append(f"openers: {share:.0%} of sentences start with The/It/This/That/You")
    out.append(f"words: {len(text.split()) or 1}")
    return out


# ---------- diff: content lock ----------
_NUM = r"[+\-\u2212]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][+\-\u2212]?\d+)?"
_UNITS = ("mmol/L mol/L mg/dL ng/mL µg/mL μg/mL kg/m2 kg/m² kHz MHz mmHg bpm mL µL μL ms min Hz kPa Pa °C "
          "kg mg ng µg μg mm cm km mol mmol L g m s h K").split()
_UNIT = "|".join(re.escape(u) for u in sorted(_UNITS, key=len, reverse=True))
NUMBER_RE = re.compile(rf"(?<![\w.])(?:[pP]\s*(?:=|<|>|≤|≥)\s*{_NUM}|{_NUM}(?:\s*(?:%|{_UNIT}))?)(?!\w)")
_AUTHOR = r"(?:(?:(?i:van|von|de|del|della|der|den|la|le|du)\s+){1,3})?[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’\-]+"
_GROUP = rf"{_AUTHOR}(?:\s+(?:et\s+al\.|&\s+{_AUTHOR}|and\s+{_AUTHOR}))?"
_YEAR = r"(?:19|20)\d{2}[a-z]?"
CITE_RES = (re.compile(rf"(?<!\w){_GROUP}\s*\({_YEAR}\)"),
            re.compile(rf"\({_GROUP},\s*{_YEAR}(?:\s*;\s*{_GROUP},\s*{_YEAR})*\)"),
            re.compile(r"\[\s*\d+(?:\s*[-–—]\s*\d+)?(?:\s*[,;]\s*\d+(?:\s*[-–—]\s*\d+)?)*\s*\]"))
LATEX_CITE_RE = re.compile(r"\\(?P<cmd>cite[A-Za-z]*|(?:paren|text|auto|foot|smart|super|full|no)cites?)\*?")
LATEX_ARG_RE = re.compile(r"\s*(?:\[[^\]]*\]\s*){0,2}\{(?P<keys>[^{}]+)\}")
ID_RES = (re.compile(r"(?<!\w)10\.\d{4,9}/[^\s<>\"']+", re.I), re.compile(r"https?://[^\s<>\"']+", re.I))
FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[^\n]*(?:\n|$)", re.M)
_ENVS = "displaymath equation equation* align align* alignat alignat* flalign flalign* gather gather* multline multline* split math".split()
SPAN_RES = (re.compile(rf"\\begin\{{(?P<env>{'|'.join(map(re.escape, _ENVS))})\}}.*?\\end\{{(?P=env)\}}", re.S),
            re.compile(r"(?<!\\)\$\$.*?(?<!\\)\$\$", re.S),
            re.compile(r"(?<!\\)\\\[.*?(?<!\\)\\\]", re.S),
            re.compile(r"(?<!\\)\\\(.*?(?<!\\)\\\)", re.S),
            re.compile(r"(?<!`)(?P<ticks>`+)(?!`)(?P<body>[^\n]*?)(?<!`)(?P=ticks)(?!`)"),
            re.compile(r"(?<![\\$])\$(?!\$)[^\n$]*?(?<!\\)\$(?!\$)"))


def _terms_re(terms):
    return re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b", re.I)


NEG_RE = _terms_re("neither without never none not no nor".split())
NEG_FORM_RE = re.compile(r"\b(?:cannot|[A-Za-z]+n['’]t)\b", re.I)
MODAL_RE = _terms_re("might could would should must shall may can".split())
CAUSAL_RE = _terms_re(["resulted in", "results in", "result in", "led to", "leads to", "lead to", "associating with",
                       "associated with", "associates with", "associate with", "preventing", "prevented", "prevents",
                       "prevent", "producing", "produced", "produces", "produce", "causing", "caused", "causes",
                       "cause", "due to", "because"])
CATEGORIES = ("numbers", "citations", "identifiers", "protected_spans", "terms",
              "stance_negation", "stance_modality", "stance_causal")
HIGH_RISK = set(CATEGORIES[:5])


def _overlaps(span, taken):
    return any(span[0] < e and s < span[1] for s, e in taken)


def _trim(value):
    value = value.rstrip(".,;:!?")
    while True:
        prev = value
        for o, c in (("(", ")"), ("[", "]"), ("{", "}")):
            if value.endswith(c) and value.count(c) > value.count(o):
                value = value[:-1]
        if value == prev:
            return value


def _citations(t):
    out, taken = Counter(), []
    for m in LATEX_CITE_RE.finditer(t):
        pos = last = m.end()
        plural = m.group("cmd").lower().endswith("cites")
        while (a := LATEX_ARG_RE.match(t, pos)) is not None:
            out.update(k.strip() for k in a.group("keys").split(",") if k.strip())
            pos = last = a.end()
            if not plural:
                break
        if last != m.end():
            taken.append((m.start(), last))
    for r in CITE_RES:
        for m in r.finditer(t):
            if not _overlaps(m.span(), taken):
                out[m.group(0)] += 1
                taken.append(m.span())
    return out


def _spans(t):
    cands = []
    for m in FENCE_RE.finditer(t):  # CommonMark: closer uses the same char and is at least as long
        f = m.group("fence")
        close = re.compile(rf"^ {{0,3}}(?P<fence>{re.escape(f[0])}{{{len(f)},}})(?=[ \t]*(?:\n|$|[.,;:!?]))", re.M).search(t, m.end())
        if close:
            cands.append((m.start(), close.end("fence")))
    cands += [m.span() for r in SPAN_RES for m in r.finditer(t)]
    out, taken = Counter(), []
    for span in sorted(set(cands), key=lambda s: (s[0], -s[1])):  # outer span wins
        if not _overlaps(span, taken):
            out[t[span[0]:span[1]]] += 1
            taken.append(span)
    return out


def snapshot(text, terms=()):
    t = unicodedata.normalize("NFKC", text)
    neg_forms = list(NEG_FORM_RE.finditer(t))
    excl = [m.span() for m in neg_forms]
    terms = list(dict.fromkeys(unicodedata.normalize("NFKC", x.strip()) for x in terms if x.strip()))
    return {
        "numbers": Counter(m.group(0) for m in NUMBER_RE.finditer(t)),
        "citations": _citations(t),
        "identifiers": Counter(v for r in ID_RES for v in map(_trim, (m.group(0) for m in r.finditer(t))) if v),
        "protected_spans": _spans(t),
        "terms": Counter({x: t.count(x) for x in terms if t.count(x)}),
        "stance_negation": Counter(m.group(0).lower() for m in NEG_RE.finditer(t)) + Counter(m.group(0).lower() for m in neg_forms),
        "stance_modality": Counter(m.group(0).lower() for m in MODAL_RE.finditer(t) if not _overlaps(m.span(), excl)),
        "stance_causal": Counter(m.group(0).lower() for m in CAUSAL_RE.finditer(t)),
    }


def lock(before, after, terms=()):
    b, a = snapshot(before, terms), snapshot(after, terms)
    cats = {c: {"before_count": sum(b[c].values()), "after_count": sum(a[c].values()),
                "removed": sorted((b[c] - a[c]).elements()), "added": sorted((a[c] - b[c]).elements())}
            for c in CATEGORIES}
    changed = {c for c, v in cats.items() if v["removed"] or v["added"]}
    status = "fail" if changed & HIGH_RISK else "review" if changed else "pass"
    return {"status": status, "categories": cats}


def render(rep):
    out = [f"status: {rep['status'].upper()}  (differences are review signals, not proof of a wrong edit)"]
    for c, v in rep["categories"].items():
        if v["removed"] or v["added"]:
            risk = "HIGH" if c in HIGH_RISK else "warn"
            out.append(f"  [{risk}] {c}: {v['before_count']} -> {v['after_count']}"
                       + (f"  removed {v['removed']}" if v["removed"] else "") + (f"  added {v['added']}" if v["added"] else ""))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="flag AI tells in one file ('-' for stdin)")
    c.add_argument("file")
    d = sub.add_parser("diff", help="compare numbers, citations, links, code and stance between two files")
    d.add_argument("before")
    d.add_argument("after")
    d.add_argument("--terms-file", help="one exact protected term per line")
    d.add_argument("--strict", action="store_true", help="exit 1 when a high-risk category differs")
    d.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # upstream content_lock crashed printing em dashes on cp949/cp1252 consoles
    read = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8-sig").read()
    if a.cmd == "check":
        print("\n".join(check(read(a.file))))
        return 0
    terms = read(a.terms_file).splitlines() if a.terms_file else ()
    rep = lock(read(a.before), read(a.after), terms)
    print(json.dumps(rep, ensure_ascii=False, indent=2) if a.json else render(rep))
    return 1 if a.strict and rep["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
