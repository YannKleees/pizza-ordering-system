/* Vibe coded: this web interface was written with an AI assistant in 2026.
   The staff pages: live orders, couriers, menu, ingredients, discount codes, history, earnings. */
import { $, $$, api, busy, esc, money, odo, passwordField, shake, sheet, toast, when, wirePassword, wordmark } from "./ui.js";
import { itemArt, pizzaArt } from "./pizza-art.js";
import { areaMap, onMap } from "./area-map.js";

const app = $("#app");
const state = { me: null, view: "board", board: null, menuTab: "Pizza", timers: [], report: {}, area: null, seen: null, signature: "" };
try { state.boardMode = localStorage.getItem("boardMode") === "map" ? "map" : "lanes"; } catch { state.boardMode = "lanes"; }

const VIEWS = [["board", "Orders"], ["couriers", "Couriers"], ["menu", "Menu"], ["ingredients", "Ingredients"],
  ["codes", "Discount codes"], ["history", "History"], ["earnings", "Earnings"]];

/* ================================================================ logging in */

function renderLogin(notice = "") {
  stopTimers();
  app.innerHTML = `
    <main class="auth">
      <section class="poster">
        ${wordmark("Staff")}
        <h1>Kitchen, couriers and the till.</h1>
        <div class="poster-art" aria-hidden="true">${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni", "Mushrooms", "Black Olives", "Red Peppers"], 5151)}</div>
      </section>
      <section class="auth-side"><div class="auth-box">
        <form class="auth-form" novalidate>
          <h2>Staff login</h2>
          ${notice ? `<p class="hint">${esc(notice)}</p>` : ""}
          <div class="field"><label for="username">Username</label>
            <input class="input" id="username" name="username" autocomplete="username" autocapitalize="off" spellcheck="false" required></div>
          ${passwordField({ id: "password", label: "Password", autocomplete: "current-password" })}
          <p class="error" role="alert"></p>
          <button class="btn btn-lead btn-big btn-wide" type="submit">Log in</button>
          <p class="hint">The example data has one staff account: staff / staff.</p>
        </form>
      </div></section>
    </main>`;
  const box = $(".auth-box"), form = $("form", box);
  wirePassword(box);
  form.username.focus();
  form.onsubmit = (event) => {
    event.preventDefault();
    $(".error", form).textContent = "";
    busy($("[type=submit]", form), async () => {
      try {
        await api("/api/staff/login", { method: "POST", body: { username: form.username.value, password: form.password.value } });
        await start();
      } catch (err) {
        $(".error", form).textContent = err.message;
        shake(box);
        form.password.focus();
        form.password.select();
      }
    });
  };
}

async function start() {
  try {
    state.me = await api("/api/staff/me");
  } catch (err) {
    if (err.status === 401) return renderLogin();
    app.innerHTML = `<main class="main"><div class="card empty"><h2>The staff pages can't open</h2><p>${esc(err.message)}</p><button class="btn" onclick="location.reload()">Try again</button></div></main>`;
    return;
  }
  app.innerHTML = `
    <div class="shell">
      <aside class="side">
        ${wordmark("Staff")}
        <nav aria-label="Staff">${VIEWS.map(([id, label]) => `<button data-view="${id}"><span>${label}</span>${id === "board" ? `<span class="n hidden" data-open></span>` : ""}</button>`).join("")}</nav>
        <div class="who"><span>${esc(state.me?.name || "Staff")}</span><button class="btn-plain" data-act="logout">Log out</button></div>
      </aside>
      <main class="main" id="view"></main>
    </div>`;
  show(location.hash.slice(1) || "board");
}

function stopTimers() { state.timers.forEach(clearInterval); state.timers = []; }

function show(view) {
  if (!VIEWS.some(([id]) => id === view)) view = "board";
  stopTimers();
  state.view = view;
  history.replaceState(null, "", "#" + view);
  $$(".side nav button").forEach((b) => b.toggleAttribute("aria-current", false));
  $(`.side [data-view="${view}"]`).setAttribute("aria-current", "page");
  ({ board: renderBoard, couriers: renderCouriers, menu: renderMenu, ingredients: renderIngredients,
    codes: renderCodes, history: renderHistory, earnings: renderEarnings })[view]();
}

const guard = async (work) => {
  try { return await work(); }
  catch (err) {
    if (err.status === 401) return renderLogin("Your session ended. Log in again.");
    toast(err.message, { error: true });
  }
};

const head = (title, sub, actions = "") =>
  `<div class="head"><div><h1>${title}</h1>${sub ? `<p class="muted">${sub}</p>` : ""}</div><div class="row">${actions}</div></div>`;

const table = (headers, rows, empty) => rows.length
  ? `<div class="table-wrap"><table><thead><tr>${headers.map((h) => `<th${/^(Price|Cost|Total|Discount|Age|Earnings)$/.test(h) ? ' class="num"' : ""}>${h}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`
  : `<div class="card empty">${empty}</div>`;

/* ================================================================ live orders */

const LANES = [["Pending", "In the kitchen"], ["Ready for Delivery", "Ready"], ["Out for Delivery", "Out for delivery"]];

function minutesAgo(iso) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)} h ${minutes % 60} min ago`;
  return when(iso);
}

function ticket(order) {
  const pickup = order.delivery_method === "Pickup";
  const late = (Date.now() - new Date(order.order_date)) / 60000 > 30;
  let action = "";
  if (order.status === "Pending") action = `<button class="btn btn-lead btn-small" data-act="ready" data-id="${order.order_id}">Mark ready</button>`;
  else if (pickup) action = `<button class="btn btn-lead btn-small" data-act="delivered" data-id="${order.order_id}">Mark picked up</button>`;
  else if (order.status === "Ready for Delivery") action = `<p class="to">Waiting for a courier for ${esc(order.postal_code)}.</p><button class="btn btn-small" data-act="delivered" data-id="${order.order_id}">Mark delivered</button>`;
  else action = `<p class="to">With ${esc(order.delivery_person_name || "a courier")}.</p><button class="btn btn-lead btn-small" data-act="delivered" data-id="${order.order_id}">Mark delivered</button>`;
  return `
    <article class="card ticket ${late ? "is-late" : ""}" data-order="${order.order_id}">
      <div class="ticket-top"><strong>No. ${order.order_id}</strong><span class="tag ${pickup ? "tag-ink" : ""}">${pickup ? "Pickup" : "Delivery"}</span></div>
      <div><strong>${esc(order.customer_name)} ${esc(order.last_name || "")}</strong>
        <div class="to">${pickup ? "Collects at the counter" : esc(order.address)}</div>
        <div class="to">${minutesAgo(order.order_date)}${late ? ", over 30 minutes" : ""}</div></div>
      <ul>${order.items.map((i) => `<li>${i.quantity} × ${esc(i.name)}</li>`).join("")}</ul>
      <div class="row spread"><span>${money(order.total_price)}</span></div>
      ${action}
    </article>`;
}

function paintLanes(host) {
  const board = state.board;
  // FLIP: remember where each ticket is, repaint, then let it travel from the old place
  const before = new Map($$(".ticket", host).map((el) => [el.dataset.order, el.getBoundingClientRect()]));
  host.innerHTML = LANES.map(([status, label]) => {
    const orders = board.orders.filter((o) => o.status === status);
    return `<section class="lane" aria-label="${label}"><h2><span>${label}</span><span>${orders.length}</span></h2>
      ${orders.map(ticket).join("") || `<p class="none">Nothing here.</p>`}</section>`;
  }).join("");
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  $$(".ticket", host).forEach((el) => {
    const old = before.get(el.dataset.order);
    const now = el.getBoundingClientRect();
    if (!old) return before.size && el.animate([{ opacity: 0, transform: "scale(0.92)" }, { opacity: 1, transform: "none" }], { duration: 260, easing: "cubic-bezier(0.23,1,0.32,1)" });
    const dx = old.left - now.left, dy = old.top - now.top;
    if (dx || dy) el.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }], { duration: 360, easing: "cubic-bezier(0.23,1,0.32,1)" });
  });
}

function paintMap(host) {
  const board = state.board;
  const deliveries = board.orders.filter((o) => o.delivery_method === "Delivery");
  const offMap = deliveries.filter((o) => !onMap(o.postal_code));
  const list = deliveries.filter((o) => !state.area || o.postal_code === state.area);
  const pickups = board.orders.length - deliveries.length;
  const crew = state.area ? board.couriers.filter((c) => c.assigned_postal_code === state.area) : [];
  host.innerHTML = `
    <div class="card map-card">
      ${areaMap({ orders: board.orders, couriers: board.couriers, selected: state.area })}
      <div class="legend">
        <span><i style="background:#FFFEFB"></i>In the kitchen</span>
        <span><i style="background:#DA251C"></i>Ready</span>
        <span><i style="background:#000"></i>On its way</span>
        <span>● courier available</span><span>○ courier out</span>
      </div>
      <p class="hint">A drawing of the postal areas around the Maas, not a street map. Select an area to see its orders.</p>
      ${offMap.length ? `<p class="hint"><strong>Not on the map:</strong> ${offMap.map((o) => `no. ${o.order_id} (${esc(o.postal_code === "Unknown" ? "no postal code" : o.postal_code)})`).join(", ")}</p>` : ""}
    </div>
    <section class="lane map-list" aria-label="Deliveries">
      <h2><span>${state.area ? `Deliveries to ${esc(state.area)}` : "Open deliveries"}</span><span>${list.length}</span></h2>
      ${state.area ? `<p class="to">${crew.length ? crew.map((c) => `${esc(c.name)} is ${c.availability ? "available" : "out"}`).join(", ") + "." : "No courier covers this area."}</p>
        <button class="btn btn-small" data-act="area-clear">Show all areas</button>` : ""}
      ${list.map(ticket).join("") || `<p class="none">${state.area ? "No open deliveries in this area." : "No open deliveries."}</p>`}
      ${pickups ? `<p class="to">${pickups} pickup ${pickups === 1 ? "order is" : "orders are"} on the board.</p>` : ""}
    </section>`;
}

function paintBoard() {
  const board = state.board;
  const host = $(".board");
  if (!host || !board) return;
  $(".couriers").innerHTML = board.couriers.map((c) =>
    `<span class="courier ${c.availability ? "free" : "out"}"><i></i>${esc(c.name)} <span class="muted">${esc(c.assigned_postal_code)}</span>${c.availability ? "" : " out"}</span>`).join("")
    || `<span class="muted">No couriers yet. Add them under Couriers.</span>`;
  const map = state.boardMode === "map";
  host.classList.toggle("is-map", map);
  map ? paintMap(host) : paintLanes(host);
}

function selectArea(code, orderId) {
  state.area = orderId ? code : state.area === code ? null : code;
  paintBoard();
  const target = orderId ? $(`.ticket[data-order="${orderId}"]`) : null;
  if (target) {
    target.scrollIntoView({ block: "nearest", behavior: "smooth" });
    target.classList.add("flash");
  } else {
    $(`.area[data-area="${code}"]`)?.focus({ preventScroll: true });
  }
}

function noticeNewOrders(board) {
  const waiting = board.orders.filter((o) => o.status === "Pending");
  const open = $("[data-open]");
  if (open) {
    open.textContent = waiting.length;
    open.classList.toggle("hidden", !waiting.length);
  }
  document.title = (waiting.length ? `(${waiting.length}) ` : "") + "Pop Pizza staff";
  if (state.seen) {
    waiting.filter((o) => !state.seen.has(o.order_id)).forEach((o) =>
      toast(`New order no. ${o.order_id} from ${o.customer_name}, ${o.delivery_method.toLowerCase()}.`));
  }
  state.seen = new Set(board.orders.map((o) => o.order_id));
}

async function loadBoard() {
  await guard(async () => {
    const board = await api("/api/staff/board");
    noticeNewOrders(board);
    const signature = JSON.stringify(board) + Math.floor(Date.now() / 60000);
    if (signature === state.signature && $(".board")?.children.length) return;
    state.signature = signature;
    state.board = board;
    paintBoard();
  });
}

function renderBoard() {
  $("#view").innerHTML = head("Orders", "Refreshes every 8 seconds.",
    `<div class="tabs" role="tablist" aria-label="View">${[["lanes", "Board"], ["map", "Map"]].map(([mode, label]) =>
      `<button role="tab" data-act="board-mode" data-mode="${mode}" aria-selected="${state.boardMode === mode}">${label}</button>`).join("")}</div>
     <button class="btn btn-lead" data-act="assign">Send couriers out</button>`) +
    `<div class="couriers" aria-label="Couriers"></div><div class="board"></div>`;
  state.signature = "";
  loadBoard();
  state.timers.push(setInterval(() => { if (!document.hidden) loadBoard(); }, 8000));
}

async function assign(button) {
  await busy(button, () => guard(async () => {
    const result = await api("/api/staff/deliveries/assign", { method: "POST" });
    if (!result.ready) toast("No delivery orders are ready to go.");
    result.assigned.forEach((a) => toast(`${a.courier} takes ${a.orders.length === 1 ? "order" : "orders"} ${a.orders.join(", ")} to ${a.postal_code}.`));
    result.waiting.forEach((message) => toast(message + ".", { error: true }));
    await loadBoard();
  }));
}

/* ================================================================ couriers */

async function renderCouriers() {
  $("#view").innerHTML = head("Couriers", "Each courier covers one postal code and takes up to three orders that came in within three minutes.",
    `<button class="btn btn-lead" data-act="courier-add">Add courier</button>`) + `<div data-list></div>`;
  await guard(async () => {
    const { couriers } = await api("/api/staff/board");
    state.couriers = couriers;
    $("[data-list]").innerHTML = table(["Name", "Postal code", "Status", ""], couriers.map((c) => `
      <tr><td><strong>${esc(c.name)}</strong></td><td>${esc(c.assigned_postal_code)}</td>
        <td><span class="tag ${c.availability ? "" : "tag-quiet"}">${c.availability ? "Available" : "Out or off"}</span></td>
        <td class="actions"><button class="btn btn-small" data-act="courier-edit" data-id="${c.delivery_person_id}">Edit</button><button class="btn btn-small" data-act="courier-delete" data-id="${c.delivery_person_id}">Remove</button></td></tr>`),
      `<h3>No couriers yet</h3><p class="muted">Add one so delivery orders can be sent out.</p>`);
  });
}

function courierSheet(courier) {
  sheet({
    title: courier ? "Edit courier" : "Add courier",
    body: `
      <div class="field"><label for="c-name">Name</label><input class="input" id="c-name" name="name" value="${esc(courier?.name)}" required></div>
      <div class="field"><label for="c-postal">Postal code</label><input class="input" id="c-postal" name="assigned_postal_code" inputmode="numeric" maxlength="4" value="${esc(courier?.assigned_postal_code)}" required>
        <span class="hint">Four digits, for example 6211.</span></div>
      ${courier ? `<label class="check"><input type="checkbox" name="availability" ${courier.availability ? "checked" : ""}>Available for deliveries</label>` : ""}`,
    onSubmit: async (data) => {
      const body = { name: data.get("name"), assigned_postal_code: data.get("assigned_postal_code"), availability: courier ? data.has("availability") : true };
      await api(courier ? `/api/staff/couriers/${courier.delivery_person_id}` : "/api/staff/couriers", { method: courier ? "PUT" : "POST", body });
      toast(courier ? "Changes saved." : "Courier added.");
      renderCouriers();
    },
  });
}

const confirmDelete = (what, path, after) => sheet({
  title: `Remove ${what}?`, body: `<p>This can't be undone.</p>`, action: "Remove", danger: true,
  onSubmit: async () => { await api(path, { method: "DELETE" }); toast("Removed."); after(); },
});

/* ================================================================ menu */

const priceFromCost = (cost) => Math.round((cost * 1.4 * 1.09 + Number.EPSILON) * 100) / 100;

async function renderMenu() {
  $("#view").innerHTML = head("Menu", "A pizza's price follows its ingredients: cost plus 40% margin plus 9% VAT.",
    `<button class="btn btn-lead" data-act="menu-add">Add menu item</button>`) +
    `<div class="row" style="margin-bottom:1rem"><div class="tabs" role="tablist">${[["Pizza", "Pizzas"], ["Drink", "Drinks"], ["Dessert", "Desserts"]].map(([t, l]) =>
      `<button role="tab" data-act="menu-tab" data-tab="${t}" aria-selected="${state.menuTab === t}">${l}</button>`).join("")}</div></div><div data-list></div>`;
  await guard(async () => {
    [state.menu, state.ingredients] = await Promise.all([api("/api/staff/menu"), api("/api/staff/ingredients")]);
    const pizza = state.menuTab === "Pizza";
    const rows = state.menu.filter((i) => i.type === state.menuTab).map((item) => `
      <tr><td style="width:60px"><span class="mini">${itemArt(item)}</span></td>
        <td><strong>${esc(item.name)}</strong>${item.vegan ? ` <span class="tag tag-ink">Vegan</span>` : item.vegetarian ? ` <span class="tag">Vegetarian</span>` : ""}
          ${pizza ? `<div class="sub">${esc(item.ingredients.join(", "))}</div>` : ""}</td>
        <td class="num"><strong>${money(item.price)}</strong></td>
        <td class="actions"><button class="btn btn-small" data-act="menu-edit" data-id="${item.id}">Edit</button><button class="btn btn-small" data-act="menu-delete" data-id="${item.id}">Remove</button></td></tr>`);
    $("[data-list]").innerHTML = table(["", "Item", "Price", ""], rows, `<h3>Nothing in this section</h3><p class="muted">Add a menu item to fill it.</p>`);
  });
}

function menuSheet(item) {
  const type = item?.type || state.menuTab;
  const chosen = new Set(item?.ingredient_ids || []);
  const dialog = sheet({
    title: item ? `Edit ${item.name}` : "Add menu item", wide: true,
    body: `
      ${item ? "" : `<div class="field"><span>Section</span><div class="segment">${["Pizza", "Drink", "Dessert"].map((t) => `<label><input type="radio" name="type" value="${t}" ${t === type ? "checked" : ""}>${t}</label>`).join("")}</div></div>`}
      <div class="field"><label for="m-name">Name</label><input class="input" id="m-name" name="name" value="${esc(item?.name)}" required></div>
      <div data-pizza class="builder">
        <div class="preview"><div data-art></div><div class="price" data-price></div><p class="hint" data-diet></p></div>
        <div class="field"><span>Ingredients</span><div class="picks">${state.ingredients.map((g) =>
          `<label class="pick"><input type="checkbox" name="ingredient" value="${g.id}" ${chosen.has(g.id) ? "checked" : ""}>${esc(g.name)}<small>${money(g.cost)}</small></label>`).join("")}</div></div>
      </div>
      <div data-other class="field"><label for="m-price">Price in euro</label><input class="input" id="m-price" name="price" type="number" step="0.01" min="0.01" inputmode="decimal" value="${item && item.type !== "Pizza" ? item.price : ""}"></div>`,
    onSubmit: async (data) => {
      const kind = item?.type || data.get("type");
      const body = { name: data.get("name"), type: kind, ingredient_ids: data.getAll("ingredient").map(Number), price: kind === "Pizza" ? null : Number(data.get("price")) || null };
      const saved = await api(item ? `/api/staff/menu/${item.id}` : "/api/staff/menu", { method: item ? "PUT" : "POST", body });
      toast(`${body.name} saved at ${money(saved.price)}.`);
      state.menuTab = kind;
      renderMenu();
    },
  });
  const sync = () => {
    const kind = item?.type || new FormData($("form", dialog)).get("type");
    $("[data-pizza]", dialog).classList.toggle("hidden", kind !== "Pizza");
    $("[data-other]", dialog).classList.toggle("hidden", kind === "Pizza");
    const picked = $$("[name=ingredient]:checked", dialog).map((el) => state.ingredients.find((g) => g.id === Number(el.value)));
    $("[data-art]", dialog).innerHTML = pizzaArt(picked.map((g) => g.name), item?.id || 8080);
    odo($("[data-price]", dialog), money(priceFromCost(picked.reduce((sum, g) => sum + g.cost, 0))));
    $("[data-diet]", dialog).textContent = !picked.length ? "Pick ingredients to build the pizza."
      : picked.every((g) => g.is_vegan) ? "Vegan" : picked.every((g) => g.is_vegetarian) ? "Vegetarian" : "Contains meat or fish";
  };
  dialog.addEventListener("change", sync);
  sync();
}

/* ================================================================ ingredients */

async function renderIngredients() {
  $("#view").innerHTML = head("Ingredients", "Changing a cost updates the price of every pizza that uses it.",
    `<button class="btn btn-lead" data-act="ingredient-add">Add ingredient</button>`) + `<div data-list></div>`;
  await guard(async () => {
    state.ingredients = await api("/api/staff/ingredients");
    $("[data-list]").innerHTML = table(["Ingredient", "Diet", "On pizzas", "Cost", ""], state.ingredients.map((g) => `
      <tr><td><strong>${esc(g.name)}</strong></td>
        <td>${g.is_vegan ? `<span class="tag tag-ink">Vegan</span>` : g.is_vegetarian ? `<span class="tag">Vegetarian</span>` : `<span class="tag tag-quiet">Meat or fish</span>`}</td>
        <td>${g.used_in}</td><td class="num">${money(g.cost)}</td>
        <td class="actions"><button class="btn btn-small" data-act="ingredient-edit" data-id="${g.id}">Edit</button><button class="btn btn-small" data-act="ingredient-delete" data-id="${g.id}">Remove</button></td></tr>`),
      `<h3>No ingredients yet</h3>`);
  });
}

function ingredientSheet(g) {
  sheet({
    title: g ? `Edit ${g.name}` : "Add ingredient",
    body: `
      <div class="field"><label for="g-name">Name</label><input class="input" id="g-name" name="name" value="${esc(g?.name)}" required></div>
      <div class="field"><label for="g-cost">Cost in euro</label><input class="input" id="g-cost" name="cost" type="number" step="0.01" min="0" inputmode="decimal" value="${g ? g.cost : ""}" required></div>
      <div class="row"><label class="check"><input type="checkbox" name="is_vegetarian" ${g?.is_vegetarian ? "checked" : ""}>Vegetarian</label>
        <label class="check"><input type="checkbox" name="is_vegan" ${g?.is_vegan ? "checked" : ""}>Vegan</label></div>`,
    onSubmit: async (data) => {
      if (data.get("cost") === "") throw new Error("Enter a cost.");
      const body = { name: data.get("name"), cost: Number(data.get("cost")), is_vegetarian: data.has("is_vegetarian") || data.has("is_vegan"), is_vegan: data.has("is_vegan") };
      const saved = await api(g ? `/api/staff/ingredients/${g.id}` : "/api/staff/ingredients", { method: g ? "PUT" : "POST", body });
      toast(saved.pizzas_repriced ? `Saved. ${saved.pizzas_repriced} pizza ${saved.pizzas_repriced === 1 ? "price" : "prices"} updated.` : "Saved.");
      renderIngredients();
    },
  });
}

/* ================================================================ discount codes */

const today = () => new Date().toISOString().slice(0, 10);

async function renderCodes() {
  $("#view").innerHTML = head("Discount codes", "A code works once, until its expiry date.",
    `<button class="btn btn-lead" data-act="code-add">Add code</button>`) + `<div data-list></div>`;
  await guard(async () => {
    state.codes = await api("/api/staff/codes");
    $("[data-list]").innerHTML = table(["Code", "Discount", "Expires", "Status", ""], state.codes.map((c) => {
      const expired = c.expiration_date < today();
      return `<tr><td><strong>${esc(c.code)}</strong></td><td class="num">${Number(c.discount_percentage)}%</td>
        <td>${new Date(c.expiration_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</td>
        <td><span class="tag ${c.is_used || expired ? "tag-quiet" : ""}">${c.is_used ? "Used" : expired ? "Expired" : "Open"}</span></td>
        <td class="actions"><button class="btn btn-small" data-act="code-edit" data-id="${esc(c.code)}">Edit</button><button class="btn btn-small" data-act="code-delete" data-id="${esc(c.code)}">Remove</button></td></tr>`;
    }), `<h3>No discount codes</h3><p class="muted">Add a code customers can type in their basket.</p>`);
  });
}

function codeSheet(c) {
  sheet({
    title: c ? `Edit ${c.code}` : "Add discount code",
    body: `
      <div class="field"><label for="d-code">Code</label><input class="input" id="d-code" name="code" maxlength="20" autocapitalize="characters" value="${esc(c?.code)}" ${c ? "disabled" : "required"} style="text-transform:uppercase"></div>
      <div class="grid-2">
        <div class="field"><label for="d-pct">Discount in percent</label><input class="input" id="d-pct" name="discount_percentage" type="number" min="0" max="100" step="0.01" value="${c ? Number(c.discount_percentage) : ""}" required></div>
        <div class="field"><label for="d-exp">Expires</label><input class="input" id="d-exp" name="expiration_date" type="date" value="${esc(c?.expiration_date)}" required></div>
      </div>
      ${c ? `<label class="check"><input type="checkbox" name="is_used" ${c.is_used ? "checked" : ""}>Already used</label>` : ""}`,
    onSubmit: async (data) => {
      if (data.get("discount_percentage") === "") throw new Error("Enter the discount.");
      const body = { code: c ? c.code : String(data.get("code")).trim().toUpperCase(), expiration_date: data.get("expiration_date"),
        discount_percentage: Number(data.get("discount_percentage")), is_used: data.has("is_used") };
      await api(c ? `/api/staff/codes/${encodeURIComponent(c.code)}` : "/api/staff/codes", { method: c ? "PUT" : "POST", body });
      toast("Saved.");
      renderCodes();
    },
  });
}

/* ================================================================ history and receipts */

const STATUS_LABEL = { "Pending": "In the kitchen", "Ready for Delivery": "Ready", "Out for Delivery": "Out for delivery" };
const statusTag = (status) =>
  `<span class="tag ${status === "Delivered" ? "tag-ink" : status === "Cancelled" ? "tag-quiet" : "tag-red"}">${esc(STATUS_LABEL[status] || status)}</span>`;

async function renderHistory() {
  $("#view").innerHTML = head("History", "Every order, newest first. Open one for its receipt.") + `<div data-list></div>`;
  await guard(async () => {
    const orders = await api("/api/staff/history");
    $("[data-list]").innerHTML = table(["No.", "Placed", "Customer", "How", "Status", "Total", ""], orders.map((o) => `
      <tr><td><strong>${o.order_id}</strong></td><td>${when(o.order_date)}</td><td>${esc(o.customer_name)} ${esc(o.last_name || "")}</td>
        <td>${esc(o.delivery_method)}</td><td>${statusTag(o.status)}</td><td class="num">${money(o.total_price)}</td>
        <td class="actions"><button class="btn btn-small" data-act="receipt" data-id="${o.order_id}">Receipt</button></td></tr>`),
      `<h3>No orders yet</h3>`);
  });
}

async function receipt(id) {
  await guard(async () => {
    const order = await api(`/api/staff/orders/${id}`);
    const lines = order.items.map((i) => ({ text: `${i.quantity} x ${i.name} @ ${money(i.price)}`, sum: i.quantity * i.price }));
    const listed = lines.reduce((sum, l) => sum + l.sum, 0);
    const off = Math.round((listed - order.total_price) * 100) / 100;
    const dialog = sheet({
      title: `Receipt, order ${order.order_id}`,
      body: `
        <div class="receipt">
          <div class="muted"><span>${esc(order.customer_name)} ${esc(order.last_name || "")}</span><span>${when(order.order_date)}</span></div>
          <div class="muted"><span>${esc(order.delivery_method)}, ${esc(order.status.toLowerCase())}</span><span>${esc(order.confirmation_number)}</span></div>
          <div class="rule"></div>
          ${lines.map((l) => `<div><span>${esc(l.text)}</span><span>${money(l.sum)}</span></div>`).join("")}
          <div class="rule"></div>
          ${off > 0.004 ? `<div><span>Discounts and free items</span><span>−${money(off)}</span></div>` : ""}
          <div class="sum"><span>Total</span><span>${money(order.total_price)}</span></div>
          <div class="muted"><span>Includes 9% VAT</span><span>${money(order.total_price * 9 / 109)}</span></div>
        </div>
        <button type="button" class="btn" data-save>Save receipt as a text file</button>`,
    });
    $("[data-save]", dialog).onclick = () => {
      const text = `Receipt - Order ID ${order.order_id}\n\n` + lines.map((l) => `${l.text} each = ${money(l.sum)}`).join("\n") +
        (off > 0.004 ? `\n\nDiscounts and free items: -${money(off)}` : "") + `\n\nTotal: ${money(order.total_price)}\n`;
      const link = document.createElement("a");
      link.href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
      link.download = `receipt_order_${order.order_id}.txt`;
      link.click();
      URL.revokeObjectURL(link.href);
    };
  });
}

/* ================================================================ earnings */

function lineChart(points) {
  if (!points.length) return "";
  const W = 720, H = 250, L = 46, R = 14, T = 16, B = 30;
  const times = points.map((p) => new Date(p.date).getTime());
  const t0 = Math.min(...times), t1 = Math.max(...times);
  const top = Math.max(...points.map((p) => p.earnings));
  const step = top > 400 ? 200 : top > 200 ? 100 : top > 80 ? 50 : top > 40 ? 20 : 10;
  const max = Math.ceil(top / step) * step || step;
  const x = (t) => (t1 === t0 ? (L + W - R) / 2 : L + ((t - t0) / (t1 - t0)) * (W - L - R));
  const y = (v) => T + (1 - v / max) * (H - T - B);
  const grid = [];
  for (let v = 0; v <= max; v += step) grid.push(`<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="${v ? "#E3DBCB" : "#000"}" stroke-width="${v ? 1.5 : 2.5}"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">€${v}</text>`);
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(times[i]).toFixed(1)} ${y(p.earnings).toFixed(1)}`).join("");
  const label = (t) => new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Earnings per day from ${label(t0)} to ${label(t1)}, highest ${money(top)}">
    ${grid.join("")}
    <path d="${path}" fill="none" stroke="#DA251C" stroke-width="3" stroke-linejoin="round"/>
    ${points.map((p, i) => `<circle cx="${x(times[i]).toFixed(1)}" cy="${y(p.earnings).toFixed(1)}" r="5" fill="#FFFEFB" stroke="#000" stroke-width="2.5"><title>${label(times[i])}: ${money(p.earnings)}</title></circle>`).join("")}
    <text x="${L}" y="${H - 8}">${label(t0)}</text>${t1 !== t0 ? `<text x="${W - R}" y="${H - 8}" text-anchor="end">${label(t1)}</text>` : ""}
  </svg>`;
}

async function loadEarnings() {
  const query = new URLSearchParams(Object.entries(state.report).filter(([, v]) => v !== "" && v != null));
  await guard(async () => {
    const report = await api("/api/staff/earnings?" + query);
    const count = report.records.length;
    odo($("[data-total]"), money(report.total));
    $("[data-count]").textContent = count;
    $("[data-average]").textContent = count ? money(report.total / count) : "€0.00";
    $("[data-line]").innerHTML = lineChart(report.by_date) || `<p class="muted">No orders match these filters.</p>`;
    $("[data-gender]").innerHTML = report.by_gender.sort((a, b) => b.earnings - a.earnings).map((g) => `
      <div class="bar-row"><div class="row spread"><strong>${esc(g.gender)}</strong><span>${money(g.earnings)}, ${Math.round((g.earnings / report.total) * 100)}%</span></div>
        <div class="bar"><i style="width:${(g.earnings / report.total) * 100}%"></i></div></div>`).join("") || `<p class="muted">Nothing to split.</p>`;
    $("[data-list]").innerHTML = table(["No.", "Placed", "Customer", "Gender", "Age", "Address", "Earnings"], report.records.map((r) => `
      <tr><td><strong>${r.order_id}</strong></td><td>${when(r.order_date)}</td><td>${esc(r.name)}</td><td>${esc(r.gender)}</td>
        <td class="num">${r.age ?? ""}</td><td>${esc(r.address)}</td><td class="num">${money(r.total_price)}</td></tr>`),
      `<h3>No orders match these filters</h3><p class="muted">Widen the dates or clear a filter.</p>`);
  });
}

function renderEarnings() {
  const r = state.report;
  $("#view").innerHTML = head("Earnings", "Filter by date, place, gender and age.") + `
    <form class="card filters" data-form="earnings" novalidate>
      <div class="field"><label for="e-start">From</label><input class="input" id="e-start" name="start" type="date" value="${esc(r.start)}"></div>
      <div class="field"><label for="e-end">Until</label><input class="input" id="e-end" name="end" type="date" value="${esc(r.end)}"></div>
      <div class="field"><label for="e-region">Place or postal code</label><input class="input" id="e-region" name="region" value="${esc(r.region)}"></div>
      <div class="field"><label for="e-gender">Gender</label><select class="input" id="e-gender" name="gender">${["All", "Female", "Male", "Other"].map((g) => `<option ${r.gender === g ? "selected" : ""}>${g}</option>`).join("")}</select></div>
      <div class="field"><label for="e-min">Youngest age</label><input class="input" id="e-min" name="min_age" type="number" min="0" value="${esc(r.min_age)}"></div>
      <div class="field"><label for="e-max">Oldest age</label><input class="input" id="e-max" name="max_age" type="number" min="0" value="${esc(r.max_age)}"></div>
      <button class="btn btn-lead" type="submit">Show report</button>
    </form>
    <div class="figures">
      <div class="card figure lead"><div>Earnings</div><div class="big" data-total></div></div>
      <div class="card figure"><div class="muted">Orders</div><div class="big" data-count>0</div></div>
      <div class="card figure"><div class="muted">Average order</div><div class="big" data-average></div></div>
    </div>
    <div class="charts">
      <div class="card chart"><h3>Earnings per day</h3><div data-line></div></div>
      <div class="card chart"><h3>By gender</h3><div class="stack" data-gender></div></div>
    </div>
    <div data-list></div>`;
  loadEarnings();
}

/* ================================================================ events */

app.addEventListener("click", async (event) => {
  const nav = event.target.closest(".side [data-view]");
  if (nav) return show(nav.dataset.view);
  const spot = event.target.closest(".area-map [data-area]");
  if (spot) return selectArea(spot.dataset.area, spot.dataset.pin);
  const el = event.target.closest("[data-act]");
  if (!el) return;
  const id = el.dataset.id;
  const find = (list, key) => list.find((x) => String(x[key]) === id);
  switch (el.dataset.act) {
    case "logout": await api("/api/staff/logout", { method: "POST" }); renderLogin(); break;
    case "ready": case "delivered":
      await busy(el, () => guard(async () => { await api(`/api/staff/orders/${id}/${el.dataset.act}`, { method: "POST" }); state.signature = ""; await loadBoard(); }));
      break;
    case "assign": assign(el); break;
    case "area-clear": state.area = null; paintBoard(); break;
    case "board-mode":
      state.boardMode = el.dataset.mode;
      try { localStorage.setItem("boardMode", state.boardMode); } catch { /* private window */ }
      $$("[data-act=board-mode]").forEach((b) => b.setAttribute("aria-selected", b === el));
      paintBoard();
      break;
    case "courier-add": courierSheet(); break;
    case "courier-edit": courierSheet(find(state.couriers, "delivery_person_id")); break;
    case "courier-delete": confirmDelete(find(state.couriers, "delivery_person_id").name, `/api/staff/couriers/${id}`, renderCouriers); break;
    case "menu-tab": state.menuTab = el.dataset.tab; renderMenu(); break;
    case "menu-add": menuSheet(); break;
    case "menu-edit": menuSheet(find(state.menu, "id")); break;
    case "menu-delete": confirmDelete(find(state.menu, "id").name, `/api/staff/menu/${id}`, renderMenu); break;
    case "ingredient-add": ingredientSheet(); break;
    case "ingredient-edit": ingredientSheet(find(state.ingredients, "id")); break;
    case "ingredient-delete": confirmDelete(find(state.ingredients, "id").name, `/api/staff/ingredients/${id}`, renderIngredients); break;
    case "code-add": codeSheet(); break;
    case "code-edit": codeSheet(find(state.codes, "code")); break;
    case "code-delete": confirmDelete(`code ${id}`, `/api/staff/codes/${encodeURIComponent(id)}`, renderCodes); break;
    case "receipt": receipt(id); break;
  }
});

app.addEventListener("keydown", (event) => {
  const spot = event.target.closest?.(".area-map [data-area]");
  if (spot && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); selectArea(spot.dataset.area, spot.dataset.pin); }
});
const linkPin = (event, on) => {
  const card = event.target.closest?.(".map-list .ticket");
  if (card) $(`[data-pin="${card.dataset.order}"]`)?.classList.toggle("hot", on);
};
app.addEventListener("mouseover", (event) => linkPin(event, true));
app.addEventListener("mouseout", (event) => linkPin(event, false));

app.addEventListener("submit", (event) => {
  if (event.target.dataset.form !== "earnings") return;
  event.preventDefault();
  state.report = Object.fromEntries(new FormData(event.target));
  loadEarnings();
});

start();
