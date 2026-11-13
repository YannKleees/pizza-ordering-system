/* Vibe coded: this web interface was written with an AI assistant in 2026.
   The customer shop. Everything that matters (prices, discounts, loyalty, orders) is decided by
   the server; this file only shows it. */
import { $, $$, api, busy, esc, money, odo, passwordField, shake, toast, when, wirePassword, wordmark } from "./ui.js";
import { itemArt, pizzaArt } from "./pizza-art.js";

const app = $("#app");
const state = {
  me: null, menu: [], basket: null, orders: [],
  view: "menu", tab: "Pizza", vegetarian: false, vegan: false, query: "",
  method: "Delivery", placed: null, timers: [],
};

/* ================================================================ logging in */

function renderAuth(mode = "login", { username = "", notice = "" } = {}) {
  stopTimers();
  document.body.classList.remove("basket-open");
  app.innerHTML = `
    <main class="auth">
      <section class="poster">
        ${wordmark()}
        <h1>Hot pizza at your door in 30 minutes.</h1>
        <div class="poster-art" aria-hidden="true">${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni", "Mushrooms", "Black Olives", "Spinach", "Red Onions"], 4242)}</div>
      </section>
      <section class="auth-side"><div class="auth-box"></div></section>
    </main>`;
  const box = $(".auth-box");
  wirePassword(box);
  mode === "login" ? showLogin(box, username, notice) : showRegister(box);
}

function showLogin(box, username = "", notice = "") {
  box.innerHTML = `
    <form class="auth-form" novalidate>
      <h2>Log in to order</h2>
      ${notice ? `<p class="note">${esc(notice)}</p>` : ""}
      <div class="field">
        <label for="username">Username</label>
        <input class="input" id="username" name="username" autocomplete="username" autocapitalize="off" spellcheck="false" required value="${esc(username)}">
      </div>
      ${passwordField({ id: "password", label: "Password", autocomplete: "current-password" })}
      <p class="error" role="alert"></p>
      <button class="btn btn-lead btn-big btn-wide" type="submit">Log in</button>
      <div class="row spread">
        <button type="button" class="btn-plain" data-go="register">Create an account</button>
        <button type="button" class="btn-plain" data-demo>Use the demo account</button>
      </div>
    </form>`;
  const form = $("form", box);
  (username ? form.password : form.username).focus();
  $("[data-go]", box).onclick = () => showRegister(box);
  $("[data-demo]", box).onclick = () => { form.username.value = "demo"; form.password.value = "demo"; form.requestSubmit(); };
  form.onsubmit = (event) => {
    event.preventDefault();
    const error = $(".error", form);
    error.textContent = "";
    busy($("[type=submit]", form), async () => {
      try {
        await api("/api/login", { method: "POST", body: { username: form.username.value, password: form.password.value } });
        await start();
      } catch (err) {
        error.textContent = err.message;
        form.password.setAttribute("aria-invalid", "true");
        shake(box);
        form.password.focus();
        form.password.select();
      }
    });
  };
  form.password.oninput = () => form.password.removeAttribute("aria-invalid");
}

function showRegister(box) {
  box.innerHTML = `
    <form class="auth-form" novalidate>
      <h2>Create an account</h2>
      <div class="grid-2">
        <div class="field"><label for="name">First name</label><input class="input" id="name" name="name" autocomplete="given-name" required></div>
        <div class="field"><label for="last_name">Last name</label><input class="input" id="last_name" name="last_name" autocomplete="family-name" required></div>
      </div>
      <div class="grid-2">
        <div class="field"><label for="birthdate">Birthdate</label><input class="input" id="birthdate" name="birthdate" type="date" autocomplete="bday" required></div>
        <div class="field"><label for="phone_number">Phone</label><input class="input" id="phone_number" name="phone_number" type="tel" inputmode="tel" autocomplete="tel" required></div>
      </div>
      <div class="field"><span id="gender-label">Gender</span>${genderSegment("Other")}</div>
      <div class="field">
        <label for="address">Address</label>
        <input class="input" id="address" name="address" autocomplete="street-address" required>
        <span class="hint">Include the four-digit postal code, for example Grote Gracht 12, 6211 Maastricht. Couriers are matched by it.</span>
      </div>
      <div class="field"><label for="username">Username</label><input class="input" id="username" name="username" autocomplete="username" autocapitalize="off" spellcheck="false" required></div>
      ${passwordField({ id: "password", label: "Password", autocomplete: "new-password" })}
      <p class="error" role="alert"></p>
      <button class="btn btn-lead btn-big btn-wide" type="submit">Create account</button>
      <button type="button" class="btn-plain" data-go="login">I already have an account</button>
    </form>`;
  const form = $("form", box);
  $("#name", form).focus();
  $("[data-go]", box).onclick = () => showLogin(box);
  form.onsubmit = (event) => {
    event.preventDefault();
    const error = $(".error", form);
    error.textContent = "";
    const body = Object.fromEntries(new FormData(form));
    busy($("[type=submit]", form), async () => {
      try {
        await api("/api/register", { method: "POST", body });
        showLogin(box, body.username, "Account created. Log in to order.");
      } catch (err) {
        error.textContent = err.message;
        shake(box);
      }
    });
  };
}

const genderSegment = (current) => `
  <div class="segment" role="radiogroup" aria-labelledby="gender-label">
    ${["Female", "Male", "Other"].map((g) => `<label><input type="radio" name="gender" value="${g}" ${g === current ? "checked" : ""}>${g}</label>`).join("")}
  </div>`;

/* ================================================================ the shop frame */

async function start() {
  try {
    state.me = await api("/api/me");
  } catch (err) {
    if (err.status === 401) return renderAuth();
    app.innerHTML = `<main class="page"><div class="card empty"><h2>The shop can't open</h2><p>${esc(err.message)}</p><button class="btn" onclick="location.reload()">Try again</button></div></main>`;
    return;
  }
  [state.menu, state.basket] = await Promise.all([api("/api/menu"), api("/api/basket")]);
  state.view = "menu";
  renderShop();
}

function renderShop() {
  app.innerHTML = `
    <header class="topbar">
      ${wordmark()}
      <nav class="nav" aria-label="Main">
        ${[["menu", "Menu"], ["orders", "My orders"], ["profile", "Profile"]].map(([id, label]) => `<button data-act="nav" data-view="${id}">${label}</button>`).join("")}
      </nav>
      <button class="btn btn-lead basket-btn" data-act="open-basket" aria-haspopup="dialog">
        Basket <span class="count">0</span> <span class="basket-total"></span>
      </button>
    </header>
    <main id="view"></main>
    <div class="scrim" data-act="close-basket"></div>
    <aside class="drawer" role="dialog" aria-modal="true" aria-label="Your basket" inert>
      <div class="drawer-head"><h2>Your basket</h2><button class="icon-btn" data-act="close-basket" aria-label="Close basket">×</button></div>
      <div class="drawer-body"></div>
      <div class="drawer-foot"></div>
    </aside>`;
  renderDrawer();
  syncBasketButton(false);
  show(state.view, true);
}

function show(view, first = false) {
  stopTimers();
  state.view = view;
  $$(".nav button").forEach((b) => b.toggleAttribute("aria-current", false));
  $(`.nav [data-view="${view}"]`)?.setAttribute("aria-current", "page");
  if (view === "menu") renderMenu(first);
  if (view === "orders") renderOrders();
  if (view === "profile") renderProfile();
  if (!first) window.scrollTo({ top: 0 });
}

function stopTimers() {
  state.timers.forEach(clearInterval);
  state.timers = [];
}

/* ================================================================ menu */

const quantityOf = (id) => state.basket.items.find((line) => line.id === id)?.quantity || 0;

function stampCard() {
  const stamps = state.me.stamps;
  const left = 10 - stamps;
  return `
    <aside class="stampcard" aria-label="Loyalty card">
      <h3>Every 10th pizza is free</h3>
      <div class="stamps" aria-hidden="true">
        ${Array.from({ length: 10 }, (_, i) =>
          i < stamps ? `<span class="stamp inked">${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni"], 600 + i)}</span>`
            : i === 9 ? `<span class="stamp free">Free</span>` : `<span class="stamp">${i + 1}</span>`).join("")}
      </div>
      <p>${stamps} of 10 stamped. ${left === 1 ? "Your next pizza comes with a free one." : `${left} more pizzas and a free one is added to your order.`}</p>
    </aside>`;
}

function footHTML(item) {
  const quantity = quantityOf(item.id);
  return `<span class="price">${money(item.price)}</span>` + (quantity
    ? `<span class="stepper">
         <button data-act="dec" data-id="${item.id}" aria-label="One ${esc(item.name)} less">−</button>
         <span class="n" aria-label="${quantity} in basket">${quantity}</span>
         <button data-act="inc" data-id="${item.id}" aria-label="One ${esc(item.name)} more" ${quantity >= 10 ? "disabled" : ""}>+</button>
       </span>`
    : `<button class="btn" data-act="inc" data-id="${item.id}">Add<span class="sr-only"> ${esc(item.name)}</span></button>`);
}

function visibleItems() {
  const words = state.query.toLowerCase().split(/\s+/).filter(Boolean);
  return state.menu.filter((item) => item.type === state.tab
    && (state.tab !== "Pizza" || ((!state.vegetarian || item.vegetarian) && (!state.vegan || item.vegan)))
    && words.every((word) => (item.name + " " + item.ingredients.join(" ")).toLowerCase().includes(word)));
}

function renderMenu(arriving = true) {
  const counts = Object.fromEntries(["Pizza", "Drink", "Dessert"].map((t) => [t, state.menu.filter((i) => i.type === t).length]));
  $("#view").innerHTML = `
    <div class="page">
      <div class="welcome">
        <div>
          <h1>What are you having, ${esc(state.me.name)}?</h1>
          <p class="muted">${state.me.is_birthday ? "Happy birthday! 10% comes off your order today." : "Baked to order in Maastricht. Delivery takes about 30 minutes, pickup 15."}</p>
        </div>
        ${stampCard()}
      </div>
      <div class="filters">
        <div class="tabs" role="tablist" aria-label="Menu section">
          ${[["Pizza", "Pizzas"], ["Drink", "Drinks"], ["Dessert", "Desserts"]].map(([type, label]) =>
            `<button role="tab" data-act="tab" data-tab="${type}" aria-selected="${state.tab === type}">${label}<span class="n">${counts[type]}</span></button>`).join("")}
        </div>
        <span class="row diet ${state.tab === "Pizza" ? "" : "hidden"}">
          <button class="chip" data-act="diet" data-diet="vegetarian" aria-pressed="${state.vegetarian}">Vegetarian</button>
          <button class="chip" data-act="diet" data-diet="vegan" aria-pressed="${state.vegan}">Vegan</button>
        </span>
        <label class="search"><span class="sr-only">Search the menu</span>
          <input class="input" type="search" id="menu-search" placeholder="Search by name or ingredient" autocomplete="off" value="${esc(state.query)}"></label>
      </div>
      <div class="menu ${arriving ? "arriving" : ""}"></div>
    </div>`;
  renderCards();
}

function renderCards() {
  const items = visibleItems();
  $(".menu").innerHTML = items.length ? items.map((item, i) => `
    <article class="card item" data-item="${item.id}" style="--i:${Math.min(i, 14)}">
      <div class="art">
        ${itemArt(item)}
        <div class="tags">${item.vegan ? `<span class="tag tag-ink">Vegan</span>` : item.vegetarian ? `<span class="tag">Vegetarian</span>` : ""}</div>
      </div>
      <div class="item-body">
        <h3>${esc(item.name)}</h3>
        ${item.ingredients.length ? `<p class="ingredients">${esc(sentence(item.ingredients))}</p>` : ""}
        <div class="item-foot">${footHTML(item)}</div>
      </div>
    </article>`).join("")
    : `<div class="card empty" style="grid-column:1/-1"><h3>Nothing on the menu matches</h3><p class="muted">Try another word, or clear the search and filters.</p><button class="btn" data-act="clear-diet">Clear search and filters</button></div>`;
}

const sentence = (names) => {
  const text = names.join(", ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

/* ================================================================ basket */

async function setQuantity(id, quantity) {
  const had = quantityOf(id);
  try {
    state.basket = await api("/api/basket", { method: "POST", body: { id, quantity } });
  } catch (err) {
    return toast(err.message, { error: true });
  }
  const item = state.menu.find((i) => i.id === id);
  const foot = $(`[data-item="${id}"] .item-foot`);
  if (foot && item) {
    const keepFocus = foot.contains(document.activeElement) && (quantity > had ? "inc" : "dec");
    foot.innerHTML = footHTML(item);
    if (had > 0 && quantity > 0) $(".stepper", foot).style.animation = "none";
    if (keepFocus) ($(`[data-act="${keepFocus}"]`, foot) || $("button", foot))?.focus();
  }
  syncBasketButton(quantity > had);
  renderDrawer(had === 0 ? id : null);
}

function syncBasketButton(bump) {
  const button = $(".basket-btn");
  if (!button) return;
  $(".count", button).textContent = state.basket.count;
  odo($(".basket-total", button), state.basket.count ? money(state.basket.total) : "");
  if (bump) {
    button.classList.remove("bump");
    void button.offsetWidth;
    button.classList.add("bump");
  }
}

function basketTotals() {
  const b = state.basket;
  const birthday = b.birthday ? Math.round(b.subtotal * 10) / 100 : 0;
  return { birthday, total: Math.max(0, b.total - birthday) };
}

function renderDrawer(newId = null) {
  const body = $(".drawer-body"), foot = $(".drawer-foot");
  if (!body) return;
  const b = state.basket;

  if (state.placed) {
    const p = state.placed;
    body.innerHTML = `
      <div class="placed">
        <div class="burst" aria-hidden="true">${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni", "Spinach"], 77)}</div>
        <h2>Order placed</h2>
        <div><p class="muted">Confirmation number</p><p class="number">${esc(p.confirmation_number)}</p></div>
        <p>${p.delivery_method === "Delivery" ? `On its way to ${esc(state.me.address)} in about ${esc(p.delivery_time_estimation)}.` : "Ready for pickup in about 15 minutes."}</p>
        <p><strong>${money(p.total_price)}</strong>${p.discount_applied ? `, ${money(p.discount_amount)} off` : ""}</p>
        ${p.free_pizza ? `<p class="note note-red">That was your 10th pizza. A free one is in the box.</p>` : ""}
        <p class="muted">Changed your mind? You can cancel for five minutes under My orders.</p>
      </div>`;
    foot.innerHTML = `<button class="btn btn-lead btn-big btn-wide" data-act="track">Follow this order</button>`;
    return;
  }

  if (!b.items.length) {
    body.innerHTML = `<div class="empty"><h3>Nothing in here yet</h3><p class="muted">Add a pizza from the menu and it shows up here.</p><button class="btn" data-act="close-basket">Back to the menu</button></div>`;
    foot.innerHTML = "";
    foot.classList.add("hidden");
    return;
  }
  foot.classList.remove("hidden");

  body.innerHTML = b.items.map((line) => {
    const item = state.menu.find((i) => i.id === line.id) || { ...line, ingredients: [] };
    return `
      <div class="line ${line.id === newId ? "is-new" : ""}">
        ${itemArt(item)}
        <div><div class="name">${esc(line.name)}</div><div class="each">${money(line.price)} each</div></div>
        <div class="right">
          <span class="stepper">
            <button data-act="dec" data-id="${line.id}" aria-label="One ${esc(line.name)} less">−</button>
            <span class="n">${line.quantity}</span>
            <button data-act="inc" data-id="${line.id}" aria-label="One ${esc(line.name)} more" ${line.quantity >= 10 ? "disabled" : ""}>+</button>
          </span>
          <div class="sum">${money(line.price * line.quantity)}</div>
        </div>
      </div>`;
  }).join("");

  const { birthday, total } = basketTotals();
  if (!$(".sums", foot)) {
    foot.innerHTML = `
      <div class="code-area"></div>
      <div class="sums">
        <div><span>Subtotal</span><span data-sum="subtotal"></span></div>
        <div class="minus hidden" data-row="discount"><span data-sum="code"></span><span data-sum="discount"></span></div>
        <div class="minus hidden" data-row="birthday"><span>Birthday, 10% off</span><span data-sum="birthday"></span></div>
        <div class="total"><span>Total</span><span data-sum="total"></span></div>
        <div class="muted" style="font-size:.9rem"><span>Includes 9% VAT</span><span data-sum="vat"></span></div>
      </div>
      <div class="segment" role="radiogroup" aria-label="How do you want it?">
        ${["Delivery", "Pickup"].map((m) => `<label><input type="radio" name="method" value="${m}" ${state.method === m ? "checked" : ""}>${m}</label>`).join("")}
      </div>
      <p class="muted where" style="font-size:.93rem"></p>
      <button class="btn btn-lead btn-big btn-wide" data-act="place-order">Place order</button>`;
  }
  $(".code-area", foot).innerHTML = b.discount_code
    ? `<p class="note">Code ${esc(b.discount_code)} is applied.</p>`
    : `<form class="code-row" data-form="code">
         <label class="sr-only" for="code">Discount code</label>
         <input class="input" id="code" name="code" placeholder="Discount code" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc($("#code")?.value || "")}">
         <button class="btn" type="submit">Apply</button>
         <p class="error" role="alert" style="grid-column:1/-1;min-height:0"></p>
       </form>`;
  $('[data-sum="subtotal"]', foot).textContent = money(b.subtotal);
  $('[data-row="discount"]', foot).classList.toggle("hidden", !b.discount);
  $('[data-sum="code"]', foot).textContent = b.discount_code ? `Code ${b.discount_code}` : "Discount";
  $('[data-sum="discount"]', foot).textContent = "−" + money(b.discount);
  $('[data-row="birthday"]', foot).classList.toggle("hidden", !birthday);
  $('[data-sum="birthday"]', foot).textContent = "−" + money(birthday);
  odo($('[data-sum="total"]', foot), money(total));
  $('[data-sum="vat"]', foot).textContent = money(total * 9 / 109);
  syncWhere();
}

function syncWhere() {
  const where = $(".drawer-foot .where");
  if (where) where.textContent = state.method === "Delivery" ? `To ${state.me.address}, about 30 minutes.` : "Pick it up at the counter in about 15 minutes.";
}

function openBasket() {
  const drawer = $(".drawer");
  state.opener = document.activeElement;
  drawer.inert = false;
  document.body.classList.add("basket-open");
  $(".drawer-head .icon-btn").focus({ preventScroll: true });
}

function closeBasket() {
  if (!document.body.classList.contains("basket-open")) return;
  document.body.classList.remove("basket-open");
  $(".drawer").inert = true;
  if (state.placed) { state.placed = null; setTimeout(renderDrawer, 280); }
  (state.opener?.isConnected ? state.opener : $(".basket-btn"))?.focus({ preventScroll: true });
}

async function applyCode(form) {
  const error = $(".error", form);
  error.textContent = "";
  await busy($("[type=submit]", form), async () => {
    try {
      state.basket = await api("/api/basket/discount", { method: "POST", body: { code: form.code.value.trim().toUpperCase() } });
      form.code.value = "";
      renderDrawer();
      syncBasketButton(false);
      toast(`Code applied, ${money(state.basket.discount)} off.`);
    } catch (err) {
      error.textContent = err.message;
      form.code.setAttribute("aria-invalid", "true");
      form.code.focus();
    }
  });
}

async function placeOrder(button) {
  await busy(button, async () => {
    try {
      state.placed = await api("/api/orders", { method: "POST", body: { method: state.method } });
      [state.basket, state.me] = await Promise.all([api("/api/basket"), api("/api/me")]);
      $(".drawer-foot").innerHTML = "";
      renderDrawer();
      syncBasketButton(false);
      if (state.view === "menu") renderMenu(false);
    } catch (err) {
      toast(err.message, { error: true });
    }
  });
}

/* ================================================================ orders */

const STEPS = {
  Delivery: [["Pending", "In the kitchen"], ["Ready for Delivery", "Waiting for a courier"], ["Out for Delivery", "On its way"], ["Delivered", "Delivered"]],
  Pickup: [["Pending", "In the kitchen"], ["Ready for Delivery", "Ready to pick up"], ["Delivered", "Picked up"]],
};

function orderCard(order) {
  const cancelled = order.status === "Cancelled";
  const steps = STEPS[order.delivery_method] || STEPS.Delivery;
  const at = steps.findIndex(([status]) => status === order.status);
  const last = at === steps.length - 1;
  const left = order.cancel_seconds_left;
  return `
    <article class="card order ${cancelled ? "is-cancelled" : ""}" data-order="${order.order_id}">
      <div class="order-head">
        <h3>${cancelled ? "Cancelled" : esc(at >= 0 ? steps[at][1] : order.status)}</h3>
        <span class="muted">${when(order.order_date)}, ${esc(order.delivery_method.toLowerCase())}, no. ${esc(order.confirmation_number)}</span>
      </div>
      ${cancelled ? "" : `<ol class="track" aria-label="Progress">
        ${steps.map(([, label], i) => `<li class="${i < at || (last && i === at) ? "done" : i === at ? "now" : ""}" ${i === at ? 'aria-current="step"' : ""}>${label}</li>`).join("")}
      </ol>`}
      <p class="order-items">${order.items.map((i) => `${i.quantity} × ${esc(i.name)}`).join(", ")}</p>
      <div class="row spread">
        <strong class="price">${money(order.total_price)}</strong>
        ${left > 0 ? `<button class="btn btn-small" data-act="cancel-order" data-id="${order.order_id}">Cancel order <span class="muted" data-left="${left}">${clock(left)}</span></button>` : ""}
      </div>
    </article>`;
}

const clock = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

async function loadOrders() {
  try {
    state.orders = await api("/api/orders");
  } catch (err) {
    if (err.status === 401) return renderAuth();
    return;
  }
  const list = $(".orders");
  if (!list) return;
  list.innerHTML = state.orders.length ? state.orders.map(orderCard).join("")
    : `<div class="card empty"><h3>No orders yet</h3><p class="muted">Your orders show up here, with where they are right now.</p><button class="btn btn-lead" data-act="nav" data-view="menu">Go to the menu</button></div>`;
}

function renderOrders() {
  $("#view").innerHTML = `<div class="page page-narrow"><h1 style="margin-bottom:1.5rem">My orders</h1><div class="orders"><p class="muted">Loading your orders</p></div></div>`;
  loadOrders();
  state.timers.push(setInterval(() => { if (!document.hidden && !document.activeElement?.closest(".orders")) loadOrders(); }, 8000));
  state.timers.push(setInterval(() => {
    $$("[data-left]").forEach((el) => {
      const left = Number(el.dataset.left) - 1;
      el.dataset.left = left;
      el.textContent = clock(Math.max(0, left));
      if (left <= 0) el.closest("button").remove();
    });
  }, 1000));
}

/* ================================================================ profile */

function renderProfile() {
  const me = state.me;
  const days = me.days_until_birthday;
  $("#view").innerHTML = `
    <div class="page">
      <h1 style="margin-bottom:1.5rem">Profile</h1>
      <div class="profile-grid">
        <form class="card profile-form" novalidate>
          <div class="grid-2">
            <div class="field"><label for="name">First name</label><input class="input" id="name" name="name" autocomplete="given-name" value="${esc(me.name)}"></div>
            <div class="field"><label for="last_name">Last name</label><input class="input" id="last_name" name="last_name" autocomplete="family-name" value="${esc(me.last_name)}"></div>
          </div>
          <div class="grid-2">
            <div class="field"><label for="birthdate">Birthdate</label><input class="input" id="birthdate" name="birthdate" type="date" autocomplete="bday" value="${esc(me.birthdate)}"></div>
            <div class="field"><label for="phone_number">Phone</label><input class="input" id="phone_number" name="phone_number" type="tel" autocomplete="tel" value="${esc(me.phone_number)}"></div>
          </div>
          <div class="field"><span id="gender-label">Gender</span>${genderSegment(me.gender)}</div>
          <div class="field"><label for="address">Delivery address</label><input class="input" id="address" name="address" autocomplete="street-address" value="${esc(me.address)}"></div>
          <p class="error" role="alert"></p>
          <div class="row spread">
            <button class="btn btn-lead" type="submit">Save changes</button>
            <button class="btn-plain" type="button" data-act="logout">Log out ${esc(me.username)}</button>
          </div>
        </form>
        <div class="stack">
          ${stampCard()}
          <p class="note" style="max-width:350px">${days === 0 ? "Happy birthday! 10% comes off your order today." : days == null ? "Order on your birthday and 10% comes off." : `${days} ${days === 1 ? "day" : "days"} until your birthday. Order that day and 10% comes off.`}</p>
        </div>
      </div>
    </div>`;
  const form = $(".profile-form");
  form.onsubmit = (event) => {
    event.preventDefault();
    const error = $(".error", form);
    error.textContent = "";
    busy($("[type=submit]", form), async () => {
      try {
        await api("/api/me", { method: "PUT", body: Object.fromEntries(new FormData(form)) });
        state.me = await api("/api/me");
        syncWhere();
        toast("Changes saved.");
      } catch (err) {
        error.textContent = err.message;
      }
    });
  };
}

/* ================================================================ events */

app.addEventListener("click", async (event) => {
  const el = event.target.closest("[data-act]");
  if (!el) return;
  const id = Number(el.dataset.id);
  switch (el.dataset.act) {
    case "nav": closeBasket(); show(el.dataset.view); break;
    case "tab": state.tab = el.dataset.tab; renderMenu(true); $(`[data-tab="${state.tab}"]`).focus(); break;
    case "diet": state[el.dataset.diet] = !state[el.dataset.diet]; el.setAttribute("aria-pressed", state[el.dataset.diet]); $(".menu").classList.add("arriving"); renderCards(); break;
    case "clear-diet": state.vegetarian = state.vegan = false; state.query = ""; renderMenu(true); break;
    case "inc": setQuantity(id, quantityOf(id) + 1); break;
    case "dec": setQuantity(id, quantityOf(id) - 1); break;
    case "open-basket": openBasket(); break;
    case "close-basket": closeBasket(); break;
    case "place-order": placeOrder(el); break;
    case "track": closeBasket(); show("orders"); break;
    case "cancel-order":
      await busy(el, async () => {
        try { await api(`/api/orders/${id}/cancel`, { method: "POST" }); toast("Order cancelled."); }
        catch (err) { toast(err.message, { error: true }); }
        await loadOrders();
      });
      break;
    case "logout":
      await api("/api/logout", { method: "POST" });
      renderAuth("login", { notice: "You are logged out." });
      break;
  }
});

app.addEventListener("submit", (event) => {
  if (event.target.dataset.form === "code") { event.preventDefault(); applyCode(event.target); }
});
app.addEventListener("change", (event) => {
  if (event.target.name === "method") { state.method = event.target.value; syncWhere(); }
});
app.addEventListener("input", (event) => {
  if (event.target.id === "code") { event.target.removeAttribute("aria-invalid"); }
  if (event.target.id === "menu-search") { state.query = event.target.value; $(".menu").classList.remove("arriving"); renderCards(); }
});
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeBasket(); });

start();
