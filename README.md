# Bookmarks API (Django + DRF)

A production-style demo showing clean Django/DRF patterns, OpenAPI docs, and a simple Tailwind dashboard.

Live version: https://joshuaeastman.dev/bookmarks/v1/bookmarks/

> This is a demo application not designed for deployment.

---

## Quick Links (when running locally)

* **Admin:** http://localhost:8000/admin/
* **Docs (Swagger UI):** http://localhost:8000/bookmarks/docs/
* **Demo Dashboard:** http://localhost:8000/bookmarks/demo/
* **Health:** http://localhost:8000/bookmarks/v1/health/
* **Bookmarks List (JSON):** http://localhost:8000/bookmarks/v1/bookmarks/
* **Submit Bookmark (POST):** http://localhost:8000/bookmarks/v1/bookmarks/submit/

> Paths may differ slightly if you’ve customized URLs; these are the defaults in this repo.

---

## Requirements

* **Python** ≥ 3.13
* **Node.js & npm** (for Tailwind build via `django-tailwind`)
* (Recommended) **virtual environment**

---

## Quickstart (Development)

### 1) Clone & enter

```bash
git clone git@github.com:JoshuaEastman/BookmarksAPI.git
cd BookmarksAPI
```

### 2) Create & activate a virtualenv

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux (bash):**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install Python deps

```bash
pip install -r requirements.txt
```

### 4) Database migrations

```bash
python manage.py migrate
```

### 5) Tailwind (CSS) — one-time install, then build

```bash
python manage.py tailwind install
python manage.py tailwind build
```

> For live dev watching, use: `python manage.py tailwind start` (Ctrl+C to stop)

### 6) Create an admin user

```bash
python manage.py createsuperuser
```

### 7) Run the server

```bash
python manage.py runserver
```

Open http://localhost:8000/ and use the **Quick Links** above.

---

## Seeding Content

Visit **/admin/** and create a few Tags and Bookmarks. The API and demo dashboard will display whatever you add.

---

## Endpoints

### GET `/bookmarks/v1/bookmarks/`

Returns a paginated list of approved bookmarks. Supports filtering and search.

**Query parameters:**

* `?tag=python` → filter by tag slug
* `?search=django` → search title/description
* `?ordering=created_at` or `?ordering=-created_at`

**Example response**

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 8,
      "title": "Tailwind CSS Documentation",
      "url": "https://tailwindcss.com/docs/installation/using-vite",
      "description": "Documentation for Tailwind CSS",
      "tags": [
        "css",
        "documentation",
        "styling",
        "tailwind"
      ],
      "created_at": "2025-09-13T14:54:57.988437Z"
    }
  ]
}
```

### GET `/bookmarks/v1/bookmarks/{id}/`

Retrieve details of a single bookmark.

**Example Response**
```json
{
  "id": 8,
  "title": "Tailwind CSS Documentation",
  "url": "https://tailwindcss.com/docs/installation/using-vite",
  "description": "Documentation for Tailwind CSS",
  "tags": [
    "css",
    "documentation",
    "styling",
    "tailwind"
  ],
  "created_at": "2025-09-13T14:54:57.988437Z"
}
```

### POST `/bookmarks/v1/bookmarks/submit/`

Submit a new bookmark anonymously. Submissions are moderated (`is_approved=false` by default).

**Response (201 Created):**

```json
{
  "id": 1,
  "title": "Google",
  "url": "https://google.com",
  "description": "Google",
  "tags": [],
  "pending_tags": [
    "google"
  ],
  "is_approved": false,
  "created_at": "2025-09-16T22:12:17.397178Z"
}
```

> Unknown tags are returned in `pending_tags`.
> A honeypot field `website` will cause rejection if set.

### GET `/bookmarks/v1/health/`

Simple health/uptime check.

### GET `/bookmarks/docs/`

OpenAPI 3.1.1 docs (Swagger UI).

### GET `/bookmarks/demo/`

A small Tailwind dashboard with quick links to endpoints.

---

## Testing

This project uses `pytest` + `pytest-django`.

```bash
pip install pytest pytest-django
pytest -q
```

If needed, the repo includes a `pytest.ini` pointing to the Django settings module. Run tests from the project root (same folder as `manage.py`).

---

## Tailwind Notes

* This repo uses **django-tailwind**; Node/npm must be available.
* Build once with `python manage.py tailwind build`, or run the watcher with `python manage.py tailwind start` during development.

---

## Deployment (brief)

* Defaults to SQLite for local dev. For production, configure `DATABASE_URL` and `ALLOWED_HOSTS`.
* If you deploy with WhiteNoise, run `python manage.py collectstatic` and ensure `STATIC_ROOT` is set.

---

## License

MIT (see `LICENSE`).
