# Water Can Ordering & Delivery Platform

Small-business MVP for customer water-can ordering, Razorpay payment, owner
order management, staff delivery, and can balance tracking.

## Stack

- Next.js, React, TypeScript, Tailwind CSS
- FastAPI, Pydantic, SQLAlchemy 2.x, Alembic
- PostgreSQL
- Razorpay Checkout with server-side signature and webhook verification

## Local setup with Docker

On Ubuntu, run [`start.sh`](start.sh). It first runs [`stop.sh`](stop.sh), then
starts the services, applies the migration, seeds development data, and opens
the customer app when `xdg-open` is available. `run.sh` remains as a compatible
alias for `start.sh`.

1. Copy the local configuration:

   ```bash
   cp .env.example .env
   ```

2. Change the local JWT and seed passwords in `.env`.

3. Start the services:

   ```bash
   docker compose up --build
   ```

4. In a second terminal, apply the database migration and seed development data:

   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m app.db.seed
   ```

The frontend is at <http://localhost:3000>, the API is at
<http://localhost:8000>, and FastAPI documentation is at
<http://localhost:8000/docs>.

To open the app from another device on the same LAN, use
`http://192.168.1.23:3000`. The frontend must use
`http://192.168.1.23:8000/api/v1` as its API URL, and Ubuntu must allow TCP
ports 3000 and 8000 through its firewall.

## Local setup without Docker

Use Python 3.12, Node.js 20, and a PostgreSQL database. Install backend
dependencies with `pip install -r backend/requirements.txt`, install frontend
dependencies with `npm install` inside `frontend`, and provide matching
environment variables from the examples before starting each service.

Run the backend from `backend/` with:

```bash
uvicorn app.main:app --reload
```

Run the frontend from `frontend/` with:

```bash
npm run dev
```

## Project layout

```text
backend/            FastAPI application, models, migrations, and seed data
frontend/           Next.js customer application
spec.md             Product and implementation specification
docker-compose.yml
```

The current application includes seller/business tenants, seller onboarding,
seller-scoped products, customers, orders, staff, can balances, and settings.
The platform administrator portal is available under `/platform/login`; each
seller receives an owner account and a public ordering URL such as
`/?seller=aquapure-water-supply`. Seller owners use `/admin` for their own
orders and staff. Staff can currently use the staff API workflow; a dedicated
staff frontend remains to be built.

For local development, the seeded platform administrator is
`platform@watercan.dev` with the value of `SEED_PLATFORM_ADMIN_PASSWORD` in
`.env`. Use that account to create sellers at `/platform/sellers`.

For a detailed implementation inventory and continuation plan, see
[`docs/HANDOFF.md`](docs/HANDOFF.md).

## Deploy with Vercel

The repository is ready for a two-project Vercel deployment: create one
project rooted at `backend/` for FastAPI and another rooted at `frontend/` for
Next.js. A hosted PostgreSQL database is required. Follow the complete setup,
environment variable list, migration commands, and Razorpay webhook
configuration in [`docs/VERCEL_DEPLOYMENT.md`](docs/VERCEL_DEPLOYMENT.md).

Render deployment is also configured through [`render.yaml`](render.yaml). It
defines native FastAPI and Next.js web services with the correct monorepo root
directories and commands. See [`docs/RENDER_DEPLOYMENT.md`](docs/RENDER_DEPLOYMENT.md)
for Blueprint, manual, and Docker deployment instructions.
