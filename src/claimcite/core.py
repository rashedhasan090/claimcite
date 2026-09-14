"""Claim↔citation proximity analysis for Markdown / LaTeX drafts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

CITE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("pandoc", re.compile(r"\[@([A-Za-z0-9_:-]+)(?:;[^\]]*)?\]")),
    (
        "latex_cite",
        re.compile(
            r"\\(?:cite|citep|citepalp|citepalt|parencite|textcite)\*?\{([^}]+)\}"
        ),
    ),
    ("md_footnote", re.compile(r"\[\^([A-Za-z0-9_-]+)\](?!:)")),
]

SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]+|[^.!?\n]+$", re.MULTILINE)

CLAIM_CUES = re.compile(
    r"\b("
    r"show(?:s|ed|ing)?|demonstrate(?:s|d|ing)?|find(?:s|ing)?|found|"
    r"prove(?:s|d|ing)?|confirm(?:s|ed|ing)?|establish(?:es|ed|ing)?|"
    r"outperform(?:s|ed|ing)?|surpass(?:es|ed|ing)?|exceed(?:s|ed|ing)?|"
    r"significant(?:ly)?|statistically|causal(?:ly)?|contributes?|"
    r"we (?:show|demonstrate|find|prove|confirm|establish)|"
    r"our (?:results?|experiments?|evaluation) "
    r"(?:show|indicate|suggest|demonstrate)|"
    r"is (?:superior|inferior) to|better than|worse than|"
    r"achieves?|attains?|yields?"
    r")\b",
    re.IGNORECASE,
)

ANTI_CLAIM = re.compile(
    r"\b(we (?:hope|plan|aim|intend)|future work|"
    r"to the best of our knowledge|"
    r"may|might|could|possibly|perhaps|allegedly)\b",
    re.IGNORECASE,
)

SECTION_SKIP = re.compile(
    r"^(#{1,6}\s*(related work|references|bibliography|"
    r"acknowledgements?|appendix)\b|"
    r"\\(section|chapter)\*?\{(related work|references|"
    r"bibliography|acknowledgements?|appendix))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Span:
    kind: str
    text: str
    start: int
    end: int
    keys: tuple[str, ...] = ()


@dataclass
class Link:
    claim: Span
    citations: list[Span]
    nearest_distance: int | None


@dataclass
class Report:
    path: str
    window: int
    claims: list[Span]
    citations: list[Span]
    links: list[Link]
    uncovered: list[Span]
    orphans: list[Span]
    coverage: float

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "window": self.window,
            "claim_count": len(self.claims),
            "citation_count": len(self.citations),
            "covered": len(self.claims) - len(self.uncovered),
            "uncovered": [
                {"text": c.text.strip(), "start": c.start, "end": c.end}
                for c in self.uncovered
            ],
            "orphans": [
                {
                    "text": c.text.strip(),
                    "keys": list(c.keys),
                    "start": c.start,
                    "end": c.end,
                }
                for c in self.orphans
            ],
            "coverage": round(self.coverage, 4),
            "links": [
                {
                    "claim": link.claim.text.strip(),
                    "nearest_distance": link.nearest_distance,
                    "citation_keys": [
                        k for c in link.citations for k in c.keys
                    ],
                }
                for link in self.links
            ],
        }


def _iter_citations(text: str) -> list[Span]:
    found: list[Span] = []
    for kind, pat in CITE_PATTERNS:
        for m in pat.finditer(text):
            raw = m.group(1)
            if kind == "latex_cite":
                keys = tuple(k.strip() for k in raw.split(",") if k.strip())
            else:
                keys = (raw,)
            found.append(
                Span(
                    kind=kind,
                    text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    keys=keys,
                )
            )
    found.sort(key=lambda s: s.start)
    return found


def _active_sections(text: str) -> list[tuple[int, int]]:
    lines = text.splitlines(keepends=True)
    ranges: list[tuple[int, int]] = []
    pos = 0
    skip = False
    block_start = 0
    for line in lines:
        if SECTION_SKIP.match(line.strip()):
            if not skip and pos > block_start:
                ranges.append((block_start, pos))
            skip = True
        elif skip and (
            line.startswith("# ")
            or line.startswith("\\section")
            or line.startswith("\\chapter")
        ):
            skip = False
            block_start = pos
        pos += len(line)
    if not skip and pos > block_start:
        ranges.append((block_start, pos))
    if not ranges and not skip:
        ranges.append((0, len(text)))
    return ranges


def _in_ranges(idx: int, ranges: Iterable[tuple[int, int]]) -> bool:
    return any(a <= idx < b for a, b in ranges)


def _iter_claims(text: str) -> list[Span]:
    ranges = _active_sections(text)
    claims: list[Span] = []
    for m in SENTENCE_RE.finditer(text):
        if not _in_ranges(m.start(), ranges):
            continue
        stripped = m.group(0).strip()
        if len(stripped) < 24:
            continue
        if stripped.startswith("#") or stripped.startswith("\\"):
            continue
        if not CLAIM_CUES.search(stripped):
            continue
        if ANTI_CLAIM.search(stripped) and not re.search(
            r"\b(we (?:show|demonstrate|find|prove)|significant(?:ly)?)\b",
            stripped,
            re.I,
        ):
            continue
        claims.append(
            Span(kind="claim", text=stripped, start=m.start(), end=m.end())
        )
    return claims


def analyze(text: str, *, path: str = "<stdin>", window: int = 240) -> Report:
    claims = _iter_claims(text)
    ranges = _active_sections(text)
    citations = [
        c for c in _iter_citations(text) if _in_ranges(c.start, ranges)
    ]
    links: list[Link] = []
    uncovered: list[Span] = []
    used: set[int] = set()

    for claim in claims:
        nearby: list[tuple[int, Span, int]] = []
        for i, cite in enumerate(citations):
            inside = claim.start <= cite.start < claim.end
            after_limit = claim.end + window
            gap = text.find("\n\n", claim.end, after_limit)
            if gap != -1:
                after_limit = gap
            for marker in ("\n#", "\n\\section", "\n\\chapter"):
                hit = text.find(marker, claim.end, after_limit)
                if hit != -1:
                    after_limit = hit
            after = claim.end <= cite.start <= after_limit
            if not (inside or after):
                continue
            dist = 0 if inside else cite.start - claim.end
            nearby.append((dist, cite, i))
        nearby.sort(key=lambda t: t[0])
        if nearby:
            uniq: list[Span] = []
            seen: set[tuple[int, int]] = set()
            for _, cite, idx in nearby:
                used.add(idx)
                key = (cite.start, cite.end)
                if key not in seen:
                    seen.add(key)
                    uniq.append(cite)
            links.append(
                Link(
                    claim=claim,
                    citations=uniq,
                    nearest_distance=nearby[0][0],
                )
            )
        else:
            uncovered.append(claim)
            links.append(
                Link(claim=claim, citations=[], nearest_distance=None)
            )

    orphans = [c for i, c in enumerate(citations) if i not in used]
    coverage = (
        (len(claims) - len(uncovered)) / len(claims) if claims else 1.0
    )
    return Report(
        path=path,
        window=window,
        claims=claims,
        citations=citations,
        links=links,
        uncovered=uncovered,
        orphans=orphans,
        coverage=coverage,
    )
