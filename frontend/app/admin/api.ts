export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("watercan_token");
}

export async function apiFetch<T>(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem("watercan_token");
    }
    throw new Error(body.detail ?? "Request failed");
  }
  return body as T;
}

export type Dashboard = {
  today: {
    orders: number;
    paid_orders: number;
    delivered_orders: number;
    revenue: number;
    cans_ordered: number;
    cans_delivered: number;
    empty_cans_returned: number;
  };
  pending_orders: number;
  unassigned_orders: number;
  out_for_delivery: number;
  total_cans_with_customers: number;
};

export type Order = {
  id: string;
  order_number: string;
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  quantity: number;
  price_per_unit: number;
  subtotal: number;
  delivery_charge: number;
  discount: number;
  total_amount: number;
  payment_status: string;
  order_status: string;
  delivery_slot?: string | null;
  customer_notes?: string | null;
  address?: {
    address_line_1: string;
    address_line_2?: string | null;
    city: string;
    district?: string | null;
    state: string;
    pincode: string;
  } | null;
  assigned_staff_name?: string | null;
  assigned_staff_id?: string | null;
  cans_delivered?: number | null;
  empty_cans_returned?: number | null;
  created_at: string;
};

export type Staff = {
  id: string;
  name: string;
  phone?: string | null;
  email: string;
  role: string;
  is_active: boolean;
};

export type PaginatedOrders = {
  items: Order[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export function formatAddress(order: Order) {
  const address = order.address;
  if (!address) return "Address unavailable";
  return [
    address.address_line_1,
    address.address_line_2,
    address.city,
    address.district,
    address.state,
    address.pincode,
  ]
    .filter(Boolean)
    .join(", ");
}

function whatsappPhone(phone?: string | null) {
  if (!phone) return "";
  const digits = phone.replace(/\D/g, "");
  if (digits.length === 10) return `91${digits}`;
  if (digits.length === 12 && digits.startsWith("91")) return digits;
  return digits;
}

export function openWhatsApp(order: Order, recipientPhone?: string | null) {
  const message = [
    "Water Delivery Order",
    "",
    `Order: ${order.order_number}`,
    `Customer: ${order.customer_name}`,
    `Phone: ${order.customer_phone}`,
    "",
    `Address: ${formatAddress(order)}`,
    `Water Cans: ${order.quantity}`,
    `Payment: ${order.payment_status}`,
    `Delivery Status: ${order.order_status}`,
  ].join("\n");
  const phone = whatsappPhone(recipientPhone);
  const target = phone ? `https://wa.me/${phone}` : "https://wa.me/";
  window.open(`${target}?text=${encodeURIComponent(message)}`, "_blank");
}
