from faster_whisper import WhisperModel

from app.config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_LANGUAGE,
)

_model = None

def get_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}")

        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
            cpu_threads=4,
            num_workers=1,
        )

    return _model

def transcribe_audio(file_path):
    model = get_model()

    segments_generator, info = model.transcribe(
    file_path,
    language=WHISPER_LANGUAGE,
    beam_size=1,
    vad_filter=True,
    )

    segments = []
    full_text_parts = []

    for segment in segments_generator:
        text = segment.text.strip()

        if text:
            segments.append({
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": text,
            })

            full_text_parts.append(text)

    return {
        "text": " ".join(full_text_parts),
        "language": info.language,
        "duration_seconds": info.duration,
        "segments": segments,
    }
