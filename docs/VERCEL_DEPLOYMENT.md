# Vercel deployment

This repository is deployed as two Vercel projects:

- `backend/` is the FastAPI API and becomes one Vercel Function.
- `frontend/` is the Next.js customer and admin application.

Vercel does not provide a persistent PostgreSQL database for this application.
Create a hosted PostgreSQL database first, using a provider such as Neon,
Supabase, or Railway. Run the migrations against that database before using
the deployed API.

## 1. Deploy the backend

Create a Vercel project from this repository with these settings:

- Root Directory: `backend`
- Framework Preset: Other (or the automatically detected Python runtime)
- Build Command: leave blank

The backend contains `backend/pyproject.toml`, which points Vercel to
`app.main:app`, and `backend/vercel.json`, which allows requests to run for up
to 60 seconds. This follows Vercel's FastAPI entrypoint and Functions
configuration documented at <https://vercel.com/docs/frameworks/backend/fastapi>.

Add these environment variables to the backend project for Production,
Preview, and Development as appropriate:

```text
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE
JWT_SECRET=<long-random-production-secret>
JWT_EXPIRE_MINUTES=480
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://<frontend-project>.vercel.app
RAZORPAY_KEY_ID=<razorpay-key>
RAZORPAY_KEY_SECRET=<razorpay-secret>
RAZORPAY_WEBHOOK_SECRET=<razorpay-webhook-secret>
SEED_PLATFORM_ADMIN_EMAIL=<initial-admin-email>
SEED_PLATFORM_ADMIN_PASSWORD=<strong-initial-admin-password>
SEED_OWNER_PASSWORD=<strong-owner-password>
SEED_STAFF_PASSWORD=<strong-staff-password>
```

Use the async SQLAlchemy form `postgresql+asyncpg://` for `DATABASE_URL`. If
your database provider gives you a `postgresql://` URL, change the scheme to
`postgresql+asyncpg://` and preserve any provider-specific query parameters.

## 2. Apply the database migration

Run this from a local checkout after installing the backend requirements. Use
the same `DATABASE_URL` configured in Vercel:

```bash
cd backend
DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE' alembic upgrade head
```

For a new database, the existing seed command creates the initial platform
administrator and demo seller data. Only run it with intentionally chosen
production seed passwords:

```bash
DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST/DATABASE' \
SEED_PLATFORM_ADMIN_EMAIL='admin@example.com' \
SEED_PLATFORM_ADMIN_PASSWORD='<strong-password>' \
SEED_OWNER_PASSWORD='<strong-password>' \
SEED_STAFF_PASSWORD='<strong-password>' \
python -m app.db.seed
```

The seed data is intended for initial setup. Change or remove demo accounts
before treating the deployment as production.

## 3. Deploy the frontend

Create a second Vercel project from the same repository:

- Root Directory: `frontend`
- Framework Preset: Next.js
- Build Command: `npm run build` (the default is fine)

Set this environment variable before deploying:

```text
NEXT_PUBLIC_API_URL=https://<backend-project>.vercel.app/api/v1
NEXT_PUBLIC_RAZORPAY_KEY_ID=<same-public-razorpay-key-as-backend>
```

After the frontend project has its final domain, update the backend's
`CORS_ORIGINS` value to that exact origin, without a trailing slash. For
example:

```text
CORS_ORIGINS=https://water-can.vercel.app
```

If Preview deployments need to call the API, add their exact preview origin to
the comma-separated list as well.

## 4. Deploy with the CLI instead

From the repository root, link and deploy each project separately:

```bash
npm install --global vercel

cd backend
vercel link
vercel --prod

cd ../frontend
vercel link
vercel --prod
```

Set secrets with `vercel env add` or in the Vercel project dashboard. The
current Vercel FastAPI documentation requires CLI version 48.1.8 or newer.

## 5. Verify the deployment

Replace the placeholders with the real project URL:

```bash
curl -fsS https://<backend-project>.vercel.app/health
curl -fsS https://<backend-project>.vercel.app/api/v1/health
```

Then open the frontend URL, test seller selection and login, and configure the
Razorpay webhook URL as:

```text
https://<backend-project>.vercel.app/api/v1/payments/webhook
```
