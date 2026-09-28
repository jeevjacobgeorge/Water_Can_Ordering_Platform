"use client";

import { useEffect, useState } from "react";
import { apiFetch, formatAddress, openWhatsApp, Order, PaginatedOrders, Staff } from "../api";

const statuses = ["", "PENDING_PAYMENT", "PAID", "CONFIRMED", "ASSIGNED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const query = new URLSearchParams({ page: "1", page_size: "50" });
      if (statusFilter) query.set("status", statusFilter);
      if (search) query.set("search", search);
      const [result, staffResult] = await Promise.all([
        apiFetch<PaginatedOrders>(`/admin/orders?${query.toString()}`),
        apiFetch<Staff[]>("/admin/staff"),
      ]);
      setOrders(result.items);
      setStaff(staffResult);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load orders");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [statusFilter]);

  async function action(order: Order, endpoint: string, body?: unknown) {
    setError("");
    try {
      await apiFetch(`/admin/orders/${order.id}/${endpoint}`, { method: "POST", body: body ? JSON.stringify(body) : undefined });
      await load();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Action failed");
    }
  }

  function deliver(order: Order) {
    const returned = window.prompt("Empty cans returned", "0");
    if (returned === null) return;
    const emptyCans = Number(returned);
    if (!Number.isInteger(emptyCans) || emptyCans < 0) {
      setError("Enter a whole number of returned cans.");
      return;
    }
    action(order, "delivered", { cans_delivered: order.quantity, empty_cans_returned: emptyCans });
  }

  return (
    <div className="space-y-6">
      <div><p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-700">Operations</p><h1 className="mt-1 text-3xl font-bold">Orders</h1></div>
      <div className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200 sm:flex-row">
        <input className="h-11 flex-1 rounded-xl border border-slate-200 px-3 outline-none focus:border-sky-600" onChange={(event) => setSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") load(); }} placeholder="Search order, name, or phone" value={search} />
        <select className="h-11 rounded-xl border border-slate-200 px-3" onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>{statuses.map((value) => <option key={value} value={value}>{value || "All statuses"}</option>)}</select>
        <button className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white" onClick={load} type="button">Search</button>
      </div>
      {error && <p className="rounded-2xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {loading ? <p className="text-slate-600">Loading orders...</p> : <div className="space-y-4">{orders.map((order) => <OrderCard key={order.id} order={order} staff={staff} onAction={action} onDeliver={deliver} />)}{orders.length === 0 && <p className="rounded-2xl bg-white p-6 text-slate-600">No orders found.</p>}</div>}
    </div>
  );
}

function OrderCard({ order, staff, onAction, onDeliver }: { order: Order; staff: Staff[]; onAction: (order: Order, endpoint: string, body?: unknown) => void; onDeliver: (order: Order) => void }) {
  const [selectedStaff, setSelectedStaff] = useState(order.assigned_staff_id ?? "");
  const assignedStaff = staff.find((member) => member.id === order.assigned_staff_id);
  return (
    <article className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="font-bold text-sky-700">{order.order_number}</p><h2 className="mt-1 text-lg font-bold">{order.customer_name}</h2><p className="text-sm text-slate-600">{order.customer_phone}</p></div>
        <div className="text-right"><p className="text-lg font-bold">₹{Number(order.total_amount).toFixed(2)}</p><p className="text-xs font-semibold text-slate-500">{order.payment_status} · {order.order_status}</p></div>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2"><p><strong className="text-slate-900">Quantity:</strong> {order.quantity} cans</p><p><strong className="text-slate-900">Address:</strong> {formatAddress(order)}</p>{order.assigned_staff_name && <p><strong className="text-slate-900">Assigned:</strong> {order.assigned_staff_name}</p>}{order.customer_notes && <p><strong className="text-slate-900">Notes:</strong> {order.customer_notes}</p>}</div>
      <div className="mt-5 flex flex-wrap gap-2">
        {order.order_status === "PAID" && <button className="rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => onAction(order, "confirm")} type="button">Confirm</button>}
        {(order.order_status === "CONFIRMED" || order.order_status === "ASSIGNED") && <><select className="rounded-xl border border-slate-200 px-3 text-sm" onChange={(event) => setSelectedStaff(event.target.value)} value={selectedStaff}><option value="">Select staff</option>{staff.filter((member) => member.is_active).map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}</select><button className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white" disabled={!selectedStaff} onClick={() => onAction(order, "assign", { staff_id: selectedStaff })} type="button">Assign</button></>}
        {order.order_status === "ASSIGNED" && <button className="rounded-xl bg-indigo-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => onAction(order, "out-for-delivery")} type="button">Out for delivery</button>}
        {order.order_status === "OUT_FOR_DELIVERY" && <button className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => onDeliver(order)} type="button">Mark delivered</button>}
        {!["DELIVERED", "CANCELLED"].includes(order.order_status) && <button className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold" onClick={() => openWhatsApp(order, assignedStaff?.phone)} type="button">{assignedStaff?.phone ? "Send to staff" : "WhatsApp"}</button>}
        {!["DELIVERED", "CANCELLED"].includes(order.order_status) && <button className="rounded-xl border border-red-200 px-3 py-2 text-sm font-semibold text-red-700" onClick={() => onAction(order, "cancel")} type="button">Cancel</button>}
      </div>
    </article>
  );
}
