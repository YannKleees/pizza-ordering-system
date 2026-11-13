/* Vibe coded: this web interface was written with an AI assistant in 2026.
   The delivery map on the staff pages. It is a drawing, not a street map: the database only
   knows the four-digit postal code of an address, so the map shows Maastricht's postal areas
   placed roughly where they lie around the river, with the open orders and the couriers on them.
   Nothing is sent to a map service. */
import { esc } from "./ui.js";
import { pizzaArt } from "./pizza-art.js";

const INK = "#000", TOMATO = "#DA251C", FLOUR = "#FFFEFB", DEEP = "#CFC5B1", SOFT = "#5B5549", WATER = "#E3DBCB";

// west of the Maas: 6211 to 6219, east of it: 6221 to 6229
export const AREAS = {
  6211: [262, 250], 6212: [258, 345], 6213: [160, 372], 6214: [140, 268], 6215: [66, 196],
  6216: [186, 170], 6217: [118, 92], 6218: [42, 82], 6219: [252, 78],
  6221: [410, 250], 6222: [420, 118], 6223: [452, 34], 6224: [496, 192], 6225: [580, 128],
  6226: [512, 296], 6227: [588, 360], 6228: [540, 440], 6229: [424, 392],
};
const SHOP = [318, 292];

const PIN = {
  "Pending": { fill: FLOUR, text: INK, label: "in the kitchen" },
  "Ready for Delivery": { fill: TOMATO, text: "#fff", label: "ready" },
  "Out for Delivery": { fill: INK, text: "#fff", label: "on its way" },
};

export const onMap = (code) => Object.hasOwn(AREAS, code);

export function areaMap({ orders, couriers, selected }) {
  const deliveries = orders.filter((o) => o.delivery_method === "Delivery");
  let routes = "", nodes = "", pins = "";

  for (const [code, [x, y]] of Object.entries(AREAS)) {
    const here = deliveries.filter((o) => o.postal_code === code);
    const crew = couriers.filter((c) => c.assigned_postal_code === code);
    const active = here.length || crew.length;
    const chosen = selected === code;

    if (here.some((o) => o.status === "Out for Delivery")) {
      const bend = x < SHOP[0] ? -26 : 26;
      routes += `<path class="route" d="M${SHOP[0]} ${SHOP[1]} Q${(SHOP[0] + x) / 2 + bend} ${(SHOP[1] + y) / 2 - 22} ${x} ${y}" fill="none" stroke="${TOMATO}" stroke-width="4" stroke-linecap="round" stroke-dasharray="1 10"/>`;
    }

    const crewText = crew.map((c) => `${c.availability ? "●" : "○"} ${esc(c.name.split(" ")[0])}`).join("  ");
    const summary = [
      here.length ? `${here.length} ${here.length === 1 ? "order" : "orders"}` : "no orders",
      ...crew.map((c) => `courier ${c.name} ${c.availability ? "available" : "out"}`),
    ].join(", ");
    nodes += `
      <g class="area ${active ? "is-active" : ""} ${chosen ? "is-chosen" : ""}" data-area="${code}" role="button" tabindex="0" aria-pressed="${chosen}" aria-label="Area ${code}: ${esc(summary)}">
        ${active ? `<circle cx="${x + 4}" cy="${y + 4}" r="30" fill="${INK}"/>` : ""}
        <circle cx="${x}" cy="${y}" r="30" fill="${active ? FLOUR : "none"}" stroke="${chosen ? TOMATO : active ? INK : DEEP}" stroke-width="${chosen ? 5 : 2.5}" ${active ? "" : 'stroke-dasharray="5 5"'}/>
        <text x="${x}" y="${y + (crewText ? -1 : 5)}" text-anchor="middle" font-size="15.5" font-weight="800" fill="${active ? INK : SOFT}">${code}</text>
        ${crewText ? `<text x="${x}" y="${y + 15}" text-anchor="middle" font-size="10.5" font-weight="700" fill="${SOFT}">${crewText}</text>` : ""}
      </g>`;

    const shown = here.slice(0, 4);
    shown.forEach((order, i) => {
      const angle = (-90 + (i - (shown.length - 1) / 2) * 42) * Math.PI / 180;
      const px = x + Math.cos(angle) * 48, py = y + Math.sin(angle) * 48;
      const style = PIN[order.status] || PIN.Pending;
      pins += `
        <g class="pin" data-pin="${order.order_id}" data-area="${code}" role="button" tabindex="0" aria-label="Order ${order.order_id}, ${style.label}, ${esc(order.customer_name)}">
          <circle cx="${px + 2.5}" cy="${py + 2.5}" r="14" fill="${INK}"/>
          <circle cx="${px}" cy="${py}" r="14" fill="${style.fill}" stroke="${INK}" stroke-width="2.5"/>
          <text x="${px}" y="${py + 4.5}" text-anchor="middle" font-size="12" font-weight="800" fill="${style.text}">${order.order_id}</text>
        </g>`;
    });
    if (here.length > shown.length) {
      pins += `<text x="${x + 38}" y="${y + 6}" font-size="12" font-weight="800" fill="${INK}">+${here.length - shown.length}</text>`;
    }
  }

  return `
    <svg class="area-map" viewBox="0 0 640 480" role="group" aria-label="Map of delivery areas with open orders and couriers">
      <defs><pattern id="map-dots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="4.5" cy="4.5" r="1.3" fill="${INK}" opacity=".16"/></pattern></defs>
      <rect width="640" height="480" fill="url(#map-dots)" opacity=".55"/>
      <path d="M352 480 C332 410 366 340 340 262 S300 150 344 84 S392 24 396 0" fill="none" stroke="${INK}" stroke-width="35" stroke-linecap="round"/>
      <path d="M352 480 C332 410 366 340 340 262 S300 150 344 84 S392 24 396 0" fill="none" stroke="${WATER}" stroke-width="29" stroke-linecap="round"/>
      <path d="M318 246h46M322 276h44" stroke="${INK}" stroke-width="7"/>
      <path d="M318 246h46M322 276h44" stroke="${FLOUR}" stroke-width="2.5"/>
      <text x="356" y="444" font-size="12" font-weight="800" fill="${SOFT}" transform="rotate(-76 356 444)" letter-spacing="2">Maas</text>
      ${routes}
      ${nodes}
      <g aria-label="The shop">
        <svg x="${SHOP[0] - 20}" y="${SHOP[1] - 20}" width="40" height="40" viewBox="0 0 200 200">${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni"], 31).replace(/^<svg[^>]*>|<\/svg>$/g, "")}</svg>
        <text x="${SHOP[0]}" y="${SHOP[1] + 34}" text-anchor="middle" font-size="11.5" font-weight="800" fill="${INK}">Shop</text>
      </g>
      ${pins}
    </svg>`;
}
