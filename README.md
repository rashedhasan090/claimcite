# claimcite

**Offline claim↔citation coverage for Markdown and LaTeX research drafts.**

Grad students and paper authors often sprinkle citations near *some* claims and leave others floating. `claimcite` is a tiny CLI that finds assertive claim sentences, maps each to nearby citation markers, and reports **uncovered claims**, **orphan citations**, and a **coverage score** — ready for local review or CI.

## Why this is novel

Most citation tools check whether a BibTeX key *exists*. Hedging tools (e.g. hedgescope) score cautious language. **claimcite** instead measures *spatial* claim↔citation coverage in the draft itself: is there a `\cite{}` / `[@key]` / footnote within a character window of each assertive claim?

It is deliberately heuristic and offline (stdlib-only Python) — a triage aid, not a semantic fact-checker.

## Install

```bash
pip install -e .
# or run without install:
PYTHONPATH=src python -m claimcite examples/sample.md
```

## Usage

```bash
claimcite draft.md
claimcite thesis.tex --window 300
claimcite chapter.md --max-uncovered 0          # CI gate
claimcite notes.md --min-coverage 0.8 --json
```

### Demo

```bash
python -m claimcite examples/sample.md
```

Example output shape:

```
claimcite — examples/sample.md
window=240  claims=N  citations=M  coverage=XX%

Uncovered claims (1):
  […] Our evaluation demonstrates a clear improvement…

Orphan citations: …
Covered (sample):
  d=12 keys=['smith2024'] :: We show that the mesh router…
```

## What counts as a claim / citation

- **Claims**: sentences with assertive research cues (`show`, `demonstrate`, `outperform`, `significant`, `we find`, …), skipping soft future-work hedges and bibliography/related-work sections when headed as such.
- **Citations**: Pandoc `[@key]`, LaTeX `\cite{…}` / `\citep{…}` (and common biblatex aliases), Markdown footnotes `[^id]`.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | OK (or within `--max-uncovered` / `--min-coverage`) |
| 1 | Coverage gate failed |
| 2 | Bad usage / missing file |

## License

MIT © Rashed Hasan
