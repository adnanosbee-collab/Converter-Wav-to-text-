import json
import subprocess
from pathlib import Path

from app.config import MAX_DURATION_SECONDS


def validate_wav(file_path):
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError("The supplied path is not a file.")

    if path.suffix.lower() != ".wav":
        raise ValueError("Only WAV files are supported.")

    if path.stat().st_size == 0:
        raise ValueError("The uploaded file is empty.")

    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=format_name,duration,size:stream=codec_type,codec_name,sample_rate,channels",
        "-of", "json",
        str(path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("FFprobe is not installed.")
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"Invalid or unreadable audio file: {exc.stderr}")

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError("Could not read audio metadata.")

    format_info = metadata.get("format", {})
    streams = metadata.get("streams", [])

    format_names = format_info.get("format_name", "").split(",")

    if "wav" not in format_names:
        raise ValueError("The file is not a valid WAV container.")

    audio_streams = [
        stream for stream in streams
        if stream.get("codec_type") == "audio"
    ]

    if not audio_streams:
        raise ValueError("No audio stream was found.")

    duration = float(format_info.get("duration", 0))

    if duration <= 0:
        raise ValueError("Audio duration must be greater than zero.")

    if duration > MAX_DURATION_SECONDS:
        raise ValueError("Audio duration exceeds the 3-hour limit.")

    audio = audio_streams[0]

    sample_rate = int(audio.get("sample_rate", 0))
    channels = int(audio.get("channels", 0))

    if not 8000 <= sample_rate <= 192000:
        raise ValueError("Unsupported audio sample rate.")

    if not 1 <= channels <= 8:
        raise ValueError("Unsupported number of audio channels.")

    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "duration_seconds": duration,
        "sample_rate": sample_rate,
        "channels": channels,
        "codec": audio.get("codec_name"),
    }
