<div align="center">

# slop-lock

**Flag AI tells in a draft, then prove the rewrite kept every number, citation and link.**

Humanizer skills fix the tone; nobody checks that "P=0.02" is still "P=0.02" afterwards. This joins a style sweep and a content lock in one stdlib-only Python file.

Works with **Claude Code** and **Codex**.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg) ![Status: prototype](https://img.shields.io/badge/status-prototype-orange.svg)

</div>

## Quick start
```bash
git clone https://github.com/Dodai0419/slop-lock && cd slop-lock
python slop_lock.py check examples/before.md
python slop_lock.py diff examples/before.md examples/tampered.md --strict
```
```
AI words: ['underscore', 'interplay']
AI phrases: ['shed light on']
filler hedges: ['it is worth noting']
status: FAIL  (differences are review signals, not proof of a wrong edit)
  [HIGH] numbers: 6 -> 6  removed ['1', '1', 'P=0.02']  added ['2', '2', 'P=0.05']
  [HIGH] citations: 2 -> 2  removed ['[1]', '[1]']  added ['[2]', '[2]']
```

## The problem
- AI drafts share tells: "delve", "Moreover,", em dashes, "not just X, but Y", every sentence the same length.
- When an LLM rewrites to remove them, it quietly changes numbers, drops citations, or turns "does not establish" into "establishes".
- Two separate tools existed for these two halves; the content-lock one also crashed on Windows consoles when printing an em dash.

## The solution
| Idea | Fixes |
|------|-------|
| **`check`**: deterministic sweep for dashes, stock AI words and phrases, filler transitions, hedges, pause-and-point lines, sentence rhythm | Shows where to look, never rewrites |
| **`diff`**: multiset compare of numbers, p-values, units, citations (numeric, author-year, LaTeX), DOIs, URLs, code and math spans, your own terms | `FAIL` + exit 1 under `--strict` when any fact moved |
| **Stance markers**: negation, modality, causal wording | `REVIEW` when a claim got stronger or weaker |

## Use with Claude Code
```bash
/plugin marketplace add Dodai0419/slop-lock
/plugin install slop-lock@slop-lock
```

## Use with Codex (ChatGPT)
```bash
git clone https://github.com/Dodai0419/slop-lock && cp -r slop-lock/skills/* ~/.codex/skills/
```
Or copy `AGENTS.md` into your project root.

## Benchmarks
Input: `examples/before.md` and `examples/after.md` repeated 50 times (about 19k and 12k words). Best of 5 runs, Windows 11, Python 3.11.1. Two benchmark runs; both shown.

| | upstream | slop-lock |
|-|-|-|
| `check` (vs work-humanizer `check.py`) | 632 / 675 ms | 128 / 140 ms |
| `diff` in-process (vs academic-deai `content_lock.build_report`) | 419 / 422 ms | 400 / 387 ms |
| `diff` CLI on the original pair, incl. Python startup | 966 / 1442 ms | 636 / 688 ms |
| lines of code | 87 + 755 + 125 (`check.py`, `content_lock.py`, `text_io.py`) | 237 |
| dependencies | 0 | 0 |

`check` is faster because each AI word and transition is first tested with a plain substring search; the regex only runs when the word is actually there. Output is unchanged.
Correctness: `tests/upstream_expected.json` holds the output of both upstream tools on the three example files; the tests check `check` lines and every `diff` category match exactly.
Scope cut: English only, plain text and Markdown/LaTeX input (upstream also reads `.docx`/`.pdf` and Chinese stance words).

## Inspired by
- [phuryn/work-humanizer](https://github.com/phuryn/work-humanizer) — the AI-tell sweep word lists and rules (MIT).
- [heise3/academic-deai](https://github.com/heise3/academic-deai) — the content-lock extractors and pass/review/fail logic (MIT). Example texts are its synthetic English case.

## Roadmap
- [ ] Line numbers for every `check` hit
- [ ] Git pre-commit hook mode for docs folders

## License
MIT
