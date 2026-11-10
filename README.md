# WAV Transcription

A self-hosted audio-to-text transcription application built with **React, FastAPI, and OpenAI Whisper (faster-whisper)**.

Upload WAV audio files, generate English transcripts, edit the recognized text, and export your results in multiple formats.

## Features

- **WAV audio transcription** – Convert prerecorded English WAV recordings into text.
- **Long recordings** – Configured to support audio up to 3 hours.
- **Background processing** – Redis and RQ handle transcription jobs without blocking the API.
- **Transcript editing** – Review and edit generated transcripts.
- **Multiple export formats** – Download transcripts as:
  - TXT
  - DOCX
  - PDF
  - SRT subtitles
- **User authentication** – Login-protected application with secure password hashing and session cookies.
- **Private user data** – Users can access only their own transcription jobs.
- **Upload validation** – Checks audio format, file size, duration, sample rate, and channels.
- **Self-hosted architecture** – Designed to run using Docker Compose.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python, FastAPI |
| Speech recognition | faster-whisper |
| AI model | Whisper base.en |
| Task queue | Redis, RQ |
| Database | PostgreSQL 17 |
| ORM | SQLAlchemy |
| Audio processing | FFmpeg |
| Authentication | JWT, Argon2 password hashing |
| Deployment | Docker, Docker Compose |

## Architecture

The application uses separate services for the frontend, API, transcription worker, database, and task queue.

```text
                 User
                   |
                   v
             React Frontend
                   |
                   v
              FastAPI
                   |
             Upload WAV
                   |
                   v
              Redis Queue
                   |
                   v
           Background Worker
                   |
             faster-whisper
                   |
                   v
             PostgreSQL
                   |
                   v
          Transcript and Segments
                   |
                   v
           Edit and Export
```

The original audio file is deleted after the transcript has been successfully saved to the database. If transcription fails, the audio file is retained for troubleshooting or retry handling.

## Requirements

Before running the application, install:

- Ubuntu or another Linux distribution
- Docker
- Docker Compose
- Node.js and npm
- Git
- FFmpeg (included in the backend Docker image)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/adnanosbee-collab/Converter-Wav-to-text-.git

cd Converter-Wav-to-text-
```

### 2. Configure environment variables

Create a `.env` file in the project root.

At minimum, configure the database password and authentication secret:

```env
POSTGRES_PASSWORD=YOUR_STRONG_DATABASE_PASSWORD
AUTH_SECRET=YOUR_LONG_RANDOM_SECRET
AUTH_TOKEN_EXPIRE_HOURS=24
AUTH_COOKIE_SECURE=false
MAX_DURATION_SECONDS=10800
MAX_UPLOAD_BYTES=1073741824
```

Use strong, unique secrets. For production, enable secure cookies by setting `AUTH_COOKIE_SECURE=true` when HTTPS is configured.

**Important:** Never upload `.env` files, passwords, authentication secrets, or database credentials to GitHub.

### 3. Start the backend services

```bash
docker compose up -d --build
```

This starts the API, transcription worker, PostgreSQL database, and Redis.

Check service status:

```bash
docker compose ps
```

Check API health:

```bash
curl http://localhost:8000/health
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

### 5. Start the frontend

```bash
npm run dev -- --host 0.0.0.0
```

Open the frontend in your browser:

```text
http://localhost:5173
```

## Create a User Account

Public registration is not enabled. An administrator creates user accounts through the backend.

Run:

```bash
docker compose exec -it api python -m app.create_user
```

Follow the prompts to create a username and password.

Users can then log in through the application.

## Supported Audio

The application is configured for:

- WAV audio files
- English prerecorded speech
- Recordings up to 3 hours
- Maximum upload size of 1 GB by default
- Sample rates from 8 kHz to 192 kHz
- Up to 8 audio channels

Actual transcription speed depends on the CPU, audio duration, and Whisper model.

## Export Formats

| Format | Purpose |
|---|---|
| TXT | Plain text transcript |
| DOCX | Editable Microsoft Word document |
| PDF | Portable document |
| SRT | Timestamped subtitles |

## Useful Docker Commands

Start services:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```

View service status:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f api
```

View transcription worker logs:

```bash
docker compose logs -f worker
```

Restart services:

```bash
docker compose restart
```

Rebuild the application:

```bash
docker compose up -d --build
```

## Security

The application includes several security measures:

- Passwords are hashed using Argon2.
- Authentication uses HTTP-only session cookies.
- Transcription endpoints require authentication.
- Job ownership is checked before retrieving or exporting transcripts.
- Upload size and audio duration are restricted.
- Database and API ports are bound to localhost in the supplied Docker Compose configuration.
- Environment secrets are excluded from Git.

For public deployment, use HTTPS, secure cookies, strong secrets, regular database backups, and appropriate server firewall rules.

## Current Project Status

The core application functionality is implemented:

- User login and authentication
- WAV upload and validation
- Background transcription
- Transcript editing
- TXT, DOCX, PDF, and SRT exports
- PostgreSQL transcript storage
- Docker-based backend services

Long-recording testing has been performed successfully with a recording of approximately 65 minutes. Full 3-hour and concurrent multi-user capacity testing remain to be completed.

## Future Improvements

- Production VPS deployment
- HTTPS and domain configuration
- Capacity and concurrency testing
- Additional performance optimizations

## License

No license has been specified yet. All rights are reserved by the repository owner unless a license is added.

---

**Built with React, FastAPI, faster-whisper, PostgreSQL, and Redis.**

