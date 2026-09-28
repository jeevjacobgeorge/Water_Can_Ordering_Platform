"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "../api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("owner@watercan.dev");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function login(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Login failed");
      if (body.user.role !== "OWNER") throw new Error("This page is for owner accounts.");
      window.localStorage.setItem("watercan_token", body.access_token);
      window.localStorage.setItem("watercan_user", JSON.stringify(body.user));
      router.replace("/admin");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-sky-50 px-5 py-8">
      <form className="w-full max-w-md rounded-3xl bg-white p-7 shadow-sm ring-1 ring-sky-100" onSubmit={login}>
        <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-600 text-2xl text-white">💧</div>
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Owner portal</p>
        <h1 className="mt-2 text-3xl font-bold">Sign in to manage deliveries</h1>
        <div className="mt-7 space-y-4">
          <input className="h-13 w-full rounded-2xl border border-slate-200 px-4 outline-none focus:border-sky-600 focus:ring-4 focus:ring-sky-100" onChange={(event) => setUsername(event.target.value)} placeholder="Email" type="email" value={username} />
          <input className="h-13 w-full rounded-2xl border border-slate-200 px-4 outline-none focus:border-sky-600 focus:ring-4 focus:ring-sky-100" onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" value={password} />
          <button className="h-13 w-full rounded-2xl bg-sky-600 px-5 font-bold text-white hover:bg-sky-700 disabled:opacity-50" disabled={busy} type="submit">{busy ? "Signing in..." : "Sign in"}</button>
        </div>
        {error && <p className="mt-4 rounded-2xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </form>
    </main>
  );
}
