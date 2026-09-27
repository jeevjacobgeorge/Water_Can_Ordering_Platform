# WATER CAN ORDERING & DELIVERY PLATFORM — MASTER BUILD PROMPT

## 1. ROLE

Act as a **Senior Full-Stack Engineer + Software Architect + Product Engineer**.

Build a small, production-ready but intentionally simple **Water Can Ordering & Delivery Platform** for a **single small-scale water-can business in India**.

This is NOT a marketplace and NOT a multi-vendor platform.

There is exactly **one business/owner** in the system.

The main goal is to make ordering extremely easy for customers:

**Scan QR → enter phone number → choose/refill cans → confirm address → pay → order created → owner/staff receive delivery order.**

The platform must work extremely well on mobile because most customers will access it from a QR code using their phone.

---

# 2. IMPORTANT DEVELOPMENT RULES

Follow these rules throughout development:

1. **Do not over-engineer the MVP.**
2. Do not introduce unnecessary microservices.
3. Do not add features that are not required.
4. Prefer simple, maintainable code.
5. Prefer boring and reliable technologies over complicated architecture.
6. Do not make major architectural decisions when a simple implementation is obvious.
7. Do not repeatedly ask me to choose between technologies when this prompt already specifies them.
8. Make reasonable assumptions when something minor is unspecified.
9. Keep the code modular so features can be added later.
10. Do not generate the entire application in one huge response.
11. Build it **phase by phase**.
12. After every phase:

* implement the required files/code
* run tests
* run lint/type checks where applicable
* fix obvious errors
* summarize what was completed
* state the next phase

13. Do not rewrite working code unnecessarily.
14. Keep the UI simple and practical rather than visually complicated.
15. Use environment variables for secrets and API keys.
16. Never hard-code passwords, API keys, payment secrets, JWT secrets, database credentials, etc.
17. Generate `.env.example`.
18. Add database migrations.
19. Add seed data for development.
20. Add API validation and useful error responses.
21. Add audit-friendly timestamps to important records.
22. Consider duplicate requests and payment callbacks. Payment/order creation must be idempotent where appropriate.

---

# 3. FIXED TECH STACK

Use this stack unless there is a strong technical reason something must change.

## Frontend

* Next.js
* React
* TypeScript
* App Router
* Tailwind CSS
* Mobile-first responsive design
* PWA support
* Simple component architecture

The customer website should feel like a mobile ordering app even though it is a web application.

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy 2.x
* Alembic
* PostgreSQL
* PostgreSQL driver appropriate for async FastAPI usage

Use a clean layered architecture:

```text
API / Routes
    ↓
Services / Business Logic
    ↓
Repositories / Database access
    ↓
PostgreSQL
```

Do not create excessive abstraction layers.

## Authentication

For owner/staff:

* JWT access tokens
* Password hashing using a secure password hashing library
* Role-based access control

Roles:

```text
OWNER
STAFF
```

Customers do NOT need to create a traditional account.

For the MVP, identify customers primarily using their phone number.

Customer OTP authentication can be added later if required.

## Payments

Use **Razorpay** because this is an Indian business.

Payment flow:

```text
Customer creates order
        ↓
Backend creates Razorpay payment/order
        ↓
Customer completes payment
        ↓
Frontend verifies payment
        ↓
Backend verifies Razorpay signature
        ↓
Order marked as PAID
```

Never trust payment status sent directly by the frontend.

Also implement a Razorpay webhook endpoint for reliable payment confirmation.

## Maps / Address

Do not require Google Maps for the MVP.

Prefer:

* OpenStreetMap
* Leaflet or MapLibre

The customer should primarily be able to:

* enter address manually
* enter pincode
* optionally select/share a map location
* optionally save latitude/longitude

The map feature is a convenience, not a dependency for placing an order.

## WhatsApp

Do NOT integrate the WhatsApp Business API in the MVP.

Use a WhatsApp deep link:

```text
https://wa.me/<phone>?text=<encoded-message>
```

This lets the owner click a button and open WhatsApp with a pre-filled order message.

A proper WhatsApp Business API integration can be added later.

---

# 4. PRODUCT SCOPE

The application has three major areas:

## A. Customer Ordering App

Mobile-first public website.

Customer can:

1. Scan QR code.
2. Open ordering page.
3. Enter phone number.
4. Existing customer:

   * retrieve previous customer information
   * show saved/default address
   * show previous order/refill information
   * select number of cans
   * quickly reorder
5. New customer:

   * enter name
   * phone number
   * address
   * pincode
   * optionally select map location
6. Choose quantity.
7. See total price.
8. Pay using Razorpay.
9. See order confirmation.
10. Receive order ID/details.

---

# 5. CUSTOMER UX — IMPORTANT

The most important interaction is the **repeat-refill flow**.

A common customer journey should be:

```text
Scan QR
   ↓
Enter phone number
   ↓
Customer recognized
   ↓
"Welcome back"
   ↓
Show last/default address
   ↓
Choose cans:
[-]  2  [+]
or
5 cans
or
10 cans
   ↓
Show total
   ↓
Pay
   ↓
Order confirmed
```

Make repeat ordering extremely fast.

Example:

### Customer has ordered before

Phone:

```text
9876543210
```

Backend finds existing customer.

Show:

```text
Welcome back!

Delivery to:
John George
Pallimukku, Trivandrum
695xxx

Previous order:
5 cans

How many cans today?

[-] 5 [+]
```

Buttons:

```text
Use this address
Change address
Continue to payment
```

---

# 6. NEW CUSTOMER FLOW

If the phone number is not found:

```text
Phone number
Name
Address
Pincode
Optional map location
Number of cans
```

Then:

```text
Order summary
↓
Payment
↓
Confirmation
```

After successful order, create the customer record and save the address.

---

# 7. CUSTOMER ADDRESS REQUIREMENTS

Support multiple addresses in the database even though the MVP UI can primarily use one default address.

Address fields:

```text
id
customer_id
label
address_line_1
address_line_2
city
district
state
pincode
latitude
longitude
is_default
created_at
updated_at
```

Possible labels:

```text
Home
Office
Other
```

For MVP, the customer should generally see the default/saved address first.

---

# 8. WATER CAN PRODUCT MODEL

For the MVP there is essentially one product:

```text
Water Can
```

The owner must be able to configure:

```text
price_per_can
```

Example:

```text
₹50 per can
```

Do not hard-code the price into frontend code.

Store product/pricing information in the database or a simple settings table.

---

# 9. ORDER MODEL

Every order should contain:

```text
order_number
customer
address
quantity
price_per_can
subtotal
delivery_charge
discount
total_amount
payment_status
order_status
delivery_slot
notes
created_at
updated_at
```

Suggested order statuses:

```text
PENDING_PAYMENT
PAID
CONFIRMED
ASSIGNED
OUT_FOR_DELIVERY
DELIVERED
CANCELLED
```

Suggested payment statuses:

```text
PENDING
PAID
FAILED
REFUNDED
```

Keep payment status separate from delivery/order status.

---

# 10. CAN INVENTORY / CAN DEPOSIT TRACKING

This is an IMPORTANT BUSINESS REQUIREMENT.

The business needs to know how many physical water cans are currently with each customer.

Every delivered order must record:

```text
cans_delivered
empty_cans_returned
```

Example:

Customer currently has:

```text
4 cans
```

Customer orders:

```text
3 filled cans
```

Delivery happens.

Customer returns:

```text
2 empty cans
```

New balance:

```text
4 + 3 - 2 = 5 cans
```

Therefore:

```text
customer_can_balance = previous_balance
                       + cans_delivered
                       - empty_cans_returned
```

Do NOT rely only on manually edited balances.

Maintain a transaction/ledger history.

Example:

```text
CAN_DELIVERED +3
CAN_RETURNED  -2
```

This provides an audit trail.

---

# 11. CAN INVENTORY TABLES

Implement at least these concepts:

## customer_can_balance

```text
id
customer_id
current_balance
updated_at
```

## can_transactions

```text
id
customer_id
order_id
transaction_type
quantity
balance_after
notes
created_at
```

Transaction types:

```text
DELIVERED
RETURNED
ADJUSTMENT
```

For an order:

```text
cans_delivered = 5
empty_cans_returned = 3
```

The transaction history should allow us to calculate:

```text
5 delivered
3 returned
current balance change = +2
```

The owner should be able to see the customer's current can balance.

---

# 12. OWNER DASHBOARD

Create an authenticated dashboard for the owner.

Main dashboard should show:

```text
Today's Orders
Pending Orders
Paid Orders
Assigned Orders
Out for Delivery
Delivered
Cancelled
```

Also show useful business information:

```text
Today's revenue
Today's cans ordered
Today's delivered cans
Today's returned empty cans
Total cans currently with customers
```

Keep dashboard visually simple.

---

# 13. OWNER ORDER MANAGEMENT

Owner should be able to:

* view all orders
* filter orders
* search by:

  * order number
  * customer name
  * phone number
* view order details
* view address
* view map coordinates if available
* view payment status
* view can quantity
* view previous orders
* view customer's can balance
* assign order to a staff member
* mark order as confirmed
* mark order as out for delivery
* mark order as delivered
* record empty cans returned
* cancel order
* generate WhatsApp message
* share order details via WhatsApp

---

# 14. STAFF / DELIVERY PARTNER SYSTEM

The owner can create staff accounts.

Staff fields:

```text
name
phone
username/email
password hash
role = STAFF
active/inactive
```

Staff login should open the same dashboard style.

However, staff permissions are restricted.

## STAFF CAN:

* log in
* see available orders that they are allowed to see
* see orders assigned to them
* see order details
* see customer name
* see phone
* see address
* see quantity
* see payment status
* see can return information
* claim an eligible unassigned order for themselves

## STAFF CANNOT:

* manage staff
* change pricing
* edit business settings
* delete customers
* access sensitive system settings
* assign orders to another staff member
* change owner account
* access unrestricted customer management

Staff can only perform the minimum delivery-related actions necessary.

If a staff member claims an order:

```text
assigned_to = current_staff_id
order_status = ASSIGNED
```

The claim operation must be atomic so two staff members cannot claim the same order simultaneously.

---

# 15. OWNER ASSIGNMENT FLOW

Owner opens:

```text
Order #WC-1023
```

Owner sees:

```text
Assigned to:
[ Unassigned ▼ ]

Staff:
Rahul
Akhil
Vishnu
```

Owner chooses:

```text
Akhil
```

Then:

```text
assigned_to = Akhil
order_status = ASSIGNED
```

Staff dashboard immediately shows it.

---

# 16. STAFF SELF-ASSIGNMENT FLOW

For orders that are eligible for staff self-assignment:

```text
Available Orders

Order #WC-1023
5 cans
Pattom
PAID

[Claim Order]
```

Clicking:

```text
Claim Order
```

assigns the order to the logged-in staff user.

Prevent race conditions so the same order cannot be claimed by two staff members.

---

# 17. WHATSAPP SHARING

The owner should have a button:

```text
Share on WhatsApp
```

Generate a concise message.

Example:

```text
Water Delivery Order

Order: WC-1023
Customer: John George
Phone: 9876543210

Address:
Pattom, Trivandrum
Kerala - 695004

Water Cans: 5
Payment: PAID

Can Return Expected: 3

Delivery Status: Assigned
```

The WhatsApp link should open WhatsApp with the message pre-filled.

Do not require a WhatsApp API account for the MVP.

---

# 18. AUTHENTICATION

## OWNER

Owner login:

```text
email/username
password
```

After login:

```text
POST /api/v1/auth/login
```

Return JWT access token.

Protect owner APIs using RBAC.

## STAFF

Staff also logs in through the same authentication endpoint.

JWT should contain user ID and role.

Example:

```json
{
  "sub": "user-id",
  "role": "STAFF"
}
```

Never trust role information sent by the frontend.

Verify role server-side.

---

# 19. DATABASE SCHEMA

Use PostgreSQL.

Create the following core tables.

## users

```text
id UUID PRIMARY KEY
name
phone
email
password_hash
role
is_active
created_at
updated_at
```

Roles:

```text
OWNER
STAFF
```

Customers should be stored separately.

---

## customers

```text
id UUID PRIMARY KEY
name
phone UNIQUE
email NULLABLE
is_active
created_at
updated_at
```

The phone number is the primary lookup identifier for customer ordering.

---

## customer_addresses

```text
id UUID PRIMARY KEY
customer_id UUID REFERENCES customers(id)
label
address_line_1
address_line_2
city
district
state
pincode
latitude
longitude
is_default
created_at
updated_at
```

---

## products

```text
id UUID PRIMARY KEY
name
description
price_per_unit
unit_name
is_active
created_at
updated_at
```

Example:

```text
name = 20L Water Can
unit_name = can
```

The actual product size should be configurable.

---

## orders

```text
id UUID PRIMARY KEY
order_number UNIQUE
customer_id REFERENCES customers(id)
address_id REFERENCES customer_addresses(id)
quantity
price_per_unit
subtotal
delivery_charge
discount
total_amount
payment_status
order_status
delivery_slot
customer_notes
created_at
updated_at
```

---

## order_assignments

```text
id UUID PRIMARY KEY
order_id REFERENCES orders(id)
staff_id REFERENCES users(id)
assigned_by UUID REFERENCES users(id)
assigned_at
unassigned_at NULLABLE
```

This provides assignment history.

---

## order_can_summary

```text
id UUID PRIMARY KEY
order_id REFERENCES orders(id)
cans_delivered
empty_cans_returned
notes
created_at
updated_at
```

---

## customer_can_balances

```text
id UUID PRIMARY KEY
customer_id UNIQUE REFERENCES customers(id)
current_balance
updated_at
```

---

## can_transactions

```text
id UUID PRIMARY KEY
customer_id REFERENCES customers(id)
order_id NULLABLE REFERENCES orders(id)
transaction_type
quantity
balance_before
balance_after
notes
created_by UUID REFERENCES users(id)
created_at
```

---

## payments

```text
id UUID PRIMARY KEY
order_id REFERENCES orders(id)
provider
provider_order_id
provider_payment_id
amount
currency
status
payment_method
raw_reference NULLABLE
created_at
updated_at
```

Do not store unnecessary sensitive payment information.

---

## business_settings

Use this for simple single-vendor configuration.

Example:

```text
business_name
business_phone
business_address
price_per_can
currency
default_delivery_charge
```

---

# 20. DATABASE RULES

Use:

* UUID primary keys
* UTC timestamps in database
* proper foreign keys
* indexes for frequent queries
* unique phone number for customers
* unique order number
* indexes on:

  * customer phone
  * order status
  * payment status
  * assigned staff
  * created_at

Use SQLAlchemy models and Alembic migrations.

Do not manually modify production schema without migrations.

---

# 21. ORDER NUMBER

Generate human-friendly order numbers.

Example:

```text
WC-20260927-0001
WC-20260927-0002
```

Internal ID can still be UUID.

Customers and staff see `order_number`, not the UUID.

---

# 22. BACKEND API STRUCTURE

Base URL:

```text
/api/v1
```

---

# 23. AUTH API

## Login

```http
POST /api/v1/auth/login
```

Request:

```json
{
  "username": "owner",
  "password": "password"
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "name": "Owner",
    "role": "OWNER"
  }
}
```

## Current user

```http
GET /api/v1/auth/me
```

---

# 24. CUSTOMER APIs

Customer lookup:

```http
GET /api/v1/customers/by-phone/{phone}
```

Return only information that is appropriate for the customer flow.

For an existing customer, return:

```text
customer id
name
masked/known phone
default address
saved addresses
last order
common order quantities
current can balance
```

Do not expose payment secrets or internal staff data.

---

## Create customer

```http
POST /api/v1/customers
```

Request:

```json
{
  "name": "John George",
  "phone": "9876543210"
}
```

---

## Update customer

```http
PATCH /api/v1/customers/{customer_id}
```

---

# 25. CUSTOMER ADDRESS APIs

List addresses:

```http
GET /api/v1/customers/{customer_id}/addresses
```

Create address:

```http
POST /api/v1/customers/{customer_id}/addresses
```

Update address:

```http
PATCH /api/v1/addresses/{address_id}
```

Set default:

```http
POST /api/v1/addresses/{address_id}/set-default
```

---

# 26. PRODUCT / PRICING APIs

Public product information:

```http
GET /api/v1/products
```

Owner:

```http
POST /api/v1/products
PATCH /api/v1/products/{product_id}
```

Or use a simple business setting if only one product exists.

---

# 27. ORDER APIs

Create order:

```http
POST /api/v1/orders
```

Request example:

```json
{
  "customer_id": "...",
  "address_id": "...",
  "quantity": 5,
  "delivery_slot": "MORNING",
  "customer_notes": "Please call when arriving"
}
```

Response should include:

```text
order_id
order_number
amount
payment_required
payment information
```

---

## Get order

```http
GET /api/v1/orders/{order_id}
```

---

## Customer's previous orders

```http
GET /api/v1/customers/{customer_id}/orders
```

Support pagination.

---

## Refill / repeat order

Create a convenience endpoint:

```http
POST /api/v1/customers/{customer_id}/refill
```

Request:

```json
{
  "quantity": 5,
  "address_id": "...",
  "delivery_slot": "MORNING"
}
```

This should make repeat ordering simple.

---

# 28. PAYMENT APIs

Create Razorpay order:

```http
POST /api/v1/payments/create-order
```

Request:

```json
{
  "order_id": "..."
}
```

Return the information required by Razorpay Checkout.

---

## Verify payment

```http
POST /api/v1/payments/verify
```

Request:

```json
{
  "order_id": "...",
  "razorpay_order_id": "...",
  "razorpay_payment_id": "...",
  "razorpay_signature": "..."
}
```

Backend must verify signature.

Never simply trust:

```text
payment_success=true
```

from the browser.

---

## Razorpay webhook

```http
POST /api/v1/payments/webhook
```

Verify webhook signature.

Handle relevant events such as payment success/failure.

Webhook processing must be idempotent.

---

# 29. OWNER ORDER APIs

List orders:

```http
GET /api/v1/admin/orders
```

Support filters:

```text
status
payment_status
assigned_staff
date_from
date_to
search
page
page_size
```

---

## Get order details

```http
GET /api/v1/admin/orders/{order_id}
```

---

## Confirm order

```http
POST /api/v1/admin/orders/{order_id}/confirm
```

---

## Assign order

```http
POST /api/v1/admin/orders/{order_id}/assign
```

Request:

```json
{
  "staff_id": "..."
}
```

---

## Unassign order

```http
POST /api/v1/admin/orders/{order_id}/unassign
```

---

## Mark out for delivery

```http
POST /api/v1/admin/orders/{order_id}/out-for-delivery
```

---

## Mark delivered

```http
POST /api/v1/admin/orders/{order_id}/delivered
```

Request:

```json
{
  "cans_delivered": 5,
  "empty_cans_returned": 3,
  "notes": "2 empty cans received"
}
```

This operation must update the customer can balance safely and transactionally.

---

## Cancel order

```http
POST /api/v1/admin/orders/{order_id}/cancel
```

---

# 30. STAFF APIs

Staff list:

```http
GET /api/v1/admin/staff
```

Create staff:

```http
POST /api/v1/admin/staff
```

Update staff:

```http
PATCH /api/v1/admin/staff/{staff_id}
```

Activate/deactivate:

```http
POST /api/v1/admin/staff/{staff_id}/activate
POST /api/v1/admin/staff/{staff_id}/deactivate
```

Staff's assigned orders:

```http
GET /api/v1/staff/orders
```

Available orders:

```http
GET /api/v1/staff/orders/available
```

Claim order:

```http
POST /api/v1/staff/orders/{order_id}/claim
```

The backend must verify:

```text
user.role == STAFF
```

and perform the claim atomically.

---

# 31. DASHBOARD API

Owner dashboard:

```http
GET /api/v1/admin/dashboard
```

Return aggregated information:

```json
{
  "today": {
    "orders": 12,
    "paid_orders": 10,
    "delivered_orders": 7,
    "revenue": 3500,
    "cans_ordered": 70,
    "cans_delivered": 65,
    "empty_cans_returned": 48
  },
  "pending_orders": 3,
  "unassigned_orders": 2,
  "out_for_delivery": 2
}
```

Staff dashboard:

```http
GET /api/v1/staff/dashboard
```

Show their assigned/available work.

---

# 32. CAN INVENTORY APIs

Customer can balance:

```http
GET /api/v1/customers/{customer_id}/can-balance
```

Can ledger:

```http
GET /api/v1/customers/{customer_id}/can-transactions
```

Owner can manually correct inventory:

```http
POST /api/v1/admin/customers/{customer_id}/can-adjustment
```

Request:

```json
{
  "quantity": -1,
  "notes": "Damaged can removed"
}
```

All adjustments must be recorded in the ledger.

Never silently change a balance.

---

# 33. FRONTEND ROUTES

Use a clear Next.js route structure.

Suggested public pages:

```text
/
 /order
 /order/customer
 /order/address
 /order/summary
 /order/payment
 /order/success
```

Admin:

```text
/admin/login
/admin
/admin/orders
/admin/orders/[id]
/admin/staff
/admin/customers
/admin/customers/[id]
/admin/settings
```

Staff:

```text
/staff
/staff/orders
/staff/orders/[id]
```

Do not make the routing unnecessarily complicated.

---

# 34. CUSTOMER UI

The UI should be extremely mobile friendly.

Use large touch targets.

Avoid complicated navigation.

Primary screens:

### Screen 1 — Start Order

```text
[Business Logo]

Fresh Water Delivered To Your Door

Phone Number

[ 9876543210 ]

[ Continue ]
```

---

### Screen 2 — Existing Customer

```text
Welcome back, John 👋

Deliver to:

John George
Pattom
Trivandrum - 695004

[ Use this address ]

Change address

How many cans?

[ - ]  5  [ + ]

₹250

[ Continue to Payment ]
```

---

### Screen 3 — New Customer

```text
Your details

Name
Phone
Address
Pincode

[ Select location on map ]

[ Save & Continue ]
```

---

### Screen 4 — Order Summary

```text
Order Summary

Water Cans     5 × ₹50
Delivery       ₹0
---------------------
Total          ₹250

Deliver to:
Pattom, Trivandrum

[ Pay ₹250 ]
```

---

### Screen 5 — Success

```text
✓ Order Confirmed

Order #WC-20260927-0001

5 Water Cans

Payment: PAID

We'll deliver your order soon.

[ Back to Home ]
```

---

# 35. OWNER DASHBOARD UI

Desktop + mobile responsive.

Top area:

```text
Today's Orders: 12
Pending: 3
Assigned: 4
Out for Delivery: 2
Delivered: 7
Revenue: ₹3,500
```

Order table/cards:

```text
WC-20260927-0001

John George
9876543210

5 cans
₹250
PAID

Pattom, Trivandrum

Assigned:
Akhil

[View]
[Assign]
[WhatsApp]
[Mark Delivered]
```

On mobile, convert table rows into cards.

---

# 36. STAFF DASHBOARD UI

Staff sees:

```text
Hello Akhil

My Orders
----------------

WC-20260927-0001
John George
5 cans
Pattom

[Open]
```

Available orders:

```text
Available Orders

WC-20260927-0005
3 cans
Kazhakkoottam
PAID

[Claim]
```

Staff should not see owner-only configuration screens.

---

# 37. API RESPONSE FORMAT

Prefer consistent API responses.

For successful standard responses:

```json
{
  "data": {},
  "message": "Success"
}
```

For errors:

```json
{
  "detail": "Human readable error message",
  "code": "ORDER_NOT_FOUND"
}
```

Use appropriate HTTP status codes.

Examples:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
500 Internal Server Error
```

---

# 38. VALIDATION

Phone number:

* validate Indian mobile number format reasonably
* normalize input
* prevent obvious duplicates

Pincode:

* validate 6 digit Indian pincode

Quantity:

* positive integer
* enforce sensible maximum

Address:

* required for a first-time customer
* saved address can be reused

Payment:

* amount must always be calculated server-side

Never trust price/total sent from the browser.

Example:

The frontend sends:

```json
{
  "quantity": 5
}
```

Backend calculates:

```text
5 × current_price
```

Do not accept:

```json
{
  "quantity": 5,
  "total": 1
}
```

as authoritative.

---

# 39. SECURITY REQUIREMENTS

Implement basic but real security.

Must include:

* password hashing
* JWT authentication
* role-based authorization
* request validation
* SQL injection protection through ORM/parameterized queries
* CORS configuration
* environment-based secrets
* Razorpay signature verification
* webhook signature verification
* no payment secrets on frontend
* no password in logs
* no unnecessary sensitive data in API responses

Do not expose internal IDs or secrets unnecessarily.

---

# 40. ORDER STATE RULES

Prevent invalid status transitions.

Example:

```text
PENDING_PAYMENT
        ↓
PAID
        ↓
CONFIRMED
        ↓
ASSIGNED
        ↓
OUT_FOR_DELIVERY
        ↓
DELIVERED
```

Cancellation should only be allowed in sensible states.

Do not allow:

```text
DELIVERED → ASSIGNED
```

unless there is a specific admin correction operation.

Create a small order state transition service so this logic is centralized.

---

# 41. TRANSACTIONAL CAN BALANCE UPDATE

When marking an order delivered:

Perform one database transaction:

```text
BEGIN

update order
set status = DELIVERED

create/update order_can_summary

read customer's current can balance

calculate:
new_balance =
    old_balance
    + cans_delivered
    - empty_cans_returned

update customer_can_balance

create can transaction for DELIVERED
create can transaction for RETURNED if applicable

COMMIT
```

If anything fails:

```text
ROLLBACK
```

Never leave the order marked delivered while the can balance is only partially updated.

---

# 42. IDEMPOTENCY / DUPLICATE PROTECTION

The customer may accidentally press the payment button twice.

Prevent duplicate orders where possible.

Payment creation should be safely repeatable.

Razorpay webhook may also be delivered more than once.

Process the same payment event only once.

Do not create duplicate can transactions from duplicate webhook events.

---

# 43. LOGGING

Implement useful application logs.

Log things such as:

```text
order created
payment verified
order assigned
order delivered
staff created
```

Do NOT log:

```text
passwords
JWT tokens
payment secrets
Razorpay secret keys
```

---

# 44. TESTING REQUIREMENTS

Backend tests should cover at minimum:

### Customer

* create customer
* lookup by phone
* create address
* retrieve saved address

### Orders

* create order
* calculate total
* invalid quantity
* invalid address
* order status transition
* cancellation

### Payments

* payment verification
* invalid Razorpay signature
* duplicate payment event

### Assignment

* owner assigns staff
* staff sees assigned order
* staff claims order
* two staff members cannot claim the same order

### Can tracking

Example test:

```text
starting balance = 4

delivery = 5
returned = 3

expected balance = 6
```

Also test:

```text
DELIVERED +5
RETURNED -3
```

ledger entries.

---

# 45. FRONTEND TESTING

At minimum test:

* customer can enter phone number
* existing customer refill flow
* new customer flow
* quantity selector
* total calculation display
* payment initiation
* order success screen
* owner login
* staff login
* role-based navigation
* claim order button
* owner assignment
* WhatsApp share button

---

# 46. SEED DATA

Create development seed data:

## Owner

```text
name: Demo Owner
role: OWNER
```

## Staff

```text
Akhil
Rahul
```

## Customer

```text
John George
phone: 9876543210
```

## Example orders

Create:

```text
pending order
paid order
assigned order
out-for-delivery order
delivered order
```

Create can-balance examples as well.

Do not put real credentials in the repository.

Use development-only passwords through environment variables or seed configuration.

---

# 47. PROJECT STRUCTURE

Prefer a structure approximately like:

```text
water-can-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── db/
│   │   └── main.py
│   │
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   ├── public/
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

You may improve the exact folder structure, but keep it simple.

---

# 48. LOCAL DEVELOPMENT

Provide Docker Compose for:

```text
PostgreSQL
Backend
Frontend
```

The application should be runnable locally with a simple command such as:

```bash
docker compose up --build
```

Also document non-Docker development if useful.

---

# 49. ENVIRONMENT VARIABLES

Create `.env.example`.

Backend examples:

```env
DATABASE_URL=
JWT_SECRET=
JWT_EXPIRE_MINUTES=

RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=

CORS_ORIGINS=
```

Frontend:

```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_RAZORPAY_KEY_ID=
```

Never commit actual secrets.

---

# 50. PWA REQUIREMENTS

The customer website should be installable as a PWA.

Include:

* web manifest
* icons
* responsive layout
* mobile viewport
* basic offline fallback where practical

Do NOT attempt to make the ordering/payment process fully offline.

Payments obviously require internet.

---

# 51. QR CODE

The business needs a QR code that points to:

```text
https://<domain>/order
```

Do not build a complicated QR-management system.

Simply document that the business can print this URL as a QR code.

Optionally provide a tiny admin setting showing the ordering URL.

---

# 52. PERFORMANCE REQUIREMENTS

This is a small business application.

Optimize for:

* fast mobile load
* small bundle
* simple queries
* database indexes
* pagination
* no unnecessary API requests

Do NOT prematurely optimize for millions of users.

Expected scale is initially something like:

```text
100–500 customers
10–100 orders/day
1–10 delivery staff
```

The architecture should still be clean enough to scale later.

---

# 53. BUSINESS LOGIC EXAMPLES

## Example 1 — Existing customer refill

Customer:

```text
John
phone: 9876543210
```

Previous:

```text
5 cans
address = Pattom
```

Customer enters phone.

System finds John.

Customer selects:

```text
5 cans
```

Server calculates:

```text
5 × ₹50 = ₹250
```

Customer pays.

Order becomes:

```text
PAID
```

Owner sees:

```text
WC-20260927-0001
John
5 cans
₹250
PAID
```

---

## Example 2 — New customer

Phone not found.

Customer enters:

```text
Name: Arun
Phone: 9999999999
Address: Kazhakkoottam
Pincode: 695582
Quantity: 3
```

Server:

1. creates customer
2. creates address
3. creates order
4. calculates price
5. creates payment
6. verifies payment
7. marks order PAID

---

## Example 3 — Delivery

Order:

```text
5 cans
```

Driver delivers:

```text
5 filled cans
```

Customer gives:

```text
3 empty cans
```

Can balance changes:

```text
old = 4
+5 delivered
-3 returned
----------------
new = 6
```

Ledger:

```text
DELIVERED +5
RETURNED  -3
```

---

# 54. DASHBOARD SEARCH/FILTER

Owner should be able to filter:

```text
Today
Tomorrow
Date range

Pending
Paid
Assigned
Out for Delivery
Delivered
Cancelled

Assigned staff

Search:
customer name
phone
order number
```

Do not build advanced analytics yet.

---

# 55. CUSTOMER HISTORY

Owner customer detail page should show:

```text
Customer
John George
9876543210

Can Balance
6 cans

Default Address
Pattom, Trivandrum

Order History

WC-001
5 cans
Delivered
₹250

WC-002
3 cans
Delivered
₹150
```

This will help the owner manage repeat customers.

---

# 56. OWNER SETTINGS

Basic settings page:

```text
Business Name
Business Phone
Business Address

Water Can Price
Delivery Charge
```

Optional:

```text
UPI/payment configuration
business WhatsApp number
```

Do not build a complicated CMS.

---

# 57. FUTURE FEATURES — DO NOT BUILD NOW

Keep architecture extensible for:

* customer OTP login
* SMS notifications
* WhatsApp Business API
* automated WhatsApp order notifications
* delivery zones
* multiple water-can sizes
* subscriptions
* monthly plans
* credit customers
* outstanding balance
* route optimization
* driver GPS tracking
* delivery proof/photo
* invoices
* GST invoices
* multiple vendors
* analytics
* customer loyalty
* referral system

These are future features only.

Do NOT implement them in the MVP unless required by the core flow.

---

# 58. UI DESIGN DIRECTION

The UI should feel:

```text
Simple
Clean
Fast
Trustworthy
Local-business friendly
Mobile-first
```

Avoid:

* excessive animations
* complicated dashboards
* unnecessary gradients
* huge navigation menus
* excessive charts
* enterprise-style complexity

The customer should be able to place a refill order in roughly a minute once their address is saved.

Use clear CTAs such as:

```text
Order Water
Refill Now
Continue
Pay ₹250
```

---

# 59. IMPORTANT DATA PRIVACY RULE

The public customer lookup endpoint must not expose arbitrary customer data just because someone knows another person's phone number.

At minimum:

* return only the data required for the refill experience
* do not return payment credentials
* do not expose staff information
* do not expose internal notes
* do not expose unnecessary order history

Design the endpoint so that customer-data exposure is limited.

Customer OTP verification can later strengthen this.

---

# 60. IMPLEMENTATION PHASES

Build the project in this exact order.

## PHASE 1 — Project Foundation

Create:

```text
repo structure
frontend
backend
Docker Compose
PostgreSQL
environment configuration
README
```

Verify:

```text
frontend starts
backend starts
database connects
```

---

## PHASE 2 — Database

Implement:

```text
users
customers
customer_addresses
products
orders
order_assignments
order_can_summary
customer_can_balances
can_transactions
payments
business_settings
```

Create Alembic migrations.

Create seed data.

Test database connectivity.

---

## PHASE 3 — Backend Foundation

Implement:

```text
FastAPI app
config
database session
SQLAlchemy models
Pydantic schemas
error handling
logging
CORS
```

---

## PHASE 4 — Authentication

Implement:

```text
login
JWT
current user
RBAC
owner
staff
```

Test protected routes.

---

## PHASE 5 — Customer APIs

Implement:

```text
customer lookup
customer creation
customer addresses
default address
customer history
```

---

## PHASE 6 — Order APIs

Implement:

```text
create order
calculate pricing
order retrieval
customer refill
order history
status transitions
```

---

## PHASE 7 — Can Tracking

Implement:

```text
can balance
can ledger
delivered
returned
adjustments
```

Make sure everything is transactional.

---

## PHASE 8 — Razorpay

Implement:

```text
create payment
verify payment
webhook
idempotency
payment states
```

Use Razorpay test mode during development.

---

## PHASE 9 — Customer Frontend

Build:

```text
QR landing page
phone lookup
existing customer refill
new customer flow
address
quantity
order summary
Razorpay checkout
success page
```

Prioritize mobile UX.

---

## PHASE 10 — Owner Dashboard

Build:

```text
login
dashboard
orders
order details
filters
assignment
staff management
customer details
can balances
settings
WhatsApp sharing
```

---

## PHASE 11 — Staff Dashboard

Build:

```text
login
assigned orders
available orders
claim order
order details
```

Implement strict permissions.

---

## PHASE 12 — Testing

Run:

```text
backend unit tests
API integration tests
frontend tests
lint
type checks
```

Fix issues.

---

## PHASE 13 — Production Readiness

Add:

```text
Docker configuration
production environment variables
database migration instructions
deployment README
health endpoint
basic error monitoring/logging
```

---

# 61. HEALTH ENDPOINT

Implement:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

Optionally verify database connectivity separately.

---

# 62. DOCUMENTATION

Create a clear README containing:

```text
Project overview
Architecture
Tech stack
Local setup
Environment variables
Database setup
Migrations
Seed data
Running tests
Running frontend
Running backend
Razorpay setup
Production deployment
```

Also create:

```text
docs/API.md
docs/ARCHITECTURE.md
```

API documentation should explain important endpoints.

FastAPI's Swagger/OpenAPI documentation should also work automatically.

---

# 63. API DOCUMENTATION

All APIs should have:

* request schemas
* response schemas
* validation
* meaningful descriptions
* examples where useful

FastAPI Swagger should be usable for testing.

---

# 64. ACCEPTANCE CRITERIA

The MVP is considered successful only when this complete flow works:

## Customer

```text
Scan QR
↓
Open mobile site
↓
Enter phone
↓
Existing customer recognized
↓
Previous/default address displayed
↓
Select 5 cans
↓
See correct total
↓
Open Razorpay
↓
Complete test payment
↓
Backend verifies payment
↓
Order becomes PAID
↓
Customer sees confirmation
```

## Owner

```text
Login
↓
See new paid order
↓
Open order
↓
See customer details
↓
See address
↓
Assign staff
↓
Click WhatsApp
↓
WhatsApp opens with prefilled order message
↓
Mark order out for delivery
↓
Mark delivered
↓
Enter empty cans returned
↓
Customer can balance updates correctly
```

## Staff

```text
Login
↓
See assigned orders
↓
See available orders
↓
Claim an available order
↓
Order becomes assigned to that staff member
```

---

# 65. DEVELOPMENT STYLE

When implementing code:

* use type hints
* keep functions small
* use meaningful names
* avoid giant files
* avoid duplicated business logic
* keep business logic in services
* validate all input
* write tests alongside important backend features
* use transactions where necessary
* use async where appropriate, but do not introduce complexity simply for the sake of async
* keep frontend components reusable but not excessively abstract

---

# 66. IMPORTANT: DO NOT OVERTHINK

This is a real small-business MVP.

Do not turn it into:

```text
Uber for water
Swiggy for water
microservices architecture
event-driven architecture
Kubernetes platform
complex analytics platform
multi-tenant SaaS
```

The correct architecture is a **simple monorepo with one frontend, one FastAPI backend, and one PostgreSQL database**.

The first objective is:

```text
Customer orders water
        ↓
Payment succeeds
        ↓
Owner sees order
        ↓
Staff gets delivery
        ↓
Delivery completed
        ↓
Can inventory updated
```

Everything else is secondary.

---

# 67. HOW YOU SHOULD WORK IN ANTIGRAVITY

Do not immediately generate the entire application.

Work in phases.

For each phase:

1. Inspect the current repository.
2. Create/update only the files required for that phase.
3. Implement the feature.
4. Run the application/tests.
5. Fix errors you introduced.
6. Verify the result.
7. Give me a concise summary:

   * files created/changed
   * functionality implemented
   * tests/checks performed
   * anything that still needs attention
8. Move to the next phase when the current phase is stable.

When there is a small ambiguity, choose the simplest reasonable implementation and document the assumption instead of stopping development.

Do not repeatedly ask me questions for decisions already specified in this prompt.

---

# 68. FIRST ACTION

Start with **PHASE 1 — Project Foundation**.

Before writing large amounts of application code, create the initial project structure and architecture.

First provide a concise implementation checklist, then create the project foundation.

Do NOT implement all phases at once.

At the end of Phase 1, make sure:

```text
Frontend runs
Backend runs
PostgreSQL runs
Backend connects to PostgreSQL
Environment configuration works
README exists
Repository structure is clean
```

Then proceed phase-by-phase.

# FINAL PRODUCT GOAL

The final application should feel like a simple digital ordering system for a local water-can business:

### CUSTOMER

```text
QR
↓
Phone
↓
Quick Refill
↓
Address
↓
Payment
↓
Done
```

### OWNER

```text
Dashboard
↓
Paid Orders
↓
Assign
↓
WhatsApp
↓
Delivery
↓
Can Tracking
```

### STAFF

```text
Login
↓
My Orders
↓
Claim/Accept
↓
Deliver
```

Build exactly this core system first.
