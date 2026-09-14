"""Data models for claimcite."""

from __future__ import annotations

from dataclasses import dataclass


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
