"""Human-readable report formatting."""

from __future__ import annotations

from claimcite.core import Report


def format_report(report: Report) -> str:
    lines = [
        f"claimcite — {report.path}",
        f"window={report.window}  claims={len(report.claims)}  "
        f"citations={len(report.citations)}  "
        f"coverage={report.coverage:.0%}",
        "",
    ]
    if report.uncovered:
        lines.append(f"Uncovered claims ({len(report.uncovered)}):")
        for c in report.uncovered:
            preview = c.text.replace("\n", " ")
            if len(preview) > 120:
                preview = preview[:117] + "..."
            lines.append(f"  [{c.start}] {preview}")
        lines.append("")
    else:
        lines.append("Uncovered claims: none")
        lines.append("")

    if report.orphans:
        lines.append(f"Orphan citations ({len(report.orphans)}):")
        for c in report.orphans:
            keys = ",".join(c.keys) if c.keys else "?"
            lines.append(f"  [{c.start}] {c.kind} {{{keys}}}")
        lines.append("")
    else:
        lines.append("Orphan citations: none")
        lines.append("")

    covered = [lnk for lnk in report.links if lnk.citations]
    if covered:
        lines.append("Covered (sample):")
        for lnk in covered[:5]:
            keys = sorted({k for c in lnk.citations for k in c.keys})
            preview = lnk.claim.text.replace("\n", " ")
            if len(preview) > 90:
                preview = preview[:87] + "..."
            lines.append(
                f"  d={lnk.nearest_distance} keys={keys or ['—']} :: {preview}"
            )
    return "\n".join(lines).rstrip() + "\n"
