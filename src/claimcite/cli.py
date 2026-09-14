"""CLI entry for claimcite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claimcite import __version__
from claimcite.core import analyze, format_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claimcite",
        description=(
            "Offline claim\u2194citation coverage for Markdown/LaTeX research drafts. "
            "Maps assertive claim sentences to nearby citation markers."
        ),
    )
    p.add_argument(
        "paths",
        nargs="*",
        help="Draft files (.md, .tex, .txt). Reads stdin if omitted and stdin is piped.",
    )
    p.add_argument(
        "--window",
        type=int,
        default=240,
        help="Max character distance from claim mid to citation mid (default: 240).",
    )
    p.add_argument(
        "--max-uncovered",
        type=int,
        default=None,
        help="Exit 1 if uncovered claim count exceeds this threshold (CI gate).",
    )
    p.add_argument(
        "--min-coverage",
        type=float,
        default=None,
        help="Exit 1 if coverage fraction is below this value (0\u20131).",
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    p.add_argument("--version", action="version", version=f"claimcite {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    texts: list[tuple[str, str]] = []

    if args.paths:
        for raw in args.paths:
            path = Path(raw)
            if not path.is_file():
                print(f"claimcite: not a file: {path}", file=sys.stderr)
                return 2
            texts.append((str(path), path.read_text(encoding="utf-8", errors="replace")))
    elif not sys.stdin.isatty():
        texts.append(("<stdin>", sys.stdin.read()))
    else:
        build_parser().print_help()
        return 2

    reports = [analyze(body, path=name, window=args.window) for name, body in texts]
    worst_uncovered = max((len(r.uncovered) for r in reports), default=0)
    worst_coverage = min((r.coverage for r in reports), default=1.0)

    if args.json:
        payload = reports[0].to_dict() if len(reports) == 1 else [r.to_dict() for r in reports]
        print(json.dumps(payload, indent=2))
    else:
        for r in reports:
            sys.stdout.write(format_report(r))
            if len(reports) > 1:
                sys.stdout.write("\n")

    if args.max_uncovered is not None and worst_uncovered > args.max_uncovered:
        return 1
    if args.min_coverage is not None and worst_coverage < args.min_coverage:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
