"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const RAZORPAY_KEY = process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID;

type Stage = "phone" | "existing" | "new" | "summary" | "success";

type Address = {
  id: string;
  label: string;
  address_line_1: string;
  address_line_2?: string | null;
  city: string;
  district?: string | null;
  state: string;
  pincode: string;
  is_default: boolean;
};

type Customer = {
  id: string;
  name: string;
  phone: string;
  default_address: Address | null;
  addresses: Address[];
  last_order_quantity?: number | null;
};

type Product = {
  price_per_unit: number;
  unit_name: string;
};

type Order = {
  id: string;
  order_number: string;
  total_amount: number;
};

type RazorpayCallback = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => {
      open: () => void;
      on: (event: string, handler: (response: { error?: { description?: string } }) => void) => void;
    };
  }
}

function addressLabel(address: Address | null) {
  if (!address) return "No saved address";
  return [
    address.address_line_1,
    address.address_line_2,
    address.city,
    address.pincode,
  ]
    .filter(Boolean)
    .join(", ");
}

async function readResponse(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ?? "Something went wrong. Please try again.");
  }
  return body;
}

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("phone");
  const [businessSlug, setBusinessSlug] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(5);
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    name: "",
    address_line_1: "",
    city: "",
    pincode: "",
  });

  useEffect(() => {
    const slug = new URLSearchParams(window.location.search).get("seller");
    setBusinessSlug(slug);
    const query = slug ? `?business_slug=${encodeURIComponent(slug)}` : "";
    fetch(`${API_BASE}/products${query}`)
      .then(readResponse)
      .then((products: Product[]) => setProduct(products[0] ?? null))
      .catch(() => setError("Pricing is temporarily unavailable. Please try again."));
  }, []);

  function sellerQuery() {
    return businessSlug ? `?business_slug=${encodeURIComponent(businessSlug)}` : "";
  }

  const total = useMemo(
    () => (product ? product.price_per_unit * quantity : 0),
    [product, quantity],
  );

  function resetError() {
    setError("");
  }

  async function lookupCustomer(event: FormEvent) {
    event.preventDefault();
    resetError();
    const normalizedPhone = phone.replace(/\D/g, "").slice(-10);
    if (!/^[6-9]\d{9}$/.test(normalizedPhone)) {
      setError("Enter a valid 10-digit Indian mobile number.");
      return;
    }

    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/customers/by-phone/${normalizedPhone}${sellerQuery()}`);
      if (response.status === 404) {
        setPhone(normalizedPhone);
        setStage("new");
        return;
      }
      const result = (await readResponse(response)) as Customer;
      setCustomer(result);
      setIsNewCustomer(false);
      setSelectedAddress(result.default_address);
      setQuantity(result.last_order_quantity || 5);
      setStage("existing");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to find that number.");
    } finally {
      setBusy(false);
    }
  }

  async function createNewCustomer(event: FormEvent) {
    event.preventDefault();
    resetError();
    if (!newCustomer.name || !newCustomer.address_line_1 || !newCustomer.city) {
      setError("Complete your name and address before continuing.");
      return;
    }
    if (!/^\d{6}$/.test(newCustomer.pincode)) {
      setError("Enter a valid 6-digit pincode.");
      return;
    }

    setBusy(true);
    try {
      const created = (await readResponse(
        await fetch(`${API_BASE}/customers${sellerQuery()}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: newCustomer.name, phone }),
        }),
      )) as Customer;
      const address = (await readResponse(
        await fetch(`${API_BASE}/customers/${created.id}/addresses`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            label: "Home",
            address_line_1: newCustomer.address_line_1,
            city: newCustomer.city,
            state: "Kerala",
            pincode: newCustomer.pincode,
            is_default: true,
          }),
        }),
      )) as Address;
      setCustomer({ ...created, default_address: address, addresses: [address] });
      setIsNewCustomer(true);
      setSelectedAddress(address);
      setStage("existing");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save your details.");
    } finally {
      setBusy(false);
    }
  }

  async function createOrder() {
    if (!customer || !selectedAddress) return;
    resetError();
    setBusy(true);
    try {
      const created = (await readResponse(
        await fetch(`${API_BASE}/orders`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_id: customer.id,
            address_id: selectedAddress.id,
            quantity,
          }),
        }),
      )) as Order;
      setOrder(created);
      setStage("summary");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create the order.");
    } finally {
      setBusy(false);
    }
  }

  async function pay() {
    if (!order) return;
    resetError();
    if (!RAZORPAY_KEY) {
      setError("Razorpay is not configured for this environment yet.");
      return;
    }

    setBusy(true);
    try {
      const paymentOrder = await readResponse(
        await fetch(`${API_BASE}/payments/create-order`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order_id: order.id }),
        }),
      );
      await new Promise<void>((resolve, reject) => {
        if (window.Razorpay) {
          resolve();
          return;
        }
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Unable to load payment checkout."));
        document.body.appendChild(script);
      });

      if (!window.Razorpay) throw new Error("Payment checkout is unavailable.");
      const Checkout = window.Razorpay;
      const checkout = new Checkout({
        key: RAZORPAY_KEY,
        amount: paymentOrder.amount,
        currency: paymentOrder.currency,
        name: "Water Can Delivery",
        description: `${quantity} water cans`,
        order_id: paymentOrder.razorpay_order_id,
        handler: async (callback: RazorpayCallback) => {
          try {
            await readResponse(
              await fetch(`${API_BASE}/payments/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ order_id: order.id, ...callback }),
              }),
            );
            setStage("success");
          } catch (requestError) {
            setError(requestError instanceof Error ? requestError.message : "Payment verification failed.");
          } finally {
            setBusy(false);
          }
        },
        modal: {
          ondismiss: () => setBusy(false),
          confirm_close: true,
        },
        prefill: { name: customer?.name, contact: customer?.phone },
        theme: { color: "#0284c7" },
      });
      checkout.on("payment.failed", (response) => {
        setBusy(false);
        setError(response.error?.description ?? "Razorpay payment failed. Please try again.");
      });
      setBusy(false);
      checkout.open();
    } catch (requestError) {
      setBusy(false);
      setError(requestError instanceof Error ? requestError.message : "Unable to start payment.");
    }
  }

  return (
    <main className="min-h-screen bg-sky-50 px-5 py-8 text-slate-900">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col rounded-3xl bg-white p-6 shadow-sm ring-1 ring-sky-100">
        <div className="mb-8">
          <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-water-600 text-2xl text-white">
            💧
          </div>
          {stage === "phone" && (
            <>
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-water-700">Water Can Delivery</p>
              <h1 className="text-4xl font-bold leading-tight">Fresh water delivered to your door.</h1>
              <p className="mt-4 text-base leading-7 text-slate-600">Enter your phone number to start a new order or quickly refill your usual cans.</p>
            </>
          )}
          {stage === "existing" && customer && (
            <>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-water-700">{isNewCustomer ? "Welcome" : "Welcome back"}</p>
              <h1 className="mt-2 text-3xl font-bold">Hi, {customer.name} 👋</h1>
              <div className="mt-6 rounded-2xl bg-sky-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Deliver to</p>
                <p className="mt-2 text-sm leading-6">{addressLabel(selectedAddress)}</p>
              </div>
            </>
          )}
          {stage === "new" && (
            <>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-water-700">New customer</p>
              <h1 className="mt-2 text-3xl font-bold">Where should we deliver?</h1>
            </>
          )}
          {stage === "summary" && order && (
            <>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-water-700">Order summary</p>
              <h1 className="mt-2 text-3xl font-bold">Ready to pay</h1>
            </>
          )}
          {stage === "success" && order && (
            <>
              <p className="text-4xl">✓</p>
              <p className="mt-5 text-sm font-semibold uppercase tracking-[0.2em] text-water-700">Confirmed</p>
              <h1 className="mt-2 text-3xl font-bold">Your order is on its way.</h1>
            </>
          )}
        </div>

        {stage === "phone" && (
          <form className="mt-auto space-y-4" onSubmit={lookupCustomer}>
            <label className="block text-sm font-semibold" htmlFor="phone">Phone number</label>
            <input className="h-14 w-full rounded-2xl border border-slate-200 px-4 text-lg outline-none transition focus:border-water-600 focus:ring-4 focus:ring-sky-100" id="phone" inputMode="numeric" onChange={(event) => setPhone(event.target.value)} placeholder="9876543210" type="tel" value={phone} />
            <button className="h-14 w-full rounded-2xl bg-water-600 px-5 text-base font-bold text-white transition hover:bg-water-700 disabled:opacity-50" disabled={busy} type="submit">{busy ? "Checking..." : "Continue"}</button>
            <p className="text-center text-xs text-slate-500">No account or password required.</p>
          </form>
        )}

        {(stage === "existing" || stage === "summary") && (
          <div className="mt-auto space-y-5">
            {stage === "existing" && (
              <>
                <div>
                  <p className="mb-3 text-sm font-semibold">How many cans today?</p>
                  <div className="flex items-center justify-between rounded-2xl border border-slate-200 p-2">
                    <button className="h-12 w-12 rounded-xl bg-sky-50 text-2xl text-water-700" onClick={() => setQuantity(Math.max(1, quantity - 1))} type="button">−</button>
                    <span className="text-2xl font-bold">{quantity}</span>
                    <button className="h-12 w-12 rounded-xl bg-sky-50 text-2xl text-water-700" onClick={() => setQuantity(Math.min(50, quantity + 1))} type="button">+</button>
                  </div>
                </div>
                <div className="flex items-center justify-between border-t border-slate-100 pt-4"><span className="text-slate-600">Total</span><span className="text-2xl font-bold">₹{total.toFixed(2)}</span></div>
                <button className="h-14 w-full rounded-2xl bg-water-600 px-5 text-base font-bold text-white disabled:opacity-50" disabled={busy || !selectedAddress || !product} onClick={createOrder} type="button">{busy ? "Creating order..." : "Review order"}</button>
              </>
            )}
            {stage === "summary" && order && (
              <>
                <div className="space-y-3 rounded-2xl bg-sky-50 p-4 text-sm">
                  <div className="flex justify-between"><span>Water cans</span><span>{quantity} × ₹{product?.price_per_unit.toFixed(2)}</span></div>
                  <div className="flex justify-between border-t border-sky-100 pt-3 font-bold"><span>Total</span><span>₹{order.total_amount.toFixed(2)}</span></div>
                  <p className="border-t border-sky-100 pt-3 text-slate-600">{addressLabel(selectedAddress)}</p>
                </div>
                <button className="h-14 w-full rounded-2xl bg-water-600 px-5 text-base font-bold text-white disabled:opacity-50" disabled={busy} onClick={pay} type="button">{busy ? "Opening payment..." : `Pay ₹${order.total_amount.toFixed(2)}`}</button>
              </>
            )}
          </div>
        )}

        {stage === "new" && (
          <form className="mt-auto space-y-3" onSubmit={createNewCustomer}>
            {(["name", "address_line_1", "city", "pincode"] as const).map((field) => (
              <input className="h-12 w-full rounded-2xl border border-slate-200 px-4 outline-none focus:border-water-600 focus:ring-4 focus:ring-sky-100" key={field} inputMode={field === "pincode" ? "numeric" : "text"} onChange={(event) => setNewCustomer({ ...newCustomer, [field]: event.target.value })} placeholder={{ name: "Your name", address_line_1: "Address", city: "City", pincode: "Pincode" }[field]} type="text" value={newCustomer[field]} />
            ))}
            <button className="mt-2 h-14 w-full rounded-2xl bg-water-600 px-5 text-base font-bold text-white disabled:opacity-50" disabled={busy} type="submit">{busy ? "Saving..." : "Save and continue"}</button>
          </form>
        )}

        {stage === "success" && order && (
          <div className="mt-auto rounded-2xl bg-sky-50 p-5 text-center">
            <p className="text-sm text-slate-600">Order number</p>
            <p className="mt-1 text-2xl font-bold text-water-700">{order.order_number}</p>
            <p className="mt-4 text-sm text-slate-600">{quantity} water cans · Payment received</p>
          </div>
        )}

        {error && <p className="mt-5 rounded-2xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>
    </main>
  );
}
