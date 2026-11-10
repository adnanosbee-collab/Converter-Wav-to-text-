from io import BytesIO
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from xml.sax.saxutils import escape


def export_txt(result, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result["text"] + "\n", encoding="utf-8")
    return path


def format_srt_time(seconds):
    milliseconds = round(seconds * 1000)
    hours = milliseconds // 3600000
    milliseconds %= 3600000
    minutes = milliseconds // 60000
    milliseconds %= 60000
    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02}:{minutes:02}:{secs:02},"
        f"{milliseconds:03}"
    )


def export_srt(result, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []

    for index, segment in enumerate(result["segments"], start=1):
        start = format_srt_time(segment["start"])
        end = format_srt_time(segment["end"])
        blocks.append(
            f"{index}\n{start} --> {end}\n{segment['text']}"
        )

    path.write_text(
        "\n\n".join(blocks) + ("\n" if blocks else ""),
        encoding="utf-8",
    )
    return path


def make_docx(text):
    document = Document()
    document.add_heading("Transcription", 0)

    for paragraph in text.splitlines():
        document.add_paragraph(paragraph)

    output = BytesIO()
    document.save(output)
    return output.getvalue()


def make_pdf(text):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for paragraph in text.splitlines():
        if paragraph.strip():
            story.append(Paragraph(escape(paragraph), styles["BodyText"]))
            story.append(Spacer(1, 8))

    document.build(story)
    return output.getvalue()


def make_srt(segments):
    blocks = []

    for index, segment in enumerate(segments, start=1):
        start = format_srt_time(segment["start"])
        end = format_srt_time(segment["end"])
        blocks.append(
            f"{index}\n{start} --> {end}\n{segment['text']}"
        )

    return ("\n\n".join(blocks) + ("\n" if blocks else "")).encode("utf-8")
