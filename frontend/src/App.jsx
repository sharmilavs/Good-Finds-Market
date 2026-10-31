import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";

const money = (cents) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format((cents || 0) / 100);
const categories = ["All products", "Coffee & Kitchen", "Electronics", "Home & Living", "Fashion", "Beauty", "Books", "Fitness", "Accessories"];
const categoryFor = (p) => p.category || (() => {
  const name = p.name.toLowerCase();
  if (/kettle|grinder|dripper|coffee|brew|moka|aero|french press|frother|espresso/.test(name)) return "Coffee & Kitchen";
  if (/headphone|speaker|watch|charger|mouse|keyboard|power bank/.test(name)) return "Electronics";
  if (/lamp|cushion|bottle|storage|bedsheet|planter|organizer/.test(name)) return "Home & Living";
  if (/shirt|t-shirt|backpack|wallet|sunglasses|sneaker/.test(name)) return "Fashion";
  if (/skincare|face wash|sunscreen|moisturizer|lip balm/.test(name)) return "Beauty";
  if (/book|journal|notebook/.test(name)) return "Books";
  if (/yoga|fitness|resistance|dumbbell|mat/.test(name)) return "Fitness";
  return "Accessories";
})();
const visualFor = (p) => {
  const name = p.name.toLowerCase();
  if (/kettle|coffee|french press|moka|aero|dripper/.test(name)) return "☕";
  if (/grinder|mouse|keyboard/.test(name)) return "⚙️";
  if (/headphone|speaker/.test(name)) return "🎧";
  if (/watch/.test(name)) return "⌚";
  if (/shirt|t-shirt|sneaker|backpack|wallet/.test(name)) return "🛍️";
  if (/lamp|cushion|bedsheet|planter/.test(name)) return "🏡";
  if (/book|journal|notebook/.test(name)) return "📚";
  if (/beauty|skin|sunscreen|moisturizer|lip/.test(name)) return "✨";
  if (/yoga|fitness|dumbbell|mat/.test(name)) return "🏋️";
  if (/bottle/.test(name)) return "🧴";
  return "✳️";
};

function AuthForm({ onDone, onError }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    try {
      await (mode === "login" ? api.login(email, password) : api.register(email, password));
      onDone();
    } catch (e) { onError(e.message); }
  };
  return <form className="auth-form" onSubmit={submit}>
    <label>Email address<input required type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} /></label>
    <label>Password<input required minLength="6" type="password" placeholder="Enter your password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
    <button className="btn btn-primary auth-submit" type="submit">{mode === "login" ? "Sign in" : "Create account"}</button>
    <button className="text-button" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "New to Good Finds? Create an account" : "Already have an account? Sign in"}</button>
  </form>;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total_cents: 0 });
  const [orders, setOrders] = useState([]);
  const [message, setMessage] = useState("");
  const [showAuth, setShowAuth] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All products");
  const [sort, setSort] = useState("featured");
  const [wishlist, setWishlist] = useState(() => JSON.parse(localStorage.getItem("kb-wishlist") || "[]"));
  const [showWishlist, setShowWishlist] = useState(false);
  const [dark, setDark] = useState(false);
  const [recent, setRecent] = useState([]);
  const [toast, setToast] = useState("");
  const [showAddress, setShowAddress] = useState(false);
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [address, setAddress] = useState({ full_name: "", phone: "", address_line: "", city: "", state: "", postal_code: "" });

  const refresh = useCallback(async () => {
    const [me, c] = await Promise.all([api.me(), api.cart()]);
    setUser(me.user); setCart(c);
    setOrders(me.user ? (await api.orders()).orders : []);
  }, []);

  const attempt = async (fn) => {
    setMessage("");
    try { await fn(); }
    catch (e) { setMessage(e.message); }
  };

  useEffect(() => {
    attempt(async () => { setProducts((await api.products()).products); await refresh(); });
  }, [refresh]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 2600);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => { localStorage.setItem("kb-wishlist", JSON.stringify(wishlist)); }, [wishlist]);

  const addItem = (id) => attempt(async () => {
    setCart(await api.addItem(id));
    const product = products.find((p) => p.id === id);
    setToast(`${product?.name || "Item"} added to your cart`);
  });
  const setQty = (id, qty) => attempt(async () => setCart(await api.setQty(id, qty)));
  const removeItem = (id) => attempt(async () => { setCart(await api.removeItem(id)); setToast("Item removed from cart"); });
  const logout = () => attempt(async () => { await api.logout(); await refresh(); setToast("You have been signed out"); });
  const checkout = () => {
    if (!user) { setShowAuth(true); setMessage("Sign in to place your order. Your cart will be saved."); return; }
    setShowAddress(true);
    setMessage("");
  };
  const placeOrder = async (event) => {
    event.preventDefault(); // Stop the browser from reloading before the API request finishes.
    if (isPlacingOrder) return;
    setMessage("");
    if (!address.full_name.trim() || !address.address_line.trim() || !address.city.trim() || !address.state.trim()) {
      setMessage("Please complete every delivery address field.");
      return;
    }
    if (!/^\d{10}$/.test(address.phone.trim())) {
      setMessage("Enter a valid 10-digit Indian mobile number.");
      return;
    }
    if (!/^\d{6}$/.test(address.postal_code.trim())) {
      setMessage("Enter a valid 6-digit Indian PIN code.");
      return;
    }
    try {
      setIsPlacingOrder(true);
      const order = await api.checkout(address);
      setShowAddress(false);
      setAddress({ full_name: "", phone: "", address_line: "", city: "", state: "", postal_code: "" });
      setMessage(`Order placed successfully! Order #${String(order.order_id).slice(-6)} · Total ${money(order.total_cents)}.`);
      setProducts((await api.products()).products);
      await refresh();
      document.getElementById("orders")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      setMessage(e.message || "Unable to place your order. Please try again.");
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const filteredProducts = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    let list = products.filter((p) => (!showWishlist || wishlist.some((id) => String(id) === String(p.id))) &&
      (showWishlist || category === "All products" || categoryFor(p) === category) &&
      (!query || `${p.name} ${p.description || ""} ${categoryFor(p)}`.toLocaleLowerCase().includes(query)));
    if (sort === "price-low") list = [...list].sort((a, b) => a.price_cents - b.price_cents);
    if (sort === "price-high") list = [...list].sort((a, b) => b.price_cents - a.price_cents);
    if (sort === "name") list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    return list;
  }, [products, search, category, sort, showWishlist, wishlist]);

  const itemCount = cart.items.reduce((n, i) => n + i.qty, 0);
  const toggleWish = (id) => setWishlist((old) => old.some((x) => String(x) === String(id)) ? old.filter((x) => String(x) !== String(id)) : [...old, id]);
  const viewProduct = (id) => setRecent((old) => [id, ...old.filter((x) => x !== id)].slice(0, 3));

  return <div className={`store ${dark ? "dark" : ""}`}>
    <div className="announcement"><span>✦</span> A little joy in every find <b>— Discover something lovely today</b><span className="announcement-right">Thoughtfully selected everyday essentials</span></div>
    <header className="site-header">
      <a className="brand" href="#home" aria-label="Good Finds Market home"><span className="brand-mark">G<span>✦</span></span><span>Good Finds<small>EVERYDAY SHOPPING</small></span></a>
      <div className="search-wrap"><span>⌕</span><input aria-label="Search products" placeholder="Search products, brands and more..." value={search} onChange={(e) => { setSearch(e.target.value); setCategory("All products"); setShowWishlist(false); }} /><kbd>⌘ K</kbd></div>
      <div className="header-actions">
        <button className="icon-action theme-action" onClick={() => setDark(!dark)} title="Toggle theme">{dark ? "☀" : "☾"}<span>Theme</span></button>
        <button className={`icon-action ${showWishlist ? "active" : ""}`} onClick={() => { setShowWishlist(!showWishlist); setCategory("All products"); setSearch(""); }} title="Wishlist">♡<span>Wishlist</span><em>{wishlist.length}</em></button>
        {user ? <div className="user-action"><span className="user-avatar">{user.email?.[0]?.toUpperCase() || "U"}</span><span className="user-label">Hi, {user.email?.split("@")[0]}</span><button className="text-button" onClick={logout}>Sign out</button></div> : <button className="icon-action" onClick={() => setShowAuth(!showAuth)}>♙<span>Account</span></button>}
        <a className="cart-action" href="#cart"><span>🛍</span><span className="cart-label">Cart</span><b>{itemCount}</b></a>
      </div>
    </header>
    <nav className="category-nav" aria-label="Product categories">{categories.map((c) => <button key={c} className={category === c && !showWishlist ? "selected" : ""} onClick={() => { setCategory(c); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth", block: "start" }); }}>{c}</button>)}<span className="nav-promo">Fresh finds across every category <span>→</span></span></nav>

    <section className="quick-categories" aria-label="Shop by category">
      <button onClick={() => { setCategory("Coffee & Kitchen"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>☕</span><b>Coffee & Kitchen</b></button>
      <button onClick={() => { setCategory("Electronics"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>🎧</span><b>Electronics</b></button>
      <button onClick={() => { setCategory("Home & Living"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>🏡</span><b>Home & Living</b></button>
      <button onClick={() => { setCategory("Fashion"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>👜</span><b>Fashion</b></button>
      <button onClick={() => { setCategory("Beauty"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>✨</span><b>Beauty</b></button>
      <button onClick={() => { setCategory("Books"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>📚</span><b>Books</b></button>
      <button onClick={() => { setCategory("Fitness"); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth" }); }}><span>🏃</span><b>Fitness</b></button>
    </section>

    {message && <div className="notice" role="status"><span>ⓘ</span>{message}<button onClick={() => setMessage("")}>×</button></div>}
    {showAuth && !user && <div className="auth-popover"><div className="auth-heading"><div><span className="eyebrow">WELCOME BACK</span><h3>Your account</h3></div><button onClick={() => setShowAuth(false)}>×</button></div><AuthForm onError={setMessage} onDone={() => attempt(async () => { setShowAuth(false); await refresh(); setToast("Welcome to Good Finds Market!"); })} /></div>}

    <main id="home">
      {(category === "All products" && !search.trim() && !showWishlist) && <section className="hero">
        <div className="hero-copy"><span className="eyebrow light">THE GOOD FINDS EDIT</span><h1>Everyday shopping,<br /><em>beautifully curated.</em></h1><p>From useful tech to home comforts, discover thoughtfully picked products for everyday living.</p><a href="#products" className="hero-button">Explore the collection <span>↗</span></a><div className="hero-proof"><span>✦ Curated essentials</span><span>✦ Quality you can feel</span></div></div>
        <div className="hero-art"><div className="sun-disc" /><div className="hero-bean bean-one">✳</div><div className="hero-bean bean-two">✳</div><div className="hero-product hero-kettle">☕<small>POUR WITH PURPOSE</small></div><div className="hero-product hero-cup">◒</div><div className="hero-sticker">BREW<br />HAPPY<br /><b>♡</b></div><div className="hero-caption">THE SLOW<br />MORNING CLUB</div></div>
        <div className="hero-bottom"><span>01 / 03</span><div className="hero-dots"><i /><i /><i /></div><span>SCROLL TO DISCOVER ↓</span></div>
      </section>}

      <section className="benefits"><div><span>✦</span><p><b>Curated with care</b><small>Only the good stuff</small></p></div><div><span>♧</span><p><b>Secure checkout</b><small>Shop with confidence</small></p></div><div><span>↗</span><p><b>Easy cart management</b><small>Your picks stay with you</small></p></div><div><span>♡</span><p><b>Made for everyday living</b><small>Little things, big joy</small></p></div></section>

      <section className="shop-section" id="products">
        <div className="section-heading"><div><span className="eyebrow">THE GOOD STUFF</span><h2>{showWishlist ? "Your wishlist" : search.trim() ? `Search results for “${search.trim()}”` : category !== "All products" ? category : "Discover good finds."}</h2><p>{showWishlist ? "Your saved favourites, all in one place." : "Explore handpicked finds for your home, style, work and everyday moments."}</p></div><label className="sort-control">Sort by <select value={sort} onChange={(e) => setSort(e.target.value)}><option value="featured">Featured</option><option value="price-low">Price: low to high</option><option value="price-high">Price: high to low</option><option value="name">Name</option></select></label></div>
        <div className="filter-row"><div className="filter-chips">{categories.map((c) => <button key={c} className={category === c && !showWishlist ? "chosen" : ""} onClick={() => { setCategory(c); setShowWishlist(false); document.getElementById("products")?.scrollIntoView({ behavior: "smooth", block: "start" }); }}>{c}</button>)}</div><span className="result-count">{filteredProducts.length} products</span></div>
        <div className="product-grid">
          {filteredProducts.map((p, index) => <article className="product-card" key={p.id} onMouseEnter={() => viewProduct(p.id)}>
            <div className="product-visual" style={{ "--product-tone": p.tone || "#b9a58d" }}><span className="product-tag">{index === 0 ? "CUSTOMER FAVOURITE" : index === 1 ? "BREW BETTER" : "MADE FOR DAILY USE"}</span><button className={`wish-button ${wishlist.some((id) => String(id) === String(p.id)) ? "wished" : ""}`} onClick={() => toggleWish(p.id)} aria-label="Toggle wishlist">{wishlist.some((id) => String(id) === String(p.id)) ? "♥" : "♡"}</button><div className="product-emoji">{visualFor(p)}</div><span className="visual-caption">GOOD FINDS / OBJECTS FOR EVERYDAY</span></div>
            <div className="product-details"><span className="product-category">{categoryFor(p)}</span><h3>{p.name}</h3><p>{p.description}</p><div className="rating curated-label"><span>✦</span><small> Carefully selected for everyday use</small></div><div className="product-buy"><div><strong>{money(p.price_cents)}</strong><small>{p.stock > 0 ? `${p.stock} available` : "Currently sold out"}</small></div><button className="add-button" disabled={p.stock === 0} onClick={() => addItem(p.id)}><span>＋</span> Add</button></div></div>
          </article>)}
        </div>
        {filteredProducts.length === 0 && <div className="empty-products"><span>☕</span><h3>{showWishlist ? "Your wishlist is waiting" : "No products found"}</h3><p>{showWishlist ? "Tap the heart on a product to save it here." : "Try another search or choose a different category."}</p><button className="btn btn-primary" onClick={() => { setSearch(""); setCategory("All products"); setShowWishlist(false); }}>Show all products</button></div>}
        {recent.length > 0 && !showWishlist && <div className="recent-note">Recently explored: {recent.map((id) => products.find((p) => p.id === id)?.name).filter(Boolean).join(" · ")}</div>}
      </section>

      <section className="little-banner"><div><span className="eyebrow light">A NOTE TO YOUR FUTURE SELF</span><h2>Find your next favourite.<br /><em>Make every day better.</em></h2><p>Your next favourite find is just a few clicks away.</p></div><div className="banner-art">☕<span>GOOD<br />THINGS<br />BREW HERE</span></div></section>

      <section className="lower-layout">
        <div className="order-panel" id="orders">
          <div className="panel-title">
            <div>
              <span className="eyebrow">YOUR PURCHASES</span>
              <h2>Order history</h2>
            </div>
            <span className="panel-icon">↗</span>
          </div>

          {orders.length > 0 ? (
            <ul className="orders-list">
              {orders.map((o) => (
                <li key={o.id}>
                  <div>
                    <b>Order </b>

                    <small>
                      {new Date(o.created_at).toLocaleDateString()}
                    </small>

                    <div className="order-items">
                      <b>Purchased Products:</b>

                      {Array.isArray(o.items) && o.items.length > 0 ? (
                        o.items.map((item, index) => (
                          <small key={`${o.id}-${index}`}>
                            {item.name || "Product name unavailable"}
                            {" × "}
                            {item.qty}
                            {" — "}
                            {money(
                              item.line_total_cents ??
                              item.price_cents * item.qty
                            )}
                          </small>
                        ))
                      ) : (
                        <small>Product details unavailable.</small>
                      )}
                    </div>

                    <small>
                      {o.delivery_address?.full_name || "Delivery details saved"}
                    </small>

                    <small>
                      {o.delivery_address
                        ? `${o.delivery_address.address_line}, ${o.delivery_address.city}, ${o.delivery_address.state} ${o.delivery_address.postal_code}`
                        : "Address not recorded for this older order"}
                    </small>

                    {o.delivery_address?.phone && (
                      <small>Contact: {o.delivery_address.phone}</small>
                    )}
                  </div>

                  <span>
                    {(o.items || []).reduce(
                      (total, item) => total + (item.qty || 0),
                      0
                    )} items
                  </span>

                  <strong>{money(o.total_cents)}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              {user
                ? "Your placed orders will appear here."
                : "Sign in to view your order history."}
            </p>
          )}
        </div>
        <aside className="cart-panel" id="cart"><div className="panel-title"><div><span className="eyebrow">READY WHEN YOU ARE</span><h2>Your cart <span className="cart-count">{itemCount}</span></h2></div><span className="panel-icon">🛍</span></div>
          {cart.items.length === 0 ? <div className="empty-cart"><span>🛒</span><b>Your cart is taking a little break.</b><p>Add something lovely from the collection.</p><a href="#products">Explore products ↓</a></div> : <ul className="cart-list">{cart.items.map((i) => <li key={i.product_id}><div className="cart-item-art">☕</div><div className="cart-item-info"><b>{i.name}</b><small>{money(i.price_cents)} each</small><div className="qty"><button aria-label={`Decrease ${i.name}`} onClick={() => setQty(i.product_id, i.qty - 1)}>−</button><span>{i.qty}</span><button aria-label={`Increase ${i.name}`} onClick={() => setQty(i.product_id, i.qty + 1)}>+</button></div></div><div className="cart-item-end"><b>{money(i.line_total_cents)}</b><button onClick={() => removeItem(i.product_id)}>Remove</button></div></li>)}</ul>}
          <div className="cart-total"><span>Subtotal</span><strong>{money(cart.total_cents)}</strong></div><p className="shipping-note">✦ Shipping and taxes calculated at checkout.</p><button className="checkout-button" disabled={cart.items.length === 0} onClick={checkout}>{user ? "Continue to checkout" : "Sign in to checkout"}<span>→</span></button>
          {showAddress && <form className="address-form" onSubmit={placeOrder}>
            <div className="address-form-heading"><b>Delivery address</b><button type="button" onClick={() => setShowAddress(false)}>×</button></div>
            <p>Where should we deliver your order?</p>
            <label>Full name<input required value={address.full_name} onChange={(e) => setAddress({ ...address, full_name: e.target.value })} placeholder="Recipient name" /></label>
            <label>Phone number<input required inputMode="numeric" maxLength="10" value={address.phone} onChange={(e) => setAddress({ ...address, phone: e.target.value.replace(/\D/g, "") })} placeholder="10-digit phone number" /></label>
            <label>House / street / area<input required value={address.address_line} onChange={(e) => setAddress({ ...address, address_line: e.target.value })} placeholder="Door no., street, area" /></label>
            <div className="address-two"><label>City<input required value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} /></label><label>State<input required value={address.state} onChange={(e) => setAddress({ ...address, state: e.target.value })} /></label></div>
            <label>PIN / ZIP code<input required inputMode="numeric" maxLength="6" pattern="[0-9]{6}" value={address.postal_code} onChange={(e) => setAddress({ ...address, postal_code: e.target.value.replace(/\D/g, "") })} /></label>
            <button className="checkout-button" type="submit" disabled={isPlacingOrder || cart.items.length === 0}>{isPlacingOrder ? "Placing your order..." : `Place order · ${money(cart.total_cents)}`} <span>{isPlacingOrder ? "…" : "✓"}</span></button>
          </form>}
          <div className="secure-note">♧ Secure session · Your cart is saved automatically</div>
        </aside>
      </section>
    </main>

    <footer className="footer"><a className="brand footer-brand" href="#home"><span className="brand-mark">G<span>✦</span></span><span>Good Finds<small>EVERYDAY SHOPPING</small></span></a><p>Everyday shopping, beautifully curated.</p><span>© 2026 Good Finds Market</span></footer>
    {toast && <div className="toast" role="status"><span>✓</span>{toast}</div>}
  </div>;
}
