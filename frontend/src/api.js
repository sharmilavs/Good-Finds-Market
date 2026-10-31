async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin", // sends the HttpOnly session cookie
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong. Try again.");
  return data;
}

export const api = {
  products: () => request("/products"),
  me: () => request("/me"),
  register: (email, password) => request("/register", { method: "POST", body: { email, password } }),
  login: (email, password) => request("/login", { method: "POST", body: { email, password } }),
  logout: () => request("/logout", { method: "POST" }),
  cart: () => request("/cart"),
  addItem: (product_id, qty = 1) => request("/cart/items", { method: "POST", body: { product_id, qty } }),
  setQty: (product_id, qty) => request(`/cart/items/${product_id}`, { method: "PATCH", body: { qty } }),
  removeItem: (product_id) => request(`/cart/items/${product_id}`, { method: "DELETE" }),
  checkout: (address) => request("/checkout", {
  method: "POST",
  body: {
    delivery_address: address,
  },
}),
  orders: () => request("/orders"),
};
