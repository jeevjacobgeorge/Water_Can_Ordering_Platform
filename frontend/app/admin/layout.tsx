"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(pathname === "/admin/login");

  useEffect(() => {
    if (pathname === "/admin/login") {
      setReady(true);
      return;
    }
    if (!window.localStorage.getItem("watercan_token")) {
      router.replace("/admin/login");
      return;
    }
    setReady(true);
  }, [pathname, router]);

  if (pathname === "/admin/login") return children;
  if (!ready) return <div className="min-h-screen bg-slate-100 p-8 text-slate-600">Loading admin...</div>;

  function logout() {
    window.localStorage.removeItem("watercan_token");
    window.localStorage.removeItem("watercan_user");
    router.replace("/admin/login");
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <Link className="text-lg font-bold text-sky-700" href="/admin">Water Can Admin</Link>
          <button className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100" onClick={logout}>Log out</button>
        </div>
      </header>
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-6 md:flex-row">
        <nav className="flex gap-2 overflow-x-auto md:w-48 md:flex-col">
          <Link className="rounded-xl bg-white px-4 py-3 text-sm font-semibold shadow-sm hover:bg-sky-50" href="/admin">Dashboard</Link>
          <Link className="rounded-xl bg-white px-4 py-3 text-sm font-semibold shadow-sm hover:bg-sky-50" href="/admin/orders">Orders</Link>
          <Link className="rounded-xl bg-white px-4 py-3 text-sm font-semibold shadow-sm hover:bg-sky-50" href="/admin/staff">Staff</Link>
        </nav>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
