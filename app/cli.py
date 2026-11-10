import argparse
import json
from pathlib import Path

from app.config import OUTPUT_DIR
from app.validator import validate_wav
from app.transcriber import transcribe_audio
from app.exporters import export_txt, export_srt


def main():
    parser = argparse.ArgumentParser(
        description="Local English WAV transcription tool"
    )

    parser.add_argument(
        "command",
        choices=["transcribe"],
        help="Operation to perform",
    )

    parser.add_argument(
        "audio_file",
        help="Path to the WAV recording",
    )

    args = parser.parse_args()

    audio_path = Path(args.audio_file)

    try:
        metadata = validate_wav(audio_path)

        print("\nAudio validation successful.")
        print(json.dumps(metadata, indent=2))

        print("\nStarting transcription...")
        result = transcribe_audio(str(audio_path))

        output_folder = Path(OUTPUT_DIR) / audio_path.stem
        output_folder.mkdir(parents=True, exist_ok=True)

        json_path = output_folder / "transcript.json"

        json_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        export_txt(result, output_folder / "transcript.txt")
        export_srt(result, output_folder / "transcript.srt")

        print("\nTranscription completed successfully.")
        print(f"Output folder: {output_folder.resolve()}")
        print(f"Transcript: {json_path.resolve()}")

    except (ValueError, RuntimeError) as exc:
        print(f"\nERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
