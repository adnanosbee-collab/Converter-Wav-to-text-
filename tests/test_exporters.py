from app.exporters import export_txt, export_srt


def sample_result():
    return {
        "text": "Hello, this is a test.",
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello, this is a test.",
            }
        ],
    }


def test_export_txt(tmp_path):
    output = tmp_path / "transcript.txt"

    export_txt(sample_result(), output)

    assert output.exists()
    assert "Hello" in output.read_text(encoding="utf-8")


def test_export_srt(tmp_path):
    output = tmp_path / "transcript.srt"

    export_srt(sample_result(), output)

    content = output.read_text(encoding="utf-8")

    assert "00:00:00,000 --> 00:00:02,500" in content
    assert "Hello, this is a test." in content
