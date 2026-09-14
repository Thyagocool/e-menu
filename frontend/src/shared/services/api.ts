const BASE = import.meta.env.VITE_API_URL ?? '/api'

export interface Restaurant {
  id: number
  name: string
  slug: string
  phone: string | null
  whatsapp_phone: string | null
  address: string | null
  opening_hours: string | null
  delivery_fee: string
  status: 'active' | 'inactive'
}

export interface Category {
  id: number
  restaurant_id: number
  name: string
  description: string | null
  sort_order: number
  status: 'active' | 'inactive'
}

export interface Variant {
  id: number
  name: string
  price: string
  status: string
}

export interface Addon {
  id: number
  restaurant_id: number
  name: string
  price: string
  status: string
}

export interface Product {
  id: number
  restaurant_id: number
  category_id: number | null
  name: string
  description: string | null
  image_url: string | null
  base_price: string
  status: 'active' | 'inactive'
}

export interface ProductDetail extends Product {
  variants: Variant[]
  addons: Addon[]
}

// --- Cardápio público ---

export interface PublicRestaurant {
  id: number
  slug: string
  name: string
  phone: string | null
  whatsapp_phone: string | null
  address: string | null
  opening_hours: string | null
  delivery_fee: string
}

export interface PublicVariant {
  id: number
  name: string
  price: string
}

export interface PublicAddon {
  id: number
  name: string
  price: string
}

export interface PublicProduct {
  id: number
  name: string
  description: string | null
  image_url: string | null
  base_price: string
  variants: PublicVariant[]
  addons: PublicAddon[]
}

export interface PublicCategory {
  id: number
  name: string
  products: PublicProduct[]
}

export interface PublicMenu {
  restaurant: PublicRestaurant
  categories: PublicCategory[]
  uncategorized_products: PublicProduct[]
}

// --- Pedidos ---

export type OrderStatus =
  | 'RECEIVED'
  | 'CONFIRMED'
  | 'PREPARING'
  | 'READY'
  | 'DELIVERING'
  | 'COMPLETED'
  | 'CANCELLED'

export const ORDER_STATUSES: OrderStatus[] = [
  'RECEIVED',
  'CONFIRMED',
  'PREPARING',
  'READY',
  'DELIVERING',
  'COMPLETED',
  'CANCELLED',
]

export interface OrderItem {
  product_name: string
  variant_name: string | null
  unit_price: string
  quantity: number
  line_total: string
  addons: { name: string; price: string }[]
}

export interface Order {
  id: number
  status: OrderStatus
  delivery_type: string
  address: string | null
  payment_method: string
  delivery_fee: string
  subtotal: string
  total: string
  customer_name: string | null
  created_at: string | null
  items: OrderItem[]
}

// --- Dashboard (US-036) ---

export interface TopProduct {
  name: string
  quantity: number
  revenue: string
}

export interface Dashboard {
  orders_today: number
  revenue_today: string
  pending_orders: number
  top_products: TopProduct[]
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Erro ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  getPublicMenu: (slug: string) => request<PublicMenu>(`/public/restaurants/${slug}/menu`),
  listOrders: (restaurantId: number, status?: string) =>
    request<Order[]>(
      `/restaurants/${restaurantId}/orders${status ? `?status=${status}` : ''}`,
    ),
  updateOrderStatus: (id: number, status: OrderStatus) =>
    request<Order>(`/orders/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    }),
  getDashboard: (restaurantId: number) =>
    request<Dashboard>(`/restaurants/${restaurantId}/dashboard`),
  getQrUrl: (restaurantId: number) => `${BASE}/restaurants/${restaurantId}/qr`,
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body ?? {}) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
  upload: async (file: File): Promise<{ url: string }> => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? 'Falha no upload')
    }
    return res.json()
  },
}