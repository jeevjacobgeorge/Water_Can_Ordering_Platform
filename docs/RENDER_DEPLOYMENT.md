# Render deployment

This repository contains two applications under one Git repository:

- `backend/`: FastAPI API
- `frontend/`: Next.js application

The included [`render.yaml`](../render.yaml) defines both as Render Web
Services. It uses Render's native Python and Node runtimes, so Docker is not
required. Render supports monorepos by assigning each service a root directory;
commands then run relative to that directory.

## Recommended: deploy from the Blueprint

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. In Render, choose **New → Blueprint** and select the repository.
3. Review the two services from `render.yaml` and create them.
4. Enter the environment variables marked `sync: false`.

Create a hosted PostgreSQL database first. The database URL must use the async
SQLAlchemy scheme:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE
```

After the API service exists, set the frontend variable to its public URL:

```text
NEXT_PUBLIC_API_URL=https://water-can-api.onrender.com/api/v1
```

Set the API's `CORS_ORIGINS` to the frontend's exact public origin, for example:

```text
CORS_ORIGINS=https://water-can-frontend.onrender.com
```

Run the database migration once from the local checkout using the same
production database URL:

```bash
cd backend
DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE' alembic upgrade head
```

For a new database, run the seed command once with strong production seed
passwords to create the initial platform administrator and demo seller. Do not
reuse the development passwords from the local `.env` file.

## Manual API service setup

If you do not want to use the Blueprint, create a **Web Service** with these
settings:

| Render setting | Value |
| --- | --- |
| Root Directory | `backend` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Render's FastAPI guidance uses a Uvicorn command bound to `0.0.0.0` and the
platform-provided `$PORT`. The root directory is important: files outside it
are not available to the service at build or runtime.

## If you choose Docker instead

The original error occurred because Render looked for `./Dockerfile` at the
repository root. Use one of these configurations:

- Root Directory: `backend`; Runtime: **Docker**; Dockerfile Path: `Dockerfile`
- Or, with repository root as context: Dockerfile Path: `backend/Dockerfile`
  and Docker Context: `backend`

The first option is simpler. The backend Dockerfile now uses Render's `$PORT`
and falls back to port `8000` for local Docker Compose use. Do not use the
frontend Dockerfile for the API service.

## Frontend on Render or Vercel

The frontend can run on Render using the second service in the Blueprint, or it
can remain on Vercel. If it remains on Vercel, deploy only the API service on
Render and set the API's `CORS_ORIGINS` to the Vercel frontend URL.

Render free Web Services can spin down after inactivity, so the first request
after a quiet period may be slower. See Render's [Web Services
documentation](https://render.com/docs/web-services) for current service
behavior and limits.
