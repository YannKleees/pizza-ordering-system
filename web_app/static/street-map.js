/* Vibe coded: this web interface was written with an AI assistant in 2026.
   The delivery map on the staff pages: a real street map (Leaflet with OpenStreetMap tiles)
   with a pin for every open delivery. The server works out where an address is
   (see geo.py); this file only draws. */
import { esc } from "./ui.js";
import { pizzaArt } from "./pizza-art.js";

const L = window.L;
const STYLE = {
  "Pending": ["kitchen", "In the kitchen"],
  "Ready for Delivery": ["ready", "Ready, waiting for a courier"],
  "Out for Delivery": ["out", "On its way"],
};

export function createStreetMap(element, shop, onPick) {
  const map = L.map(element, { scrollWheelZoom: true }).setView([shop.lat, shop.lng], 13);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  const shopIcon = L.divIcon({
    className: "map-shop", iconSize: [46, 46], iconAnchor: [23, 23],
    html: pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni"], 31),
  });
  L.marker([shop.lat, shop.lng], { icon: shopIcon, zIndexOffset: 500, title: "The shop" })
    .addTo(map).bindPopup("<strong>Pop Pizza</strong><br>The shop. Couriers leave from here.");
  setTimeout(() => map.invalidateSize(), 60);
  return { map, shop, onPick, layer: L.layerGroup().addTo(map), markers: new Map(), shown: null };
}

export function updateStreetMap(view, deliveries) {
  view.layer.clearLayers();
  view.markers.clear();
  const points = [[view.shop.lat, view.shop.lng]];
  const taken = new Map();
  for (const order of deliveries) {
    if (order.lat == null) continue;
    // orders to the same door would hide each other, so later ones step a little to the east
    const spot = `${order.lat},${order.lng}`;
    const nth = taken.get(spot) || 0;
    taken.set(spot, nth + 1);
    const position = [order.lat, order.lng + nth * 0.0006];
    points.push(position);
    const [style, label] = STYLE[order.status] || STYLE.Pending;

    if (order.status === "Out for Delivery") {
      L.polyline([[view.shop.lat, view.shop.lng], position], {
        color: "#141414", weight: 4, opacity: 0.9, dashArray: "2 14", lineCap: "round", className: "map-route", interactive: false,
      }).addTo(view.layer);
    }
    const marker = L.marker(position, {
      title: `Order ${order.order_id}, ${label.toLowerCase()}`,
      icon: L.divIcon({
        className: "map-pin", iconSize: [34, 34], iconAnchor: [17, 41], popupAnchor: [0, -40],
        html: `<span class="${style}${order.exact ? "" : " rough"}" data-pin="${order.order_id}"><b>${order.order_id}</b></span>`,
      }),
    }).addTo(view.layer);
    marker.bindPopup(`
      <strong>No. ${order.order_id}, ${esc(order.customer_name)} ${esc(order.last_name || "")}</strong><br>
      ${esc(order.address)}<br>
      ${order.items.map((i) => `${i.quantity} × ${esc(i.name)}`).join(", ")}<br>
      <em>${label}${order.delivery_person_name ? ` with ${esc(order.delivery_person_name)}` : ""}</em>
      ${order.exact ? "" : "<br>Placed in the middle of the postal area; the exact address is not known yet."}`);
    marker.on("click", () => view.onPick(order.order_id));
    view.markers.set(order.order_id, marker);
  }
  // move the view only when the set of orders changed, so it never fights the person using the map
  const shown = [...view.markers.keys()].sort().join(",") + points.length;
  if (shown !== view.shown) {
    view.shown = shown;
    points.length > 1 ? view.map.fitBounds(points, { padding: [60, 60], maxZoom: 15 }) : view.map.setView(points[0], 14);
  }
}

export function focusPin(view, orderId) {
  const marker = view?.markers.get(Number(orderId));
  if (!marker) return;
  view.map.flyTo(marker.getLatLng(), Math.max(view.map.getZoom(), 15), { duration: 0.6 });
  marker.openPopup();
}
