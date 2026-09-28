# Water Can Platform — Agent Handoff

Last updated: 2026-09-27

This document is the working handoff for the next coding agent. The original
product and acceptance specification is [`spec.md`](../spec.md). Read this file
first, then inspect the existing source before changing architecture.

## Product goal

This is a multi-seller water-can ordering and delivery application for India.
The intended core flow is:

```text
Customer QR
  -> phone lookup
  -> quick refill or new customer details
  -> address and quantity
  -> Razorpay payment
  -> owner sees paid order
  -> staff assignment and delivery
  -> delivered/returned can ledger update
```

It is intentionally a monorepo with one Next.js frontend, one FastAPI backend,
and one PostgreSQL database. Keep the seller tenant boundaries in this
architecture; do not split it into microservices prematurely.

## Repository layout

```text
spec.md                  Complete product/build specification
README.md                Local setup and project overview
.env.example             Root Docker Compose environment template
.env                     Local ignored environment file created for development
docker-compose.yml       PostgreSQL, FastAPI, and Next.js services
start.sh                Ubuntu launcher; stops old services before starting
stop.sh                 Ubuntu Compose shutdown helper

backend/
  app/main.py            FastAPI application and /health
  app/api/v1/             API route modules
  app/core/               Settings, JWT security, and RBAC dependencies
  app/models/             SQLAlchemy models
  app/schemas/            Pydantic request/response schemas
  app/services/           Order number and status transition helpers
  app/db/seed.py          Development seed data
  migrations/             Alembic configuration and initial schema migration

frontend/
  app/page.tsx            Current customer ordering flow
  app/admin/               Seller owner login, dashboard, orders, and staff screens
  app/platform/            Platform administrator login and seller onboarding
  app/layout.tsx          Metadata and root layout
  app/globals.css         Tailwind/global styles
  package.json            Next.js/React/Tailwind dependencies and scripts

docs/HANDOFF.md           This document
```

## Stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS, App Router.
- Backend: Python 3.12, FastAPI 0.115, Pydantic 2, SQLAlchemy 2 async,
  Alembic, asyncpg.
- Database: PostgreSQL 16.
- Authentication: JWT access token, bcrypt password hashing, PLATFORM_ADMIN,
  OWNER, and STAFF RBAC.
- Payments: Razorpay SDK, server-side HMAC signature checks, webhook endpoint.

## Environment and local credentials

The ignored `.env` currently contains local-only development values. The
committed template is `.env.example`. If the ignored file is absent:

```bash
cp .env.example .env
```

The current local seed configuration uses:

```text
Owner: owner@watercan.dev / owner-development-password
Platform admin: platform@watercan.dev / platform-development-password
Staff: akhil@watercan.dev / staff-development-password
Staff: rahul@watercan.dev / staff-development-password
Customer: 9876543210
Customer: 9999999999
```

The platform admin manages sellers at `/platform/login` and
`/platform/sellers`. Each seller receives a slug such as
`aquapure-water-supply`; its public ordering URL is
`/?seller=aquapure-water-supply`.

These are development credentials only. Change them before using any shared or
production environment. Razorpay values are empty until test keys are added to
`.env`.

## Start the application

From the repository root:

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

The services are intended to be available at:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Swagger:  http://localhost:8000/docs
Health:   http://localhost:8000/health
```

Stop the services with:

```bash
docker compose down
```

The PostgreSQL volume is named `water-can_pgdata` or the Compose-generated
equivalent. Do not remove it casually because it contains local development
data.

## Implemented backend routes

All routes below are under `/api/v1` unless stated otherwise.

### Health and authentication

```text
GET  /health
GET  /api/v1/health
POST /auth/login
GET  /auth/me
```

Login accepts the seeded user email and password and returns a bearer JWT.

### Customer ordering

```text
GET   /customers/by-phone/{phone}
POST  /customers
PATCH /customers/{customer_id}

GET   /customers/{customer_id}/addresses
POST  /customers/{customer_id}/addresses
POST  /customers/{customer_id}/addresses/{address_id}/set-default

GET   /customers/{customer_id}/orders
GET   /customers/{customer_id}/can-balance
GET   /customers/{customer_id}/can-transactions
POST  /customers/{customer_id}/refill

GET   /products
PATCH /products/{product_id}       OWNER only

POST  /orders
GET   /orders/{order_id}
```

Order totals are calculated from the active database product and business
settings. The browser does not provide an authoritative price or total.

### Payments

```text
POST /payments/create-order
POST /payments/verify
POST /payments/webhook
```

Payment order creation reuses an existing provider order for the same local
order. Browser verification checks the Razorpay payment signature before
setting the order to `PAID`. The webhook checks its raw-body HMAC signature and
ignores duplicate captured events after the local order is already paid.

### Owner

All owner routes require a JWT with role `OWNER`.

```text
GET  /admin/dashboard

GET  /admin/staff
POST /admin/staff
PATCH /admin/staff/{staff_id}
POST /admin/staff/{staff_id}/activate
POST /admin/staff/{staff_id}/deactivate

GET  /admin/orders
GET  /admin/orders/{order_id}
POST /admin/orders/{order_id}/confirm
POST /admin/orders/{order_id}/assign
POST /admin/orders/{order_id}/unassign
POST /admin/orders/{order_id}/out-for-delivery
POST /admin/orders/{order_id}/delivered
POST /admin/orders/{order_id}/cancel
```

Owner order listing supports status, payment status, assigned staff, search by
order number/customer name/phone, pagination, and order detail responses.

### Staff

All staff routes require a JWT with role `STAFF`.

```text
GET  /staff/dashboard
GET  /staff/orders
GET  /staff/orders/available
POST /staff/orders/{order_id}/claim
```

Claiming locks the order row and checks its current status and assignment before
creating the assignment, preventing two staff members from claiming it in the
same transaction.

## Important business logic already implemented

### Order state machine

The allowed main path is:

```text
PENDING_PAYMENT -> PAID -> CONFIRMED -> ASSIGNED
                -> OUT_FOR_DELIVERY -> DELIVERED
```

Cancellation is allowed only from the states defined in
`backend/app/models/order.py`. Invalid transitions raise a conflict response.

### Can ledger

The owner delivery endpoint performs the following in one request transaction:

1. Locks the customer's balance row.
2. Validates returned cans will not make the balance negative.
3. Marks the order delivered.
4. Creates `order_can_summary`.
5. Updates `customer_can_balances`.
6. Creates separate `DELIVERED` and `RETURNED` ledger entries when quantities
   are nonzero.

The formula is:

```text
new balance = old balance + cans delivered - empty cans returned
```

Assignment history is stored as a list of `order_assignments`; the active
assignment is the entry whose `unassigned_at` is null.

## Current frontend behavior

`frontend/app/page.tsx` is a client component implementing the public customer
flow in one mobile-first page. The optional `seller` query parameter scopes the
flow to one business:

1. Reads the optional seller slug from the URL and fetches that seller's active
   product price.
2. Accepts and normalizes an Indian phone number.
3. Looks up an existing customer.
4. Shows the saved address and previous quantity for a refill.
5. Creates a new customer and default address when the phone is unknown.
6. Creates a server-priced order.
7. Loads Razorpay Checkout when a public test key is configured.
8. Calls backend payment verification and shows the order number on success.

The owner portal is available at `/admin` and stores the JWT in browser
localStorage. It includes `/admin/login`, `/admin`, `/admin/orders`, and
`/admin/staff`. From an order card, the owner can assign active staff, move an
order through delivery, and open a WhatsApp message addressed to the assigned
staff member's saved phone number. Staff still use the backend APIs directly
until a dedicated staff frontend is built.

The platform portal is available at `/platform/login` and supports creating,
listing, activating, and deactivating sellers. Creating a seller creates its
business settings and the first OWNER account.

## Verification completed

These checks have passed during this work:

```text
python -m compileall -q backend/app
FastAPI application import and route assertions
docker compose config --quiet
npm run typecheck
npm run build
```

The running frontend also returned HTTP 200 for `/`, `/admin/login`, `/admin`,
`/admin/orders`, and `/admin/staff`.

The local Docker services are currently running after applying the migration.
The existing PostgreSQL volume already contained seed data, so the seed command
skipped insertion; the local owner and staff password hashes were then
synchronized with the current ignored `.env` values.

The latest internal-container smoke check returned:

```text
owner_login:          200
staff_login:          200
auth/me:              200
customer lookup:      200
products:             200
order creation:       201
staff dashboard:      200
payment without keys: 503 (expected until Razorpay keys are configured)
```

The initial backend image exposed two dependency compatibility problems during
startup. They are fixed by lazy-loading Razorpay and pinning
`setuptools==75.8.0` plus `bcrypt==4.0.1`. The frontend image built once and is
running; a later full rebuild was blocked only by a transient Docker Hub
connection while refreshing the Node base-image metadata. `frontend/.dockerignore`
now excludes the locally installed `node_modules` and `.next` directories.

The frontend build reported that Next.js `14.2.15` has a security advisory and
npm reported two vulnerabilities. Upgrade Next.js and refresh the lockfile
before treating this as production-ready. A real Razorpay payment still cannot
be verified until test credentials are added.

## Known gaps and next work

The following work is still required to reach the full `spec.md` acceptance
criteria:

### Highest priority

1. Finish and smoke-test the Docker services with PostgreSQL, migration, and
   seed data.
2. Build `/staff` screens for assigned orders, available orders, claim, and
   delivery details.
3. Add owner settings, customer management, and can adjustment screens.

### Product features still missing

- PWA manifest, icons, service worker/install metadata, and QR instructions.
- Razorpay Route linked-account onboarding, commission calculation, transfers,
  refunds, and seller settlement reporting. Current Razorpay integration still
  processes the payment as a single platform-side payment.
- Owner settings and business pricing UI/API.
- Owner customer list/detail screens and can adjustment endpoint/UI.
- Staff mark-delivered flow if staff delivery completion is desired.
- Optional map location picker using Leaflet/OpenStreetMap.
- Separate customer route structure if the one-page flow becomes difficult to
  maintain.

### Reliability and security hardening

- Add an idempotency key for customer order creation and make the order-number
  generator safe under concurrent requests.
- Add a uniqueness rule for one active payment record/provider order per local
  order where appropriate.
- Add rate limiting or another abuse control around public phone lookup and
  customer creation before production.
- Review public order/customer data exposure before deployment; OTP is listed as
  a future enhancement in the product spec.
- Add consistent error response codes and centralized exception handling.

### Tests and documentation

- Add backend unit/integration tests for auth, customers, orders, payments,
  assignment races, and can tracking.
- Add frontend tests for customer, owner, staff, payment, and WhatsApp flows.
- Add `docs/API.md` and `docs/ARCHITECTURE.md`.
- Run lint, typecheck, backend tests, and end-to-end smoke checks in CI.

## Guidance for the next agent

- Preserve the existing simple monorepo architecture.
- Treat `business_id` as a mandatory tenant boundary for seller-owned data.
- Do not accept an arbitrary seller ID from an authenticated owner; derive it
  from the authenticated owner/staff account or a validated public seller slug.
- Use `apply_patch` for source edits.
- Keep prices server-side and keep payment verification server-side.
- Use existing models/schemas/services before adding abstractions.
- Run `docker compose exec backend alembic upgrade head` after migration
  changes, and seed only against disposable development data.
- Do not commit `.env`, real Razorpay keys, passwords, or generated build
  directories.
- When adding frontend routes, keep the mobile customer flow fast and use the
  existing API base variable `NEXT_PUBLIC_API_URL`.
