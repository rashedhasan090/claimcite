from pathlib import Path

from claimcite.core import analyze
from claimcite.cli import main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample.md"
TEX = ROOT / "examples" / "sample.tex"


def test_sample_finds_uncovered_and_covered():
    report = analyze(SAMPLE.read_text(), path=str(SAMPLE), window=240)
    assert report.claims, "expected at least one claim"
    assert any("no nearby citation" in c.text.lower() or "clear improvement" in c.text.lower() for c in report.uncovered) or report.uncovered
    assert report.coverage < 1.0
    # First results claim should be covered by [@smith2024]
    covered_texts = " ".join(lnk.claim.text for lnk in report.links if lnk.citations)
    assert "mesh router" in covered_texts or "reduces median" in covered_texts


def test_latex_citep():
    report = analyze(TEX.read_text(), path=str(TEX), window=200)
    assert report.citations
    assert any(c.kind == "latex_cite" for c in report.citations)
    assert any(lnk.citations for lnk in report.links)


def test_cli_json_and_gate(tmp_path, capsys):
    code = main(["--json", "--max-uncovered", "0", str(SAMPLE)])
    out = capsys.readouterr().out
    assert '"coverage"' in out
    assert code == 1  # sample has uncovered claims


def test_cli_ok_when_threshold_high(capsys):
    code = main(["--max-uncovered", "99", str(SAMPLE)])
    assert code == 0
    assert "claimcite" in capsys.readouterr().out
