from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_license_file_and_no_mit_wording_in_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "MIT" not in readme
    assert not any(ROOT.glob("LICENSE*"))


def test_product_is_explicitly_non_chat() -> None:
    html = (ROOT / "planprobe/static/index.html").read_text(encoding="utf-8")
    assert "챗봇" in html
    assert "채팅" in html
