/* Vibe coded: this web interface was written with an AI assistant in 2026.
   Small helpers shared by the shop and the staff pages. */
import { pizzaArt } from "./pizza-art.js";

export const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const money = (value) => "€" + Number(value || 0).toFixed(2);

export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

export async function api(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(path, {
      method, credentials: "same-origin",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("The server is not answering. Check that it is still running.", 0);
  }
  if (!response.ok) {
    let message = "Something went wrong. Try again.";
    try {
      const detail = (await response.json()).detail;
      if (typeof detail === "string") message = detail;
    } catch { /* keep the default */ }
    throw new ApiError(message, response.status);
  }
  return response.json();
}

/* ---------- toast */
export function toast(message, { error = false } = {}) {
  let host = $(".toasts");
  if (!host) {
    host = document.createElement("div");
    host.className = "toasts";
    host.setAttribute("aria-live", "polite");
    document.body.append(host);
  }
  const el = document.createElement("div");
  el.className = "toast" + (error ? " is-error" : "");
  el.textContent = message;
  host.append(el);
  setTimeout(() => {
    el.classList.add("is-leaving");
    setTimeout(() => el.remove(), 200);
  }, error ? 5000 : 2800);
}

/* ---------- a button that shows it is working and cannot be pressed twice */
export async function busy(button, work) {
  if (!button || button.classList.contains("is-busy")) return;
  const label = button.innerHTML;
  button.classList.add("is-busy");
  button.disabled = true;
  button.innerHTML = `<span class="spinner" aria-hidden="true"></span><span class="sr-only">Working</span>`;
  try {
    return await work();
  } finally {
    button.classList.remove("is-busy");
    button.disabled = false;
    if (button.isConnected) button.innerHTML = label;
  }
}

/* ---------- rolling numbers: each digit turns on its own reel */
export function odo(el, text) {
  text = String(text);
  if (!el) return;
  const reels = $$(".odo-col", el);
  const same = el.dataset.shape === text.replace(/\d/g, "0");
  if (!same) {
    el.dataset.shape = text.replace(/\d/g, "0");
    el.classList.add("odo");
    el.innerHTML = [...text].map((ch) =>
      /\d/.test(ch)
        ? `<span class="odo-col" aria-hidden="true"><span class="odo-reel" style="transform:translateY(-${ch * 1.15}em)">${"0123456789".split("").map((d) => `<span>${d}</span>`).join("")}</span></span>`
        : `<span aria-hidden="true">${esc(ch)}</span>`).join("") + `<span class="sr-only">${esc(text)}</span>`;
    return;
  }
  const digits = text.replace(/\D/g, "");
  reels.forEach((col, i) => { col.firstElementChild.style.transform = `translateY(-${digits[i] * 1.15}em)`; });
  $(".sr-only", el).textContent = text;
}

/* ---------- dialog */
export function sheet({ title, body, action = "Save", danger = false, onSubmit, wide = false }) {
  const dialog = document.createElement("dialog");
  dialog.className = "sheet";
  if (wide) dialog.style.width = "min(94vw, 760px)";
  dialog.innerHTML = `
    <form method="dialog" novalidate>
      <div class="sheet-head"><h2>${esc(title)}</h2><button type="button" class="icon-btn" data-close aria-label="Close">×</button></div>
      <div class="sheet-body">${body}<p class="error" role="alert"></p></div>
      <div class="sheet-foot">
        <button type="button" class="btn" data-close>${onSubmit ? "Cancel" : "Close"}</button>
        ${onSubmit ? `<button type="submit" class="btn ${danger ? "btn-danger" : "btn-lead"}">${esc(action)}</button>` : ""}
      </div>
    </form>`;
  document.body.append(dialog);
  const close = () => { dialog.close(); dialog.remove(); };
  dialog.addEventListener("click", (event) => {
    if (event.target.closest("[data-close]") || event.target === dialog) close();
  });
  dialog.addEventListener("cancel", (event) => { event.preventDefault(); close(); });
  $("form", dialog).addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!onSubmit) return close();
    const error = $(".error", dialog);
    error.textContent = "";
    await busy($("[type=submit]", dialog), async () => {
      try {
        await onSubmit(new FormData(event.target), dialog);
        close();
      } catch (err) {
        error.textContent = err.message;
      }
    });
  });
  dialog.showModal();
  return dialog;
}

/* ---------- password field: show or hide, and warn about Caps Lock */
export function passwordField({ id, label, autocomplete, extra = "" }) {
  return `
    <div class="field">
      <div class="label-row"><label for="${id}">${label}</label><span class="caps hidden" data-caps>Caps Lock is on</span></div>
      <div class="input-wrap">
        <input class="input" id="${id}" name="password" type="password" autocomplete="${autocomplete}" required ${extra}>
        <button type="button" class="btn-plain" data-reveal aria-controls="${id}" aria-pressed="false">Show</button>
      </div>
    </div>`;
}

export function wirePassword(root) {
  root.addEventListener("click", (event) => {
    const button = event.target.closest("[data-reveal]");
    if (!button) return;
    const input = document.getElementById(button.getAttribute("aria-controls"));
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.textContent = show ? "Hide" : "Show";
    button.setAttribute("aria-pressed", String(show));
    input.focus();
  });
  const caps = (event) => {
    if (event.target.name !== "password" || !event.getModifierState) return;
    const note = event.target.closest(".field")?.querySelector("[data-caps]");
    note?.classList.toggle("hidden", !event.getModifierState("CapsLock"));
  };
  root.addEventListener("keydown", caps);
  root.addEventListener("keyup", caps);
}

export function shake(el) {
  el.classList.remove("shake");
  void el.offsetWidth;
  el.classList.add("shake");
}

/* ---------- the shop name, with a pizza for the o */
export const wordmark = (suffix = "") =>
  `<span class="wordmark" aria-label="Pop Pizza${suffix ? " " + suffix : ""}">P${pizzaArt(["Tomato Sauce", "Mozzarella", "Pepperoni"], 9001)}p Pizza${suffix ? `<small>${suffix}</small>` : ""}</span>`;

export const when = (iso) => {
  const date = new Date(iso);
  const today = new Date();
  const time = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  if (date.toDateString() === today.toDateString()) return `Today, ${time}`;
  return `${date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: date.getFullYear() === today.getFullYear() ? undefined : "numeric" })}, ${time}`;
};
