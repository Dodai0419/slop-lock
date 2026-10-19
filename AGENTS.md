# slop-lock

Use this when editing or "humanizing" text (README, email, post, paper abstract) so it stops sounding machine-written without changing what it says.

## Steps
1. Save the draft to a file and run `python slop_lock.py check draft.md` from the repo root. Each line is a prompt to look: em dashes, stock AI words, filler transitions, pause-and-point lines, hedges, uniform sentence rhythm.
2. Rewrite only the flagged spots. Keep the author's claims, numbers and voice.
3. Save the rewrite and run `python slop_lock.py diff draft.md rewrite.md --strict`.
   - `FAIL` (exit 1): a number, citation, DOI/URL, code span or protected term changed. Restore it.
   - `REVIEW`: negation, modality ("may", "must") or causal wording changed. Check the claim did not get stronger or weaker.
   - `PASS`: nothing observable changed.
4. Add `--terms-file terms.txt` (one exact term per line) to lock product names or jargon; add `--json` for machine-readable output.

## Rules
- A flag is not a verdict; never rewrite text that is already plain just to silence a count.
- Never report PASS unless the diff command printed it.
