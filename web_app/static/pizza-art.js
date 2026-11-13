/* Vibe coded: this web interface was written with an AI assistant in 2026.
   Draws every menu item from its data. A pizza is built from the ingredient list stored in the
   database, in a flat print style: tomato red, a quiet leaf green for vegetables and black line,
   on dough colours. The same pizza always looks the same. */

const INK = "#000";
const TOMATO = "#DA251C";
const TOMATO_DEEP = "#8E1A12";
const TOMATO_TINT = "#F29C8E";
const LEAF = "#3F6B3A"; // the one colour outside the palette, used only inside the drawings
const LEAF_TINT = "#CBD9B8";
const WATER = "#E6E1D6";
const FLOUR = "#FFFEFB";
const CHEESE = "#FFF1BF";
const GOLD = "#E3B04B";

function rng(seed) {
  let a = (seed * 2654435761) >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const SAUCES = { "tomato sauce": TOMATO, "bbq sauce": TOMATO_DEEP, "buffalo sauce": "#EE4B2B" };
const CHEESES = ["mozzarella", "cheddar cheese", "vegan cheese"];

const ring = (r, colour) =>
  `<circle r="${r}" fill="none" stroke="${INK}" stroke-width="5.4"/><circle r="${r}" fill="none" stroke="${colour}" stroke-width="2.6"/>`;
const disc = (r, fill) =>
  `<circle r="${r}" fill="${fill}" stroke="${INK}" stroke-width="1.8"/><circle cx="${-r / 3}" cy="${-r / 4}" r="1.3" fill="${INK}" opacity=".55"/><circle cx="${r / 3}" cy="${r / 3}" r="1.1" fill="${INK}" opacity=".55"/>`;
const strip = (fill, stripe) =>
  `<rect x="-10" y="-4" width="20" height="8" rx="3" fill="${fill}" stroke="${INK}" stroke-width="1.8"/>${stripe ? `<path d="M-6 0h12" stroke="${FLOUR}" stroke-width="1.6" stroke-linecap="round"/>` : ""}`;
const chunk = (fill) =>
  `<path d="M-6-5 5-6 7 3 0 7-7 4Z" fill="${fill}" stroke="${INK}" stroke-width="1.8" stroke-linejoin="round"/>`;
const crescent = (fill) =>
  `<path d="M-8 2a8 8 0 0 1 16 0 5 5 0 0 0-5-1 4 4 0 0 1-6 0 5 5 0 0 0-5 1Z" fill="${fill}" stroke="${INK}" stroke-width="1.8" stroke-linejoin="round"/>`;

// name -> [shape, pieces on a pizza]
const TOPPINGS = {
  "pepperoni": [disc(8.5, TOMATO), 7],
  "sausage": [disc(6.5, TOMATO_DEEP), 7],
  "italian sausage": [disc(7, TOMATO_DEEP), 7],
  "bacon": [strip(TOMATO_TINT, true), 6],
  "ham": [strip(TOMATO_TINT, false), 6],
  "pulled pork": [strip(TOMATO_DEEP, false), 6],
  "chicken": [chunk(FLOUR), 6],
  "pineapple": [chunk(GOLD), 6],
  "feta cheese": [chunk("#fff"), 6],
  "artichokes": [chunk(LEAF_TINT), 5],
  "onions": [ring(6, FLOUR), 6],
  "red onions": [ring(6.5, LEAF), 6],
  "green peppers": [ring(5.5, LEAF), 6],
  "jalapenos": [ring(4, LEAF), 7],
  "red peppers": [ring(5.5, TOMATO), 6],
  "black olives": [`<circle r="4.2" fill="none" stroke="${INK}" stroke-width="3.6"/>`, 8],
  "kalamata olives": [`<circle r="4.6" fill="${LEAF}" stroke="${INK}" stroke-width="3"/>`, 7],
  "mushrooms": [`<path d="M-8 0a8 7 0 0 1 16 0Zm5 0h6v5a3 3 0 0 1-6 0Z" fill="${FLOUR}" stroke="${INK}" stroke-width="1.8" stroke-linejoin="round"/>`, 6],
  "spinach": [`<path d="M-9 0Q0-9 9 0 0 9-9 0Z" fill="${LEAF}" stroke="${INK}" stroke-width="1.8" stroke-linejoin="round"/><path d="M-6 0H6" stroke="${LEAF_TINT}" stroke-width="1.2"/>`, 6],
  "shrimp": [crescent(TOMATO_TINT), 5],
  "clams": [crescent(FLOUR), 5],
  "garlic": [`<circle r="2.6" fill="${FLOUR}" stroke="${INK}" stroke-width="1.5"/>`, 9],
};

function scatter(random, count, taken, minGap, maxRadius) {
  const points = [];
  for (let tries = 0; points.length < count && tries < count * 40; tries++) {
    const angle = random() * Math.PI * 2;
    const radius = Math.sqrt(random()) * maxRadius;
    const x = 100 + Math.cos(angle) * radius;
    const y = 100 + Math.sin(angle) * radius;
    if (taken.every((p) => (p.x - x) ** 2 + (p.y - y) ** 2 > minGap ** 2)) {
      const point = { x, y, turn: Math.round(random() * 360) };
      taken.push(point);
      points.push(point);
    }
  }
  return points;
}

function cheeseBlob(random) {
  const steps = 14;
  const at = (i) => {
    const angle = (i / steps) * Math.PI * 2;
    const radius = 66 + random() * 7;
    return [100 + Math.cos(angle) * radius, 100 + Math.sin(angle) * radius];
  };
  const points = Array.from({ length: steps }, (_, i) => at(i));
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const start = mid(points[0], points[1]);
  let d = `M${start[0].toFixed(1)} ${start[1].toFixed(1)}`;
  for (let i = 1; i <= steps; i++) {
    const p = points[i % steps];
    const m = mid(p, points[(i + 1) % steps]);
    d += `Q${p[0].toFixed(1)} ${p[1].toFixed(1)} ${m[0].toFixed(1)} ${m[1].toFixed(1)}`;
  }
  return d + "Z";
}

export function pizzaArt(ingredients, seed = 1) {
  const names = ingredients.map((n) => n.toLowerCase());
  const random = rng(seed + 7);
  const sauceName = names.find((n) => SAUCES[n]);
  const sauce = sauceName ? SAUCES[sauceName] : "#F1DDA6";
  const hasCheese = names.some((n) => CHEESES.includes(n));
  const cheeseFill = names.includes("cheddar cheese") && !names.includes("mozzarella") ? GOLD : CHEESE;
  let toppings = names.filter((n) => TOPPINGS[n]);
  if (!toppings.length && hasCheese) toppings = ["spinach"]; // a plain margherita gets its basil leaves
  const share = toppings.length > 3 ? 0.62 : toppings.length > 1 ? 0.8 : 1;

  const taken = [];
  let pieces = "";
  toppings.forEach((name) => {
    const [shape, count] = TOPPINGS[name];
    scatter(random, Math.max(4, Math.round(count * share * 1.25)), taken, 18, 54).forEach((p) => {
      pieces += `<g transform="translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) rotate(${p.turn}) scale(1.3)">${shape}</g>`;
    });
  });

  const id = `p${seed}`;
  return `<svg viewBox="0 0 200 200" role="img" aria-label="Drawing of a pizza with ${ingredients.join(", ").toLowerCase() || "nothing on it yet"}">
  <defs>
    <pattern id="${id}d" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><circle cx="3.5" cy="3.5" r="1.25" fill="${INK}"/></pattern>
    <clipPath id="${id}c"><circle cx="100" cy="100" r="77"/></clipPath>
  </defs>
  <circle cx="106" cy="107" r="90" fill="${INK}"/>
  <circle cx="100" cy="100" r="90" fill="${GOLD}" stroke="${INK}" stroke-width="3"/>
  <circle cx="100" cy="100" r="77" fill="${sauce}" stroke="${INK}" stroke-width="2"/>
  ${hasCheese ? `<path d="${cheeseBlob(random)}" fill="${cheeseFill}" stroke="${INK}" stroke-width="1.8"/>` : ""}
  <path d="M100 100 L200 60 L200 200 L60 200 Z" fill="url(#${id}d)" opacity=".13" clip-path="url(#${id}c)"/>
  ${pieces}
</svg>`;
}

const CAN = (body, band) => `<svg viewBox="0 0 200 200" role="img" aria-label="Drawing of a drink can">
  <rect x="72" y="42" width="68" height="128" rx="12" fill="${INK}"/>
  <rect x="66" y="36" width="68" height="128" rx="12" fill="${body}" stroke="${INK}" stroke-width="3"/>
  <rect x="66" y="78" width="68" height="40" fill="${band}" stroke="${INK}" stroke-width="3"/>
  <path d="M78 36h44M78 164h44" stroke="${INK}" stroke-width="3"/>
  <ellipse cx="108" cy="30" rx="9" ry="4" fill="${FLOUR}" stroke="${INK}" stroke-width="2.4"/>
</svg>`;

const BOTTLE = (body) => `<svg viewBox="0 0 200 200" role="img" aria-label="Drawing of a bottle">
  <path d="M92 26h28v24c0 10 14 16 14 34v80a10 10 0 0 1-10 10H88a10 10 0 0 1-10-10V84c0-18 14-24 14-34Z" fill="${INK}" transform="translate(6 6)"/>
  <path d="M86 20h28v24c0 10 14 16 14 34v80a10 10 0 0 1-10 10H82a10 10 0 0 1-10-10V78c0-18 14-24 14-34Z" fill="${body}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>
  <rect x="84" y="14" width="32" height="12" rx="3" fill="${TOMATO}" stroke="${INK}" stroke-width="3"/>
  <rect x="72" y="96" width="56" height="34" fill="${FLOUR}" stroke="${INK}" stroke-width="3"/>
</svg>`;

const SLICE = (sponge, cream, top) => `<svg viewBox="0 0 200 200" role="img" aria-label="Drawing of a slice of cake">
  <path d="M36 150 164 150 164 84 36 112Z" fill="${INK}" transform="translate(7 7)"/>
  <path d="M36 150 164 150 164 84 36 112Z" fill="${sponge}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>
  <path d="M36 126 164 112" stroke="${cream}" stroke-width="9"/>
  <path d="M36 112 164 84 164 96 36 122Z" fill="${top}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>
  <circle cx="142" cy="78" r="9" fill="${TOMATO}" stroke="${INK}" stroke-width="3"/>
</svg>`;

const CONE = (one, two) => `<svg viewBox="0 0 200 200" role="img" aria-label="Drawing of an ice cream cone">
  <path d="M74 104h64l-32 78Z" fill="${INK}"/>
  <path d="M68 98h64l-32 78Z" fill="${GOLD}" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>
  <path d="M78 122l44-24M88 146l34-34M76 100l28 28" stroke="${INK}" stroke-width="1.6" opacity=".5"/>
  <circle cx="84" cy="76" r="26" fill="${one}" stroke="${INK}" stroke-width="3"/>
  <circle cx="118" cy="72" r="26" fill="${two}" stroke="${INK}" stroke-width="3"/>
</svg>`;

export function itemArt(item) {
  if (item.type === "Pizza") return pizzaArt(item.ingredients || [], item.id);
  const name = item.name.toLowerCase();
  if (item.type === "Drink") {
    if (/water|juice|tea|lemonade/.test(name)) return BOTTLE(/water/.test(name) ? WATER : GOLD);
    if (/sprite/.test(name)) return CAN(LEAF_TINT, LEAF);
    if (/fanta|root/.test(name)) return CAN(GOLD, FLOUR);
    return CAN(TOMATO, FLOUR);
  }
  if (/gelato|ice/.test(name)) return CONE(TOMATO_TINT, FLOUR);
  if (/cheesecake|tart|panna/.test(name)) return SLICE(CHEESE, FLOUR, GOLD);
  if (/tiramisu/.test(name)) return SLICE(GOLD, FLOUR, TOMATO_DEEP);
  return SLICE(TOMATO_DEEP, FLOUR, "#5A120C");
}
