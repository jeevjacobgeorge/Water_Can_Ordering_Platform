# Water Can Ordering & Delivery Platform

Small-business MVP for customer water-can ordering, Razorpay payment, owner
order management, staff delivery, and can balance tracking.

## Stack

- Next.js, React, TypeScript, Tailwind CSS
- FastAPI, Pydantic, SQLAlchemy 2.x, Alembic
- PostgreSQL
- Razorpay integration planned for the payment phase

## Local setup with Docker

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

The application is being built phase by phase. The current foundation includes
the database schema and seed data, the health endpoint, the initial customer and
auth APIs, and a mobile landing page. Ordering, payments, dashboards, and
delivery workflows are implemented in later phases.
