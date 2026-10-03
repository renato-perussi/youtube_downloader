# youtube_downloader

## Quick start

```bash
source .venv/bin/activate
python manage.py migrate && python manage.py runserver
```

## Verify (run in this order)

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/python -m pytest -q
```

- Pytest config lives in `pyproject.toml` (`DJANGO_SETTINGS_MODULE=app.settings.test`, `testpaths=ytdownloader/tests`). No extra flags needed.
- Single test: `.venv/bin/python -m pytest ytdownloader/tests/test_views.py -q`.

## Settings / environment

- `app/settings/` is a package: `base.py` + `dev.py` (SQLite) / `prd.py` (PostgreSQL) / `test.py` (in-memory) selected by `ENVIRONMENT` in `app/settings/__init__.py`. There is no `app/settings.py` file.
- `ENVIRONMENT=test` is only used by pytest (via `pyproject.toml`), never set it in `.env`.
- Fail-closed in `prd`: `SECRET_KEY` must be ≥32 chars without weak markers and `DEBUG` must be `False`, else `ImproperlyConfigured` on boot. `test.py` forces `DEBUG=False`.
- `python-dotenv` loads `.env` from `BASE_DIR` in both `base.py` and `settings/__init__.py`.
- Locale `pt-br`, timezone `America/Sao_Paulo`. Django 6.0.6, yt-dlp 2026.8.19.
- System deps for yt-dlp: `ffmpeg` + Node.js 18+ (JS runtime; avoids deno fallback warning).

## Docker

- Prod: `docker compose -f docker-compose.yml up --build` (hardcodes `ENVIRONMENT=prd`, `DEBUG=False`, named volumes only, gunicorn 3 workers, non-root `appuser`, healthcheck on `/healthz/`).
- Dev: `docker compose up --build` picks up `docker-compose.override.yml` (bind mount `.:/app`, `ENVIRONMENT=dev`, `runserver`).
- `entrypoint.sh` runs only `migrate --noinput` + `collectstatic`; never `makemigrations` in containers.
- `docs/` screenshots are in `.dockerignore` (excluded from image, still in repo).

## Multi-tenant architecture

- One `Tenant` per `User`, created by `post_save` signal calling `Tenant.resolve()`. Slug = `slugify(username)` with `-1/-2` suffix loop on collision (usernames like `User.Name` and `UserName` collide).
- All `ytdownloader` URLs are slug-prefixed; `TenantAwareMixin.dispatch` resolves `request.tenant`, redirects wrong slugs via `reverse()` preserving querystring, and redirects anonymous to login (it assumes `LoginRequiredMixin` first but guards anyway).
- File/JSON views (`ServeDownloadView`, `DownloadProgressJsonView`, `DownloadAllView`) additionally filter `tenant__slug + tenant__user` → cross-tenant access is 404.
- `context_processors.py` exposes `request_tenant`. Root `/` redirects by auth state (`RootRedirectView`).

## Code layout (packages, not files)

- `ytdownloader/models/{choices,tenant,download}.py` — `DownloadQuerySet.for_tenant()/completed()/search()` holds filter logic; don't inline ORM filters in views.
- `ytdownloader/forms/{search,download}.py` + canonical URL validator at `ytdownloader/validators.py` (`forms/validators.py` is just a re-export). Both forms enforce the YouTube host whitelist (anti-SSRF); `DownloadForm.clean_quality` guards `None` and cross-validates video-vs-audio.
- `ytdownloader/services/` — pure logic, no `request`: `ytdlp.py` (`get_video_info` rejects non-whitelisted URLs, lives, >2h videos; `download_video` takes `download_id` so `outtmpl` is `{id}_%(title)s`, unique per job), `downloads.py` (thread orchestration, `BoundedSemaphore(2)` **per process** — 6 real slots under gunicorn's 3 workers; `create_and_start_download` acquires **before** creating to avoid orphan rows), `files.py` (ZIP capped at 100 files / 500 MB, `ZIP_DEFLATED`), `exceptions.py` (`safe_error_message` regex masks signed URLs — always log through it, never raw `exc`).
- `ytdownloader/views/` — 100% CBV, zero FBVs: `auth.py` (`RegisterView`, `LoginRedirectView`, `RootRedirectView`), `home.py`, `search.py` (`handle_download` revalidates via `get_video_info` then checks semaphore; catches `DownloadServiceError` into form errors, never 500), `history.py`, `progress.py`, `files.py`, `health.py` (`/healthz/` does `SELECT 1`, 503 on failure), `mixins.py`. `ytdownloader/utils.py` is an untested legacy shim (excluded from coverage) — don't add imports to it.
- `Tenant.resolve()` uses `transaction.atomic` + retry; `run_download_job` calls `close_old_connections()` around the download.

## Conventions

- Ruff is the only linter/formatter (`quote-style='single'`); `requirements-dev.txt` intentionally omits black/blue/flake8/isort (they were uninstalled — do not reintroduce).
- `RUF012` is ignored project-wide (Django admin/model attrs). `SIM115` on the `FileResponse(open(...))` in `views/files.py` is a deliberate `noqa` (Django closes the handle).
- `SECURE_SSL_REDIRECT` and cookie/HSTS settings in `prd.py` default to off (env opt-in) so the HTTP quickstart works; enable behind a TLS proxy. Documented in `.env.example`.
- Screenshots live in `docs/screenshots/` and are referenced from `README.md` with relative paths.
- Migrations are real files (`migrations/0001_initial.py` exists); `makemigrations` is expected after model changes, just never inside containers.
