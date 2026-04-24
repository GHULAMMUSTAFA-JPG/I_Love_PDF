 Let me use your actual project as the teaching example — every decision here has a reason.

  ---
  The Core Principle: Separate by Responsibility

  Every folder answers one question: "What is this code responsible for?"

  If you can't answer that in 3 words, the folder is wrong.

  ---
  Your Project, Folder by Folder

  ocr-service/
  ├── core/
  ├── db/
  ├── api/
  │   └── routes/
  ├── ocr/
  ├── storage/
  ├── watcher/
  ├── websockets/
  ├── tests/
  ├── main.py
  └── worker.py

  ---
  core/ — App-wide building blocks

  core/
  ├── config.py      ← all env vars in one place
  └── security.py    ← password hashing, JWT

  Why here? These are used by everyone — routes, worker, db, tests. Putting them in core/ means no circular imports. Nothing in core/ imports
   from your other folders.

  Rule: core/ has zero dependencies on the rest of your app.

  ---
  db/ — Everything touching the database

  db/
  ├── client.py      ← connect/disconnect/get_db
  ├── models.py      ← Pydantic schemas (shape of your data)
  └── repository.py  ← all MongoDB queries

  Why split into 3 files?

  - client.py — manages the connection lifecycle. Only one place to change if you swap MongoDB for PostgreSQL
  - models.py — data shapes. No logic, no queries — just structure
  - repository.py — all queries in one class. Your routes never write raw db.find_one(...) — they call repo.get_by_id()

  ★ Insight ─────────────────────────────────────
  This is the Repository Pattern. Routes ask the repository
  for data; the repository asks MongoDB. Routes never touch
  MongoDB directly. If MongoDB changes, you fix one file.
  ─────────────────────────────────────────────────

  ---
  api/ — HTTP layer only

  api/
  ├── deps.py          ← shared dependencies (auth, db injection)
  └── routes/
      ├── auth.py      ← /auth/register, /auth/login
      ├── upload.py    ← POST /upload
      └── requests.py  ← GET /requests/{id}

  Why a routes/ subfolder? As the app grows, you add more routes. Keeping them flat in api/ gets messy fast. One file per domain area.

  Why deps.py? FastAPI's Depends() system needs reusable functions. get_current_user and get_db are used by every protected route — they live
   in one place, not copied into each route file.

  Rule: Route files do input validation and call other layers. They do NOT contain business logic or database queries directly.

  ---
  ocr/ — The actual work

  ocr/
  ├── engine.py        ← image → text (Tesseract)
  └── pdf_processor.py ← PDF → images → text

  Why isolated? OCR is the core capability of this service. Isolating it means you can swap Tesseract for a cloud OCR API by changing only
  this folder.

  ---
  watcher/ — Background listeners

  watcher/
  ├── change_stream.py   ← worker listens for new jobs
  ├── api_stream.py      ← API listens for completions
  └── polling.py         ← fallback for stuck jobs

  Why not put this in worker.py? A 200-line worker.py becomes unreadable. Each file has one job. change_stream.py = claim and run jobs.
  polling.py = heal stuck jobs.

  ---
  storage/ — File I/O

  storage/
  └── local.py     ← save uploads to disk, validate extensions

  Why a class? Tomorrow you might swap local disk for S3. If upload logic is scattered in routes, you change 10 files. With LocalStorage, you
   write a new S3Storage class and swap one line.

  ---
  websockets/ — Real-time connections

  websockets/
  └── manager.py    ← ConnectionManager singleton

  Tracks which WebSocket belongs to which request_id. Small but isolated because it has a distinct job.

  ---
  tests/ — Mirror your app structure

  tests/
  ├── conftest.py        ← shared fixtures (mock db, test client)
  ├── test_auth.py
  ├── test_api.py
  ├── test_models.py
  ├── test_ocr.py
  ├── test_repository.py
  ├── test_security.py
  ├── test_storage.py
  └── test_ws_manager.py

  Rule: One test file per source module. test_repository.py tests db/repository.py. Easy to find.

  ---
  main.py vs worker.py — Two entrypoints

  main.py    → starts FastAPI (serves HTTP + WebSocket)
  worker.py  → starts background OCR processor

  Why two files? They run as separate OS processes. Mixing them means OCR work slows down HTTP responses. Splitting lets you scale them
  independently — 1 API server, 5 workers.

  ---
  Template for Any New Backend Project

  my-service/
  ├── core/
  │   ├── config.py       ← env vars
  │   └── security.py     ← auth utilities
  ├── db/
  │   ├── client.py       ← connection
  │   ├── models.py       ← schemas
  │   └── repository.py   ← queries
  ├── api/
  │   ├── deps.py         ← shared dependencies
  │   └── routes/
  │       └── *.py        ← one file per domain
  ├── services/           ← business logic (use this instead of ocr/ for general apps)
  ├── tests/
  │   ├── conftest.py
  │   └── test_*.py
  └── main.py

  For this project services/ is called ocr/ because the domain is specific. In a general app (e-commerce, blog, etc.) you'd have
  services/orders.py, services/emails.py etc.

  ---
  The 3 Questions to Ask for Any New Folder

  1. What is it responsible for? (answer in 3 words)
  2. Who depends on it? (it should not depend back on them)
  3. Could you swap it out without touching other folders? (if yes, the boundary is right)
