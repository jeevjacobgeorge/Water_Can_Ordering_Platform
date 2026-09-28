"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiFetch, Staff } from "../api";

export default function StaffPage() {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");

  async function load() {
    try { setStaff(await apiFetch<Staff[]>("/admin/staff")); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to load staff"); }
  }
  useEffect(() => { load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await apiFetch("/admin/staff", { method: "POST", body: JSON.stringify(form) });
      setForm({ name: "", email: "", phone: "", password: "" });
      await load();
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to create staff member"); }
  }

  async function toggle(member: Staff) {
    try { await apiFetch(`/admin/staff/${member.id}/${member.is_active ? "deactivate" : "activate"}`, { method: "POST" }); await load(); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Unable to update staff member"); }
  }

  return (
    <div className="space-y-6">
      <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Team</p><h1 className="mt-1 text-3xl font-bold">Delivery staff</h1></div>
      <form className="grid gap-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:grid-cols-2" onSubmit={create}>
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Name" required value={form.name} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="Email" required type="email" value={form.email} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setForm({ ...form, phone: event.target.value })} placeholder="Phone" value={form.phone} />
        <input className="h-11 rounded-xl border border-slate-200 px-3" minLength={6} onChange={(event) => setForm({ ...form, password: event.target.value })} placeholder="Temporary password" required type="password" value={form.password} />
        <button className="rounded-xl bg-sky-600 px-4 py-3 text-sm font-bold text-white sm:col-span-2" type="submit">Add staff member</button>
      </form>
      {error && <p className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      <div className="space-y-3">{staff.map((member) => <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200" key={member.id}><div><p className="font-bold">{member.name}</p><p className="text-sm text-slate-600">{member.email}{member.phone ? ` · ${member.phone}` : ""}</p></div><button className={`rounded-xl px-3 py-2 text-sm font-semibold ${member.is_active ? "border border-red-200 text-red-700" : "bg-emerald-600 text-white"}`} onClick={() => toggle(member)} type="button">{member.is_active ? "Deactivate" : "Activate"}</button></div>)}</div>
    </div>
  );
}
