OCR Service — Full Learning Map

  Folder Structure

  ocr-service/
  ├── main.py          # FastAPI app entrypoint
  ├── worker.py        # Separate background worker process
  ├── core/            # Config & security utilities
  ├── api/             # HTTP routes + auth dependency
  │   └── routes/      # auth, upload, requests
  ├── db/              # MongoDB client, models, queries
  ├── ocr/             # Tesseract + PDF processing
  ├── storage/         # File upload handling
  ├── watcher/         # Change Stream + polling (2 watchers!)
  ├── websockets/      # Real-time push to browser
  └── tests/           # Full test suite

  ---
  Area 1 — Authentication & Authorization (core/security.py, api/deps.py, api/routes/auth.py)

  What you learn:
  - bcrypt — passwords are never stored as plain text; hash_password() turns "mypassword" into a 60-char hash
  - JWT tokens — after login, server signs a token with a secret key. Every future request carries that token; server verifies the signature
  without hitting the DB
  - FastAPI Dependency Injection — get_current_user is a function that FastAPI automatically runs before any protected route. If the token is
   invalid, it raises 401 and the route never runs

  Register → hash password → store in MongoDB
  Login    → verify hash  → issue JWT token
  Request  → decode JWT   → inject user_id into route

  ---
  Area 2 — MongoDB Schemas & Models (db/models.py)

  What you learn:
  - Pydantic models — define the shape of your data with types. If wrong data comes in, Pydantic raises an error automatically
  - PyObjectId — a custom bridge class. MongoDB uses 12-byte ObjectId internally, but Python/JSON needs strings. This class converts between
  them
  - Enums for status — RequestStatus.PENDING / PROCESSING / COMPLETED / FAILED — using an enum prevents typos like "compelted" from silently
  breaking logic
  - Field(alias="_id") — MongoDB calls it _id, Python calls it id. The alias bridges them

  ---
  Area 3 — MongoDB Queries (Repository Pattern) (db/repository.py)

  What you learn:
  - Repository pattern — all DB queries live in one class (RequestRepository), not scattered across routes. Easier to test and swap
  - find_one_and_update — the atomic lock — this is the most important query in the project. When 10 workers run simultaneously, MongoDB
  guarantees only ONE of them "wins" and gets the job marked as PROCESSING. No two workers process the same file
  - Retry logic with $inc — failed jobs get retry_count incremented and status reset to PENDING. The Change Stream picks them up again
  automatically
  - reset_stuck_jobs — finds documents stuck in PROCESSING for too long (worker crashed) and resets them

  ★ Insight ─────────────────────────────────────
  find_one_and_update is a single atomic MongoDB operation —
  "find this, update it, return the result" with no gap in between.
  This is how you solve the distributed "who does this job?" race
  condition without any external locking system.
  ─────────────────────────────────────────────────

  ---
  Area 4 — Concurrency with asyncio (ocr/engine.py, ocr/pdf_processor.py, worker.py)

  Three distinct patterns were used:

  ┌─────────────────────┬──────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────┐
  │       Pattern       │      Where       │                                             Why                                              │
  ├─────────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ asyncio.to_thread() │ engine.py        │ Tesseract is a blocking C program. Moving it to a thread lets the event loop keep running    │
  │                     │                  │ other coroutines                                                                             │
  ├─────────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ asyncio.gather()    │ pdf_processor.py │ Process all PDF pages in parallel, not one-by-one. 10 pages = ~10x faster                    │
  ├─────────────────────┼──────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
  │ asyncio.Semaphore   │ worker.py        │ Limits concurrent OCR jobs. WORKER_CONCURRENCY=3 means max 3 Tesseract threads at once       │
  └─────────────────────┴──────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────┘

  ★ Insight ─────────────────────────────────────
  async/await does NOT mean parallel — it means "while waiting
  for I/O, do other things." CPU-heavy work (Tesseract) still
  blocks. asyncio.to_thread() is how you escape the event loop
  for CPU-bound or blocking-library calls.
  ─────────────────────────────────────────────────

  ---
  Area 5 — Change Streams (Two of them!) (watcher/change_stream.py, watcher/api_stream.py)

  This is the most architecturally interesting part — two separate MongoDB Change Streams for two different purposes:

  Worker-side (change_stream.py) — runs in worker.py process:
  New job inserted in MongoDB
      → Change Stream fires
      → Worker atomically claims it (find_one_and_update)
      → Runs Tesseract
      → Marks completed/failed

  API-side (api_stream.py) — runs inside the FastAPI process:
  Job status changes to completed/failed
      → Change Stream fires
      → Push result to browser via WebSocket

  ★ Insight ─────────────────────────────────────
  Change Streams are MongoDB's built-in "subscribe to changes"
  feature (like a database event listener). The worker uses one
  to know when new jobs arrive; the API uses another to know
  when to notify the browser. Two processes, two streams, zero polling.
  ─────────────────────────────────────────────────

  ---
  Area 6 — Fallback Polling (watcher/polling.py)

  Change Streams are reliable but not perfect. If a worker crashes mid-job, the job stays PROCESSING forever — and never re-triggers the
  stream. The polling loop runs every N minutes, finds those "orphaned" jobs, and resets them to PENDING.

  This is a resilience pattern — the system heals itself.

  ---
  Area 7 — WebSockets for Real-time Push (websockets/manager.py, main.py)

  - Browser opens ws://server/ws/{request_id} when submitting a job
  - ConnectionManager stores the live WebSocket connection in a dict keyed by request_id
  - When the API-side Change Stream fires, it calls manager.push(request_id, result) — the result goes directly to the right browser tab
  - Singleton pattern — manager = ConnectionManager() at module level means all routes share the same manager instance

  ---
  Area 8 — File Upload & Validation (storage/local.py, api/routes/upload.py)

  - Extension whitelist (only .pdf .jpg .png .jpeg)
  - Max file size enforcement in bytes
  - UUID filenames — prevents overwriting files and directory traversal attacks
  - aiofiles — async file write so the event loop doesn't freeze during disk I/O

  ---
  Area 9 — Two-Process Architecture (main.py vs worker.py)

  Process 1: FastAPI (main.py)
    ├── Serves HTTP requests (upload, auth, status)
    ├── Watches for completions → pushes to WebSocket
    └── Never runs Tesseract itself

  Process 2: Worker (worker.py)
    ├── Watches for new pending jobs → runs Tesseract
    ├── Fallback polling for stuck jobs
    └── Never serves HTTP

  Why split? Tesseract is CPU-heavy. Running it in the API process would slow down HTTP responses for all other users.

  ---
  Skills Map — What to Study Next

  ┌──────────────────────────┬────────────────────────────────────────┐
  │          Skill           │               Learn via                │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ async/await, event loops │ Python asyncio docs                    │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ JWT auth                 │ python-jose, OAuth2                    │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ MongoDB queries          │ Motor (async driver) + PyMongo docs    │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ Change Streams           │ MongoDB manual → "Change Streams"      │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ Pydantic models          │ Pydantic v2 docs                       │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ WebSockets               │ FastAPI WebSockets guide               │
  ├──────────────────────────┼────────────────────────────────────────┤
  │ Concurrency patterns     │ "Python Concurrency with asyncio" book │
  └──────────────────────────┴────────────────────────────────────────┘
