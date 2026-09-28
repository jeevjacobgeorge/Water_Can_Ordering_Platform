"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(pathname === "/platform/login");

  useEffect(() => {
    if (pathname === "/platform/login") {
      setReady(true);
      return;
    }
    if (!window.localStorage.getItem("watercan_token")) {
      router.replace("/platform/login");
      return;
    }
    setReady(true);
  }, [pathname, router]);

  if (pathname === "/platform/login") return children;
  if (!ready) return <div className="min-h-screen bg-slate-100 p-8 text-slate-600">Loading platform admin...</div>;

  function logout() {
    window.localStorage.removeItem("watercan_token");
    window.localStorage.removeItem("watercan_user");
    router.replace("/platform/login");
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link className="text-lg font-bold text-sky-700" href="/platform/sellers">Water Can Platform</Link>
          <button className="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100" onClick={logout} type="button">Log out</button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-5 py-6">{children}</main>
    </div>
  );
}
