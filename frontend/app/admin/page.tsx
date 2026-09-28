"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, Dashboard, Order } from "./api";

function Stat({ label, value, accent = "text-slate-900" }: { label: string; value: string | number; accent?: string }) {
  return <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200"><p className="text-sm text-slate-500">{label}</p><p className={`mt-2 text-2xl font-bold ${accent}`}>{value}</p></div>;
}

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      apiFetch<Dashboard>("/admin/dashboard"),
      apiFetch<{ items: Order[] }>("/admin/orders?page=1&page_size=5"),
    ])
      .then(([summary, orderList]) => { setDashboard(summary); setOrders(orderList.items); })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Unable to load dashboard"));
  }, []);

  if (error) return <p className="rounded-2xl bg-red-50 p-4 text-red-700">{error}</p>;
  if (!dashboard) return <p className="text-slate-600">Loading dashboard...</p>;

  return (
    <div className="space-y-6">
      <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Overview</p><h1 className="mt-1 text-3xl font-bold">Today&apos;s operations</h1></div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Today&apos;s orders" value={dashboard.today.orders} />
        <Stat label="Today&apos;s revenue" value={`₹${Number(dashboard.today.revenue).toFixed(2)}`} accent="text-emerald-700" />
        <Stat label="Pending orders" value={dashboard.pending_orders} accent="text-amber-700" />
        <Stat label="Out for delivery" value={dashboard.out_for_delivery} accent="text-sky-700" />
        <Stat label="Paid orders" value={dashboard.today.paid_orders} />
        <Stat label="Delivered today" value={dashboard.today.delivered_orders} accent="text-emerald-700" />
        <Stat label="Unassigned" value={dashboard.unassigned_orders} accent="text-amber-700" />
        <Stat label="Cans with customers" value={dashboard.total_cans_with_customers} />
      </div>
      <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-bold">Recent orders</h2><Link className="text-sm font-semibold text-sky-700" href="/admin/orders">View all</Link></div>
        <div className="space-y-3">
          {orders.map((order) => <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-slate-50 p-4" key={order.id}><div><p className="font-bold">{order.order_number}</p><p className="text-sm text-slate-600">{order.customer_name} · {order.quantity} cans</p></div><div className="text-right"><p className="font-semibold">₹{Number(order.total_amount).toFixed(2)}</p><p className="text-xs text-slate-500">{order.order_status}</p></div></div>)}
        </div>
      </section>
    </div>
  );
}
