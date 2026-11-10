import os
import tempfile
import uuid
from pathlib import Path

import redis
from rq import Queue

from fastapi import FastAPI, File, Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.exporters import make_docx, make_pdf, make_srt
from sqlalchemy import select, text

from app.auth import get_current_user
from app.auth_routes import router as auth_router
from app.config import MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.database import Base, SessionLocal, engine
from app.models import TranscriptionJob, User
from app.validator import validate_wav


app = FastAPI(
    title="WAV Transcription API",
    version="3.0.0",
)

app.include_router(auth_router)

redis_connection = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

transcription_queue = Queue(
    "transcriptions",
    connection=redis_connection,
)


async def save_upload(file: UploadFile, temp_file):
    total_bytes = 0

    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break

        total_bytes += len(chunk)
        if total_bytes > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Upload exceeds the maximum allowed file size.",
            )

        temp_file.write(chunk)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    try:
        redis_connection.ping()
        redis_status = "ok"
    except redis.RedisError:
        redis_status = "unavailable"

    return {
        "status": "ok" if redis_status == "ok" else "degraded",
        "service": "wav-transcription-api",
        "redis": redis_status,
    }


@app.post("/validate-audio")
async def validate_audio(file: UploadFile = File(...)):
    if not file.filename or Path(file.filename).suffix.lower() != ".wav":
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are supported.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

            await save_upload(file, temp_file)

        metadata = validate_wav(temp_path)
        metadata["filename"] = Path(file.filename).name

        return {
            "valid": True,
            "audio": metadata,
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        await file.close()


@app.post("/transcribe", status_code=202)
async def create_transcription(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or Path(file.filename).suffix.lower() != ".wav":
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are supported.",
        )

    temp_path = None
    job_id = str(uuid.uuid4())

    try:
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            prefix="audio-",
            dir=UPLOAD_DIR,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

            await save_upload(file, temp_file)

        metadata = validate_wav(temp_path)
        metadata["filename"] = Path(file.filename).name

        with SessionLocal() as db:
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:user_id))"),
                {"user_id": current_user.id},
            )

            active_jobs = db.scalars(
                select(TranscriptionJob).where(
                    TranscriptionJob.user_id == current_user.id,
                    TranscriptionJob.status.in_(["queued", "processing"]),
                )
            ).all()

            active_long_jobs = [
                active for active in active_jobs
                if float((active.audio_metadata or {}).get("duration_seconds", 0)) >= 3600
            ]

            incoming_duration = float(metadata["duration_seconds"])

            if active_long_jobs:
                raise HTTPException(
                    status_code=429,
                    detail="You already have an active audio file of 1 hour or longer.",
                )

            if incoming_duration >= 3600 and active_jobs:
                raise HTTPException(
                    status_code=429,
                    detail="Finish your other active jobs before uploading a file of 1 hour or longer.",
                )

            if incoming_duration < 3600 and len(active_jobs) >= 3:
                raise HTTPException(
                    status_code=429,
                    detail="You can have up to 3 active files under 1 hour.",
                )

            job = TranscriptionJob(
                id=job_id,
                filename=Path(file.filename).name,
                user_id=current_user.id,
                status="queued",
                audio_metadata=metadata,
            )
            db.add(job)
            db.commit()

        try:
            transcription_queue.enqueue(
                "app.worker.process_transcription",
                job_id,
                str(temp_path),
                job_timeout=4 * 60 * 60,
            )
        except Exception:
            with SessionLocal() as db:
                job = db.get(TranscriptionJob, job_id)
                if job is not None:
                    job.status = "failed"
                    job.error = "Unable to add the job to the processing queue."
                    db.commit()
            raise

        temp_path = None

        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "queued",
                "message": "Transcription job accepted.",
            },
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to accept the transcription job. Please try again.",
        ) from exc

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        await file.close()

class ExportRequest(BaseModel):
    text: str | None = None

@app.get("/jobs/{job_id}")
def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        job = db.scalar(
            select(TranscriptionJob).where(
                TranscriptionJob.id == job_id,
                TranscriptionJob.user_id == current_user.id,
            )
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Transcription job not found.",
            )

        return {
            "job_id": job.id,
            "status": job.status,
            "filename": job.filename,
            "audio": job.audio_metadata,
            "result": (
                {
                    "text": job.transcript_text,
                    "language": job.language,
                    "duration_seconds": job.duration_seconds,
                    "segments": [
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text,
                        }
                        for segment in job.segments
                    ],
                }
                if job.status == "completed"
                else None
            ),
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }


@app.post("/jobs/{job_id}/export/{file_format}")
def export_job(
    job_id: str,
    file_format: str,
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
):
    if file_format not in {"txt", "docx", "pdf", "srt"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported export format.",
        )

    with SessionLocal() as db:
        job = db.scalar(
            select(TranscriptionJob).where(
                TranscriptionJob.id == job_id,
                TranscriptionJob.user_id == current_user.id,
            )
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Transcription job not found.",
            )

        if job.status != "completed":
            raise HTTPException(
                status_code=409,
                detail="Transcription is not completed.",
            )

        filename = Path(job.filename).stem or "transcript"

        if file_format == "srt":
            content = make_srt([
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
                for segment in job.segments
            ])
            media_type = "application/x-subrip"
        else:
            text = (
                request.text
                if request.text is not None
                else (job.transcript_text or "")
            )

            if file_format == "txt":
                content = (text + "\n").encode("utf-8")
                media_type = "text/plain; charset=utf-8"
            elif file_format == "docx":
                content = make_docx(text)
                media_type = (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
            else:
                content = make_pdf(text)
                media_type = "application/pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}.{file_format}"'
            )
        },
    )
