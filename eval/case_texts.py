"""Customer texts of D01-D08 (development) and H01-H06 (test) from the local AFS materials.

materials/ is never committed (copyright, .gitignore). This module only reads it at run time.

    load_case_texts() -> {"D01": "...", ..., "H06": "..."}
"""
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "materials"
DOCX = "AFS_Examples_and_Reference.docx"
H_TXT = "customer_scenarios_for_final_evaluation.txt"


def _docx_paragraphs(path: Path) -> list[str]:
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p))
        t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&quot;", '"').replace("&apos;", "'"))
        if t.strip():
            out.append(t.strip())
    return out


def load_d_texts(materials: Path = MATERIALS) -> dict:
    """D01-D08: the enquiry is the paragraph right after the 'Dxx · title' heading in section 1."""
    paras = _docx_paragraphs(materials / DOCX)
    texts = {}
    for i, p in enumerate(paras):
        m = re.match(r"^(D0[1-8])\s+·\s+", p)
        if m and m.group(1) not in texts and i + 1 < len(paras):
            nxt = paras[i + 1]
            if not nxt.startswith(("Facts stated", "Decision status")):
                texts[m.group(1)] = nxt
    return texts


def load_h_texts(materials: Path = MATERIALS) -> dict:
    raw = (materials / H_TXT).read_text(encoding="utf-8")
    texts = {}
    for m in re.finditer(r"^(H0[1-6]) \| [^\n]*\n=+\n(.*?)(?=\n=+\n|\Z)", raw, flags=re.S | re.M):
        texts[m.group(1)] = " ".join(m.group(2).split())
    return texts


def load_case_texts(materials: Path = MATERIALS) -> dict:
    return {**load_d_texts(materials), **load_h_texts(materials)}


if __name__ == "__main__":
    t = load_case_texts()
    for k in sorted(t):
        print(f"{k}: {len(t[k]):4} chars  {t[k][:70]}…")
    assert sorted(t) == [f"D0{i}" for i in range(1, 9)] + [f"H0{i}" for i in range(1, 7)], sorted(t)
