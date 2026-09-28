"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, API_BASE } from "../../admin/api";

type Seller = {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  owner_name?: string | null;
  owner_email?: string | null;
  created_at: string;
};

const emptyForm = {
  business_name: "",
  slug: "",
  business_phone: "",
  business_address: "",
  business_whatsapp: "",
  owner_name: "",
  owner_email: "",
  owner_phone: "",
  owner_password: "",
};

export default function SellersPage() {
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try { setSellers(await apiFetch<Seller[]>("/platform/sellers")); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load sellers"); }
  }

  useEffect(() => { load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiFetch("/platform/sellers", { method: "POST", body: JSON.stringify({ ...form, currency: "INR", default_delivery_charge: 0 }) });
      setForm(emptyForm);
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create seller");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(seller: Seller) {
    setError("");
    try {
      await apiFetch(`/platform/sellers/${seller.id}/${seller.is_active ? "deactivate" : "activate"}`, { method: "POST" });
      await load();
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to update seller"); }
  }

  return (
    <div className="space-y-6">
      <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Marketplace</p><h1 className="mt-1 text-3xl font-bold">Sellers</h1><p className="mt-2 text-slate-600">Each seller receives an owner account and a public ordering URL.</p></div>
      <form className="grid gap-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:grid-cols-2" onSubmit={create}>
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, business_name: event.target.value })} placeholder="Business name" required value={form.business_name} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, slug: event.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-") })} placeholder="seller-slug" required value={form.slug} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, business_phone: event.target.value })} placeholder="Business phone" required value={form.business_phone} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, business_whatsapp: event.target.value })} placeholder="WhatsApp number" value={form.business_whatsapp} />
        <input className="h-11 rounded-xl border border-slate-200 px-3 sm:col-span-2" onChange={(event) => setForm({ ...form, business_address: event.target.value })} placeholder="Business address" value={form.business_address} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, owner_name: event.target.value })} placeholder="Owner name" required value={form.owner_name} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, owner_phone: event.target.value })} placeholder="Owner phone" value={form.owner_phone} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, owner_email: event.target.value })} placeholder="Owner email" required type="email" value={form.owner_email} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" minLength={8} onChange={(event) => setForm({ ...form, owner_password: event.target.value })} placeholder="Temporary owner password" required type="password" value={form.owner_password} />
        <button className="rounded-xl bg-sky-600 px-4 py-3 font-bold text-white disabled:opacity-50 sm:col-span-2" disabled={busy} type="submit">{busy ? "Creating..." : "Create seller"}</button>
      </form>
      {error && <p className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      <div className="space-y-3">{sellers.map((seller) => <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200" key={seller.id}><div><p className="font-bold">{seller.name}</p><p className="text-sm text-slate-600">/{seller.slug} · {seller.owner_email ?? "No owner"}</p><p className="mt-1 text-xs text-slate-500">Public URL: {typeof window !== "undefined" ? `${window.location.origin}/?seller=${seller.slug}` : `/?seller=${seller.slug}`}</p></div><button className={`rounded-xl px-3 py-2 text-sm font-semibold ${seller.is_active ? "border border-red-200 text-red-700" : "bg-emerald-600 text-white"}`} onClick={() => toggle(seller)} type="button">{seller.is_active ? "Deactivate" : "Activate"}</button></div>)}</div>
      <p className="text-xs text-slate-500">API base: {API_BASE}</p>
    </div>
  );
}
