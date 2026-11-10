import { useEffect, useState } from 'react'
import './App.css'

type JobResponse = {
  job_id: string
  status: string
  result?: {
    text: string
    language: string
    duration_seconds: number
    segments: { start: number; end: number; text: string }[]
  } | null
  error?: string | null
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState('')
  const [status, setStatus] = useState('')
  const [message, setMessage] = useState('')
  const [transcript, setTranscript] = useState('')
  const [isWorking, setIsWorking] = useState(false)
  const [exporting, setExporting] = useState('')
  const [username, setUsername] = useState('')
  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [authChecking, setAuthChecking] = useState(true)

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(async (response) => {
        if (response.ok) {
          const data = await response.json()
          setUsername(data.username)
        }
      })
      .catch(() => {
        setLoginError('Unable to connect to the server.')
      })
      .finally(() => setAuthChecking(false))
  }, [])

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginError('')

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: loginUsername,
          password: loginPassword,
        }),
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(data?.detail || 'Login failed.')
      }

      setUsername(data.username)
      setLoginPassword('')
    } catch (error) {
      setLoginError(
        error instanceof Error ? error.message : 'Login failed.',
      )
    }
  }

  async function handleLogout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
    } finally {
      setUsername('')
      setFile(null)
      setJobId('')
      setTranscript('')
      setStatus('')
      setMessage('')
    }
  }

  function handleFile(selectedFile?: File) {
    if (!selectedFile) return

    if (!selectedFile.name.toLowerCase().endsWith('.wav')) {
      setMessage('Please select a WAV audio file.')
      setFile(null)
      return
    }

    setFile(selectedFile)
    setJobId('')
    setMessage('')
    setTranscript('')
    setStatus('')
  }

  async function startTranscription() {
    if (!file || isWorking) return

    setIsWorking(true)
    setMessage('')
    setTranscript('')
    setJobId('')
    setStatus('Uploading audio...')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const uploadResponse = await fetch('/api/transcribe', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => null)
        throw new Error(errorData?.detail || 'Audio upload failed.')
      }

      const uploadData: JobResponse = await uploadResponse.json()
      setJobId(uploadData.job_id)
      setStatus('Queued')

      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 3000))

        const jobResponse = await fetch(`/api/jobs/${uploadData.job_id}`, {
          credentials: 'include',
        })

        if (!jobResponse.ok) {
          throw new Error('Could not check transcription status.')
        }

        const job: JobResponse = await jobResponse.json()
        setStatus(job.status)

        if (job.status === 'completed') {
          setTranscript(job.result?.text || '')
          setStatus('Completed')
          break
        }

        if (job.status === 'failed') {
          throw new Error(job.error || 'Transcription failed.')
        }
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Something went wrong.',
      )
      setStatus('Failed')
    } finally {
      setIsWorking(false)
    }
  }

  async function downloadExport(format: 'txt' | 'docx' | 'pdf' | 'srt') {
    if (!jobId || exporting) return

    setExporting(format)
    setMessage('')

    try {
      const response = await fetch(`/api/jobs/${jobId}/export/${format}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(format === 'srt' ? {} : { text: transcript }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => null)
        throw new Error(data?.detail || `Could not export ${format.toUpperCase()}.`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      const baseName = file?.name.replace(/\.wav$/i, '') || 'transcript'

      link.href = url
      link.download = `${baseName}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Export failed.',
      )
    } finally {
      setExporting('')
    }
  }

  if (authChecking) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4 text-slate-900">
        <p className="text-slate-600">Checking your session...</p>
      </main>
    )
  }

  if (!username) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-8 text-slate-900">
        <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <h1 className="text-2xl font-bold tracking-tight">WAV Transcriber</h1>
          <p className="mt-2 text-sm text-slate-500">
            Sign in to access your transcription workspace.
          </p>

          <form onSubmit={handleLogin} className="mt-6 space-y-4">
            <div>
              <label htmlFor="login-username" className="mb-1 block text-sm font-medium">
                Username
              </label>
              <input
                id="login-username"
                type="text"
                autoComplete="username"
                required
                value={loginUsername}
                onChange={(event) => setLoginUsername(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-3 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="login-password" className="mb-1 block text-sm font-medium">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                required
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-3 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {loginError && (
              <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {loginError}
              </p>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Sign in
            </button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900">
      <div className="mx-auto max-w-4xl">
        <header className="mb-10 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">WAV Transcriber</h1>
            <p className="mt-1 text-sm text-slate-500">
              Audio to text transcription workspace
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{username}</span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-100"
            >
              Sign out
            </button>
          </div>
        </header>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-semibold">Upload your audio</h2>
          <p className="mt-2 text-sm text-slate-500">
            Select a WAV recording to start transcription.
          </p>

          <label
            htmlFor="audio-file"
            className="mt-6 flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center transition hover:border-blue-500 hover:bg-blue-50"
          >
            <span className="text-4xl">🎧</span>
            <span className="mt-4 font-semibold">Choose a WAV audio file</span>
            <span className="mt-2 text-sm text-slate-500">
              Click here to browse your files
            </span>
            <input
              id="audio-file"
              type="file"
              accept=".wav,audio/wav"
              className="hidden"
              disabled={isWorking}
              onChange={(event) => handleFile(event.target.files?.[0])}
            />
          </label>

          {file && (
            <div className="mt-5 rounded-lg border border-slate-200 p-4">
              <p className="font-medium">{file.name}</p>
              <p className="mt-1 text-sm text-slate-500">
                {(file.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          )}

          {message && (
            <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {message}
            </p>
          )}

          <button
            type="button"
            disabled={!file || isWorking}
            className="mt-6 w-full rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            onClick={startTranscription}
          >
            {isWorking ? 'Please wait...' : 'Start transcription'}
          </button>

          {status && (
            <div className="mt-5 rounded-lg bg-blue-50 p-4">
              <p className="font-medium text-blue-800">
                Transcription status: {status}
              </p>
              {isWorking && (
                <p className="mt-1 text-sm text-blue-700">
                  This page will check the job automatically.
                </p>
              )}
            </div>
          )}
        </section>

        {transcript && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">Edit your transcript</h2>
            <p className="mt-2 text-sm text-slate-500">
              Correct the transcript before downloading. TXT, DOCX and PDF use
              your edited text. SRT uses the original timestamps.
            </p>

            <textarea
              value={transcript}
              onChange={(event) => setTranscript(event.target.value)}
              rows={14}
              className="mt-4 w-full rounded-lg border border-slate-200 p-4 text-sm leading-7 text-slate-800 focus:border-blue-500 focus:outline-none"
            />

            <h3 className="mt-6 font-semibold">Download transcript</h3>
            <div className="mt-3 grid grid-cols-2 gap-3">
              {(['txt', 'docx', 'pdf', 'srt'] as const).map((format) => (
                <button
                  key={format}
                  type="button"
                  disabled={!!exporting}
                  onClick={() => downloadExport(format)}
                  className="rounded-lg bg-green-600 px-4 py-3 font-semibold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {exporting === format
                    ? 'Preparing...'
                    : `Download .${format.toUpperCase()}`}
                </button>
              ))}
            </div>
          </section>
        )}

        <p className="mt-6 text-center text-sm text-slate-500">
          English transcription · WAV files · Up to 3 hours
        </p>
      </div>
    </main>
  )
}

export default App
