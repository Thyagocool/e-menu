const KEY = 'e-menu-restaurant-id'

export function getRestaurantId(): number | null {
  const raw = localStorage.getItem(KEY)
  return raw ? Number(raw) : null
}

export function setRestaurantId(id: number) {
  localStorage.setItem(KEY, String(id))
}