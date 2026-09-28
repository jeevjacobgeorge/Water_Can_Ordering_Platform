"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "../../admin/api";

export default function PlatformLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("platform@watercan.dev");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail ?? "Login failed");
      if (body.user?.role !== "PLATFORM_ADMIN") throw new Error("Platform administrator access required");
      window.localStorage.setItem("watercan_token", body.access_token);
      window.localStorage.setItem("watercan_user", JSON.stringify(body.user));
      router.replace("/platform/sellers");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-sky-50 px-5">
      <form className="w-full max-w-md space-y-5 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-sky-100" onSubmit={submit}>
        <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Platform administration</p><h1 className="mt-2 text-3xl font-bold">Manage sellers</h1><p className="mt-2 text-sm text-slate-600">Create and manage independent water businesses.</p></div>
        <input className="h-12 w-full rounded-xl border border-slate-200 px-3" onChange={(event) => setUsername(event.target.value)} placeholder="Email" type="email" value={username} />
        <input className="h-12 w-full rounded-xl border border-slate-200 px-3" onChange={(event) => setPassword(event.target.value)} placeholder="Password" type="password" value={password} />
        {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <button className="h-12 w-full rounded-xl bg-sky-600 font-bold text-white disabled:opacity-50" disabled={busy} type="submit">{busy ? "Signing in..." : "Sign in"}</button>
      </form>
    </main>
  );
}
