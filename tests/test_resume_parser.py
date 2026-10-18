import pymupdf
import docx
import pytest

import config
from modules.resume_analyzer import analyze_resume
from modules.resume_parser import ResumeParseError, clean_pasted_text, extract_text

SAMPLE = (config.__file__ and open(__import__("pathlib").Path(config.__file__).parent / "data" / "sample_resume.txt", encoding="utf-8").read())


def make_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 560, 800), text, fontsize=9)
    data = doc.tobytes()
    doc.close()
    return data


def make_docx(text: str, tmp_path) -> bytes:
    d = docx.Document()
    for line in text.splitlines():
        d.add_paragraph(line)
    path = tmp_path / "r.docx"
    d.save(path)
    return path.read_bytes()


def test_pdf_is_parsed_and_analyzed():
    text = extract_text("resume.pdf", make_pdf(SAMPLE))
    assert "Python" in text and "EDUCATION" in text
    profile = analyze_resume(text)
    assert "Python" in profile.skills and profile.email == "demo.candidate@example.com"
    assert len(profile.projects) >= 2


def test_docx_is_parsed(tmp_path):
    text = extract_text("resume.docx", make_docx(SAMPLE, tmp_path))
    profile = analyze_resume(text)
    assert profile.has_internship and profile.education_level == "bachelor"


@pytest.mark.parametrize("name,data,msg", [
    ("resume.txt", b"hello", "Unsupported"),
    ("resume.pdf", b"", "empty"),
    ("resume.pdf", b"not a pdf at all" * 10, "valid PDF"),
    ("resume.docx", b"not a zip" * 10, "valid DOCX"),
    ("resume.pdf", b"%PDF-1.4 garbage" + b"x" * 200, "Could not read"),
])
def test_bad_files_raise_friendly_errors(name, data, msg):
    with pytest.raises(ResumeParseError, match=msg):
        extract_text(name, data)


def test_oversized_file_rejected():
    big = b"%PDF" + b"0" * (config.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    with pytest.raises(ResumeParseError, match="larger"):
        extract_text("r.pdf", big)


def test_empty_pdf_text_rejected():
    with pytest.raises(ResumeParseError, match="Very little text"):
        extract_text("r.pdf", make_pdf("Hi"))


def test_pasted_text_validation():
    with pytest.raises(ResumeParseError):
        clean_pasted_text("too short")
    assert clean_pasted_text(SAMPLE).startswith("Aarav")


def test_missing_fields_stay_empty():
    p = analyze_resume("Just some words about cooking and gardening that are long enough to pass. " * 3)
    assert p.email is None and p.name is None and p.projects == [] and p.skills == []
    assert p.experience_level.startswith("Student")
