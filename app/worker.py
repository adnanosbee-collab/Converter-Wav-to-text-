from pathlib import Path

from app.database import SessionLocal
from app.models import TranscriptionJob, TranscriptSegment
from app.transcriber import transcribe_audio


def delete_audio_safely(audio_path: Path):
    try:
        audio_path.unlink(missing_ok=True)
    except OSError as exc:
        print(f"WARNING: Could not delete audio file {audio_path}: {exc}")


def process_transcription(job_id: str, file_path: str):
    audio_path = Path(file_path)

    try:
        with SessionLocal() as db:
            job = db.get(TranscriptionJob, job_id)

            if job is None:
                raise RuntimeError("Transcription job not found.")

            if job.status == "completed":
                delete_audio_safely(audio_path)
                return

            job.status = "processing"
            job.error = None
            db.commit()

        result = transcribe_audio(str(audio_path))

        # Save transcript and segments in one database transaction.
        with SessionLocal() as db:
            job = db.get(TranscriptionJob, job_id)

            if job is None:
                raise RuntimeError("Transcription job no longer exists.")

            job.transcript_text = result["text"]
            job.language = result["language"]
            job.duration_seconds = result["duration_seconds"]
            job.status = "completed"
            job.error = None

            job.segments = [
                TranscriptSegment(
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"],
                )
                for segment in result["segments"]
            ]

            db.commit()

        # Delete audio only after successful transcript persistence.
        delete_audio_safely(audio_path)

    except Exception as exc:
        try:
            with SessionLocal() as db:
                job = db.get(TranscriptionJob, job_id)

                if job is not None:
                    job.status = "failed"
                    job.error = str(exc)
                    db.commit()
        except Exception as db_exc:
            print(f"WARNING: Could not update failed job: {db_exc}")

        # Keep the original WAV so it can be recovered or retried.
        raise
