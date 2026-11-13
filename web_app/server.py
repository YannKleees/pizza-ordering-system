# Vibe coded: this web interface was written with an AI assistant in 2026.
"""
Web interface for the pizza ordering system.

This file only translates between the browser and the original 2024 code: logging in, the menu,
the basket, prices, discounts, loyalty and orders all go through the classes in customer_app
(Auth, Customer, Menu, Basket, OrderManager). The staff pages are in staff_api.py.
"""
import datetime
import queue
import secrets
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from customer_app.auth import Auth
from customer_app.basket import Basket
from customer_app.customer import Customer
from customer_app.database import DatabaseConnection
from customer_app.menu import Menu
from customer_app.order import OrderManager

STATIC = Path(__file__).parent / "static"
CANCEL_WINDOW_SECONDS = 300  # same five minutes as the desktop app
GENDERS = ("Male", "Female", "Other")

app = FastAPI(title="Pizza ordering system", docs_url=None, redoc_url=None)


# ---------------------------------------------------------------- sessions and database

class Session:
    """What the desktop app kept in memory per window: who is logged in and their basket."""

    def __init__(self):
        self.customer_id = None
        self.staff_id = None
        self.basket = Basket()


SESSIONS: dict[str, Session] = {}


def get_session(sid: str | None, response: Response) -> Session:
    if sid and sid in SESSIONS:
        return SESSIONS[sid]
    sid = secrets.token_urlsafe(24)
    SESSIONS[sid] = Session()
    response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return SESSIONS[sid]


def require_customer(sid: str | None, response: Response) -> Session:
    session = get_session(sid, response)
    if session.customer_id is None:
        raise HTTPException(401, "Please log in.")
    return session


POOL: "queue.LifoQueue[DatabaseConnection]" = queue.LifoQueue()


@contextmanager
def database():
    """
    Hand out a database connection. Opening one can take seconds (on Windows 'localhost' is tried
    over IPv6 first), so connections are kept and reused instead of opened for every click.
    """
    db = None
    try:
        db = POOL.get_nowait()
        db.connection.ping(reconnect=True, attempts=1)
        db.cursor = db.connection.cursor(dictionary=True, buffered=True)
    except queue.Empty:
        db = None
    except Exception:
        db = None
    if db is None:
        db = DatabaseConnection()
        try:
            db.connect()
        except Exception:
            raise HTTPException(503, "The database is not reachable. Check that MySQL is running and the DB_ settings are right.")
    try:
        yield db
    finally:
        try:
            db.connection.rollback()  # ends the read snapshot, so the next request sees fresh data
            db.cursor.close()
            POOL.put(db)
        except Exception:
            pass


def plain(value):
    """Make database values safe for JSON."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


# ---------------------------------------------------------------- account

class Login(BaseModel):
    username: str
    password: str


class Registration(BaseModel):
    name: str
    last_name: str
    gender: str
    birthdate: str
    phone_number: str
    address: str
    username: str
    password: str


class Profile(BaseModel):
    name: str
    last_name: str
    gender: str
    birthdate: str
    phone_number: str
    address: str


def check_person(details: dict):
    """The same checks the desktop app runs before saving a customer."""
    if not all(str(v).strip() for v in details.values()):
        raise HTTPException(422, "Fill in every field.")
    try:
        datetime.datetime.strptime(details["birthdate"], "%Y-%m-%d")
    except ValueError:
        raise HTTPException(422, "The birthdate is not a valid date.")
    if details["gender"].capitalize() not in GENDERS:
        raise HTTPException(422, "Choose Male, Female or Other.")
    details["gender"] = details["gender"].capitalize()


def is_birthday(birthdate) -> bool:
    today = datetime.date.today()
    return bool(birthdate) and (today.month, today.day) == (birthdate.month, birthdate.day)


def days_until_birthday(birthdate):
    if not birthdate:
        return None
    today = datetime.date.today()
    try:
        upcoming = birthdate.replace(year=today.year)
        if upcoming < today:
            upcoming = birthdate.replace(year=today.year + 1)
    except ValueError:  # 29 February
        return None
    return (upcoming - today).days


def fetch_customer(db, customer_id):
    cursor = db.execute_query(
        "SELECT name, last_name, username, gender, birthdate, phone_number, address, pizzas_ordered "
        "FROM customer WHERE customer_id = %s", (customer_id,))
    return cursor.fetchone()


@app.post("/api/login")
def login(body: Login, response: Response, sid: str | None = Cookie(None)):
    session = get_session(sid, response)
    username, password = body.username.strip(), body.password.strip()
    if not username or not password:
        raise HTTPException(422, "Enter your username and password.")
    with database() as db:
        result = Auth(db).verify_login(username, password)
    if not result["success"]:
        raise HTTPException(401, "Username or password didn't match.")
    session.customer_id = result["customer_id"]
    session.basket = Basket()
    return {"ok": True}


@app.post("/api/register")
def register(body: Registration):
    details = {k: v.strip() for k, v in body.model_dump().items()}
    check_person(details)
    with database() as db:
        result = Auth(db).register_user(details)
    if not result["success"]:
        raise HTTPException(409, result.get("message", "Registration failed."))
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response, sid: str | None = Cookie(None)):
    if sid:
        SESSIONS.pop(sid, None)
    response.delete_cookie("sid")
    return {"ok": True}


@app.get("/api/me")
def me(response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    with database() as db:
        customer = fetch_customer(db, session.customer_id)
    if not customer:
        raise HTTPException(401, "Please log in.")
    return plain({
        **customer,
        "stamps": (customer["pizzas_ordered"] or 0) % 10,
        "is_birthday": is_birthday(customer["birthdate"]),
        "days_until_birthday": days_until_birthday(customer["birthdate"]),
    })


@app.put("/api/me")
def update_me(body: Profile, response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    details = {k: v.strip() for k, v in body.model_dump().items()}
    check_person(details)
    with database() as db:
        result = Customer(db).update_customer(session.customer_id, details)
    if not result["success"]:
        raise HTTPException(500, result["message"])
    return {"ok": True}


# ---------------------------------------------------------------- menu and basket

def load_menu(db) -> dict:
    menu = Menu(db)
    menu.fetch_menu()
    return menu.menu


@app.get("/api/menu")
def menu(response: Response, sid: str | None = Cookie(None)):
    require_customer(sid, response)
    with database() as db:
        items = load_menu(db)
    return [
        {
            "id": item_id, "name": d["name"], "type": d["type"], "price": d["price"],
            "ingredients": d["ingredients"],
            "vegetarian": bool(d["is_vegetarian"]), "vegan": bool(d["is_vegan"]),
        }
        for item_id, d in items.items()
    ]


def basket_view(basket: Basket, birthday: bool = False) -> dict:
    totals = basket.calculate_total_price()
    return plain({
        "items": basket.items,
        "count": sum(item["quantity"] for item in basket.items),
        "subtotal": totals["subtotal"],
        "discount": basket.discount_amount,
        "discount_code": basket.discount_code,
        "total": totals["grand_total"],
        "vat": totals["vat_amount"],
        "birthday": birthday,
    })


def customer_has_birthday(db, customer_id) -> bool:
    cursor = db.execute_query("SELECT birthdate FROM customer WHERE customer_id = %s", (customer_id,))
    row = cursor.fetchone()
    return bool(row) and is_birthday(row["birthdate"])


class BasketLine(BaseModel):
    id: int
    quantity: int


class Code(BaseModel):
    code: str


@app.get("/api/basket")
def get_basket(response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    with database() as db:
        birthday = customer_has_birthday(db, session.customer_id)
    return basket_view(session.basket, birthday)


@app.post("/api/basket")
def set_basket_line(body: BasketLine, response: Response, sid: str | None = Cookie(None)):
    """Set how many of one menu item are in the basket (0 removes it)."""
    session = require_customer(sid, response)
    basket = session.basket
    if body.quantity < 0 or body.quantity > 10:
        raise HTTPException(422, "You can order between 1 and 10 of each item.")
    with database() as db:
        items = load_menu(db)
        birthday = customer_has_birthday(db, session.customer_id)
    line = next((item for item in basket.items if item["id"] == body.id), None)
    if body.quantity == 0:
        basket.remove_item(body.id)
    elif line:
        basket.add_item(body.id, line["name"], body.quantity - line["quantity"], line["type"], line["price"])
    else:
        details = items.get(body.id)
        if not details:
            raise HTTPException(404, "That item is no longer on the menu.")
        basket.add_item(body.id, details["name"], body.quantity, details["type"], details["price"])
    return basket_view(basket, birthday)


@app.post("/api/basket/discount")
def apply_discount(body: Code, response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    basket = session.basket
    code = body.code.strip()
    if not code:
        raise HTTPException(422, "Enter a discount code.")
    if not basket.items:
        raise HTTPException(422, "Add something to your basket first.")
    if basket.discount_code:
        raise HTTPException(409, f"{basket.discount_code} is already applied to this basket.")
    with database() as db:
        subtotal = basket.calculate_total_price()["subtotal"]
        result = OrderManager(db).validate_and_apply_discount_code(code, subtotal)
        birthday = customer_has_birthday(db, session.customer_id)
    if not result["success"]:
        raise HTTPException(422, result.get("message", "That code can't be used."))
    basket.apply_discount(result["discount_amount"])
    basket.discount_code = code
    return basket_view(basket, birthday)


# ---------------------------------------------------------------- orders

class NewOrder(BaseModel):
    method: str


@app.post("/api/orders")
def place_order(body: NewOrder, response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    if body.method not in ("Delivery", "Pickup"):
        raise HTTPException(422, "Choose delivery or pickup.")
    if not session.basket.items:
        raise HTTPException(422, "Your basket is empty.")
    with database() as db:
        birthday = customer_has_birthday(db, session.customer_id)
        result = OrderManager(db).place_order(session.customer_id, session.basket, body.method, None, birthday)
    if not result or not result["success"]:
        raise HTTPException(500, (result or {}).get("message", "The order could not be placed."))
    details = dict(result["details"])
    details["birthday_discount"] = birthday
    session.basket.clear_basket()
    return plain(details)


@app.get("/api/orders")
def my_orders(response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    now = datetime.datetime.now()
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT order_id, order_date, confirmation_number, status, total_price, delivery_method
            FROM customerorder
            WHERE customer_id = %s
            ORDER BY order_date DESC
            LIMIT 10
            """, (session.customer_id,))
        orders = cursor.fetchall()
        for order in orders:
            cursor = db.execute_query(
                """
                SELECT oi.quantity, mi.name, mi.price, mi.type
                FROM order_item oi
                JOIN menu_item mi ON oi.menu_item_id = mi.menu_item_id
                WHERE oi.order_id = %s
                """, (order["order_id"],))
            order["items"] = cursor.fetchall()
            age = (now - order["order_date"]).total_seconds()
            order["cancel_seconds_left"] = (
                max(0, int(CANCEL_WINDOW_SECONDS - age)) if order["status"] == "Pending" else 0)
    return plain(orders)


@app.post("/api/orders/{order_id}/cancel")
def cancel_order(order_id: int, response: Response, sid: str | None = Cookie(None)):
    session = require_customer(sid, response)
    with database() as db:
        cursor = db.execute_query(
            "SELECT order_date FROM customerorder WHERE order_id = %s AND customer_id = %s",
            (order_id, session.customer_id))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(404, "Order not found.")
        if (datetime.datetime.now() - order["order_date"]).total_seconds() > CANCEL_WINDOW_SECONDS:
            raise HTTPException(409, "Orders can only be cancelled in the first five minutes.")
        result = OrderManager(db).cancel_order(session.customer_id, order_id)
    if not result["success"]:
        raise HTTPException(409, result["message"])
    return {"ok": True}


# ---------------------------------------------------------------- pages

from web_app.staff_api import router as staff_router  # noqa: E402  (needs the helpers above)

app.include_router(staff_router)


@app.get("/")
def customer_page():
    return FileResponse(STATIC / "index.html")


@app.get("/staff")
def staff_page():
    return FileResponse(STATIC / "staff.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
