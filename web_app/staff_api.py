# Vibe coded: this web interface was written with an AI assistant in 2026.
"""
Staff pages of the web interface.

The desktop staff app keeps its SQL inside the Tkinter screens, so it cannot be imported here.
These routes run the same queries and follow the same rules as staff_app: the order states,
grouping deliveries by postal code, pizza prices from ingredient cost with 40% margin and 9% VAT,
and the earnings filters.
"""
import datetime
import re
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from customer_app.customer import Customer
from web_app import geo
from web_app.server import database, get_session, plain

router = APIRouter(prefix="/api/staff")

PROFIT_MARGIN = Decimal("0.40")
VAT = Decimal("0.09")
ACTIVE = ("Pending", "Ready for Delivery", "Out for Delivery")


def require_staff(sid, response):
    session = get_session(sid, response)
    if session.staff_id is None:
        raise HTTPException(401, "Please log in.")
    return session


def pizza_price(total_cost, margin=PROFIT_MARGIN, vat=VAT, base=Decimal("0.00")) -> Decimal:
    price = (Decimal(str(total_cost or 0)) + Decimal(str(base))) * (1 + Decimal(str(margin))) * (1 + Decimal(str(vat)))
    return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def extract_postal_code(address: str) -> str:
    match = re.search(r"\b\d{4}\b", address or "")
    return match.group() if match else "Unknown"


def order_items(db, order_id):
    cursor = db.execute_query(
        """
        SELECT oi.quantity, mi.name, mi.price, mi.type
        FROM order_item oi
        JOIN menu_item mi ON oi.menu_item_id = mi.menu_item_id
        WHERE oi.order_id = %s
        """, (order_id,))
    return cursor.fetchall()


# ---------------------------------------------------------------- login

class Login(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: Login, response: Response, sid: str | None = Cookie(None)):
    session = get_session(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT staff_id, password, name FROM staff WHERE username = %s", (body.username.strip(),))
        staff = cursor.fetchone()
    if not staff or staff["password"] != Customer.hash_password(body.password.strip()):
        raise HTTPException(401, "Username or password didn't match.")
    session.staff_id = staff["staff_id"]
    return {"ok": True}


@router.post("/logout")
def logout(response: Response, sid: str | None = Cookie(None)):
    get_session(sid, response).staff_id = None
    return {"ok": True}


@router.get("/me")
def me(response: Response, sid: str | None = Cookie(None)):
    session = require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT name, role FROM staff WHERE staff_id = %s", (session.staff_id,))
        return cursor.fetchone()


# ---------------------------------------------------------------- live orders and deliveries

def free_couriers_after_30_minutes(db):
    """A courier is available again 30 minutes after leaving, as in the desktop app."""
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=30)
    cursor = db.execute_query(
        """
        SELECT da.delivery_person_id
        FROM deliveryassignment da
        JOIN customerorder co ON da.order_id = co.order_id
        WHERE da.assigned_at <= %s
        AND co.status = 'Out for Delivery'
        """, (cutoff,))
    for person in cursor.fetchall():
        db.execute_query("UPDATE deliverypersonnel SET availability = 1 WHERE delivery_person_id = %s",
                         (person["delivery_person_id"],))
    db.connection.commit()


@router.get("/board")
def board(response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        free_couriers_after_30_minutes(db)
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, co.status, co.delivery_method, co.total_price,
                   c.name AS customer_name, c.last_name, c.address, c.phone_number,
                   dp.name AS delivery_person_name
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            LEFT JOIN deliveryassignment da ON co.order_id = da.order_id
            LEFT JOIN deliverypersonnel dp ON da.delivery_person_id = dp.delivery_person_id
            WHERE co.status IN ('Pending', 'Ready for Delivery', 'Out for Delivery')
            ORDER BY co.order_date ASC
            """)
        orders = cursor.fetchall()
        for order in orders:
            order["items"] = order_items(db, order["order_id"])
            order["postal_code"] = extract_postal_code(order["address"])
            order["lat"] = order["lng"] = None
            order["exact"] = False
            if order["delivery_method"] == "Delivery":
                order.update(geo.locate(order["address"], order["postal_code"]) or {})
        cursor = db.execute_query("SELECT * FROM deliverypersonnel ORDER BY name")
        couriers = cursor.fetchall()
    return plain({"orders": orders, "couriers": couriers, "shop": geo.SHOP, "geocoding": geo.ENABLED})


@router.post("/orders/{order_id}/ready")
def mark_ready(order_id: int, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT status FROM customerorder WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()
        if not order or order["status"] != "Pending":
            raise HTTPException(409, "Only a new order can be marked ready.")
        db.execute_query("UPDATE customerorder SET status = 'Ready for Delivery' WHERE order_id = %s", (order_id,))
        db.connection.commit()
    return {"ok": True}


@router.post("/orders/{order_id}/dispatch")
def dispatch(order_id: int, response: Response, sid: str | None = Cookie(None)):
    """
    Send one ready delivery order out. The courier of its postal area takes it, together with up
    to two more ready orders for the same area that were placed within three minutes of it
    (the grouping rule of the desktop app).
    """
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, co.status, co.delivery_method, c.address,
                   (SELECT COUNT(*) FROM deliveryassignment da WHERE da.order_id = co.order_id) AS assigned
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            WHERE co.order_id = %s
            """, (order_id,))
        order = cursor.fetchone()
        if not order or order["status"] != "Ready for Delivery" or order["delivery_method"] != "Delivery" or order["assigned"]:
            raise HTTPException(409, "Only a ready delivery order can be sent out.")
        postal_code = extract_postal_code(order["address"])
        if postal_code == "Unknown":
            raise HTTPException(409, "This address has no four-digit postal code, so no courier can be matched to it.")
        cursor = db.execute_query(
            "SELECT delivery_person_id, name FROM deliverypersonnel WHERE assigned_postal_code = %s AND availability = 1",
            (postal_code,))
        courier = cursor.fetchone()
        if not courier:
            raise HTTPException(409, f"No courier for {postal_code} is available right now. Wait for one to come back, or add one under Couriers.")
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, c.address
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            LEFT JOIN deliveryassignment da ON co.order_id = da.order_id
            WHERE co.status = 'Ready for Delivery' AND da.order_id IS NULL
              AND co.delivery_method = 'Delivery' AND co.order_id <> %s
            ORDER BY co.order_date ASC
            """, (order_id,))
        batch = [order]
        for other in cursor.fetchall():
            near = abs(other["order_date"] - order["order_date"]) <= datetime.timedelta(minutes=3)
            if len(batch) < 3 and near and extract_postal_code(other["address"]) == postal_code:
                batch.append(other)
        try:
            for item in batch:
                db.execute_query(
                    "INSERT INTO deliveryassignment (order_id, delivery_person_id, assigned_at) VALUES (%s, %s, %s)",
                    (item["order_id"], courier["delivery_person_id"], datetime.datetime.now()))
                db.execute_query("UPDATE customerorder SET status = 'Out for Delivery' WHERE order_id = %s", (item["order_id"],))
            db.execute_query("UPDATE deliverypersonnel SET availability = 0 WHERE delivery_person_id = %s",
                             (courier["delivery_person_id"],))
            db.connection.commit()
        except Exception:
            db.connection.rollback()
            raise HTTPException(500, "Sending the order out failed.")
    return {"courier": courier["name"], "postal_code": postal_code, "orders": [item["order_id"] for item in batch]}


@router.post("/orders/{order_id}/delivered")
def mark_delivered(order_id: int, response: Response, sid: str | None = Cookie(None)):
    """The last step: a delivery that is on the road has arrived, or a ready pickup order was handed over."""
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT status, delivery_method FROM customerorder WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(404, "Order not found.")
        if order["delivery_method"] == "Pickup" and order["status"] != "Ready for Delivery":
            raise HTTPException(409, "A pickup order can be handed over once it is ready.")
        if order["delivery_method"] == "Delivery" and order["status"] != "Out for Delivery":
            raise HTTPException(409, "A delivery has to be sent out before it can be delivered.")
        db.execute_query("UPDATE customerorder SET status = 'Delivered' WHERE order_id = %s", (order_id,))
        cursor = db.execute_query("SELECT delivery_person_id FROM deliveryassignment WHERE order_id = %s", (order_id,))
        assignment = cursor.fetchone()
        if assignment:
            # the courier is free again once none of their orders is still on the road
            cursor = db.execute_query(
                """
                SELECT COUNT(*) AS still_out
                FROM deliveryassignment da
                JOIN customerorder co ON co.order_id = da.order_id
                WHERE da.delivery_person_id = %s AND co.status = 'Out for Delivery'
                """, (assignment["delivery_person_id"],))
            if not cursor.fetchone()["still_out"]:
                db.execute_query("UPDATE deliverypersonnel SET availability = 1 WHERE delivery_person_id = %s",
                                 (assignment["delivery_person_id"],))
        db.connection.commit()
    return {"ok": True}


@router.post("/deliveries/assign")
def assign_couriers(response: Response, sid: str | None = Cookie(None)):
    """
    Group the ready delivery orders by postal code. One courier takes up to three orders of the
    same postal code that were placed within three minutes of the first one.
    """
    require_staff(sid, response)
    assigned, waiting = [], []
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, c.name AS customer_name, c.address, co.status
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            LEFT JOIN deliveryassignment da ON co.order_id = da.order_id
            WHERE co.status = 'Ready for Delivery' AND da.order_id IS NULL
              AND co.delivery_method = 'Delivery'
            ORDER BY co.order_date ASC
            """)
        orders = cursor.fetchall()
        by_postal_code = {}
        for order in orders:
            by_postal_code.setdefault(extract_postal_code(order["address"]), []).append(order)

        for postal_code, orders_list in by_postal_code.items():
            if postal_code == "Unknown":
                waiting.append(f"{len(orders_list)} order(s) without a postal code in the address")
                continue
            batch = []
            for order in orders_list:
                if not batch:
                    batch.append(order)
                elif order["order_date"] - batch[0]["order_date"] <= datetime.timedelta(minutes=3) and len(batch) < 3:
                    batch.append(order)
                else:
                    break
            cursor = db.execute_query(
                """
                SELECT dp.delivery_person_id, dp.name
                FROM deliverypersonnel dp
                WHERE dp.assigned_postal_code = %s AND dp.availability = 1
                """, (postal_code,))
            courier = cursor.fetchone()
            if not courier:
                waiting.append(f"No courier available for {postal_code}")
                continue
            try:
                for order in batch:
                    db.execute_query(
                        "INSERT INTO deliveryassignment (order_id, delivery_person_id, assigned_at) VALUES (%s, %s, %s)",
                        (order["order_id"], courier["delivery_person_id"], datetime.datetime.now()))
                    db.execute_query("UPDATE customerorder SET status = 'Out for Delivery' WHERE order_id = %s",
                                     (order["order_id"],))
                db.execute_query("UPDATE deliverypersonnel SET availability = 0 WHERE delivery_person_id = %s",
                                 (courier["delivery_person_id"],))
                db.connection.commit()
                assigned.append({"courier": courier["name"], "postal_code": postal_code,
                                 "orders": [order["order_id"] for order in batch]})
            except Exception:
                db.connection.rollback()
                raise HTTPException(500, "Assigning couriers failed.")
    return {"assigned": assigned, "waiting": waiting, "ready": len(orders)}


class Courier(BaseModel):
    name: str
    assigned_postal_code: str
    availability: bool = True


def check_courier(body: Courier):
    if not body.name.strip() or not body.assigned_postal_code.strip():
        raise HTTPException(422, "Enter a name and a postal code.")
    if not re.match(r"^\d{4}$", body.assigned_postal_code.strip()):
        raise HTTPException(422, "The postal code is four digits, for example 6211.")


@router.post("/couriers")
def add_courier(body: Courier, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_courier(body)
    with database() as db:
        db.execute_query("INSERT INTO deliverypersonnel (name, assigned_postal_code, availability) VALUES (%s, %s, %s)",
                         (body.name.strip(), body.assigned_postal_code.strip(), 1))
        db.connection.commit()
    return {"ok": True}


@router.put("/couriers/{courier_id}")
def edit_courier(courier_id: int, body: Courier, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_courier(body)
    with database() as db:
        db.execute_query(
            "UPDATE deliverypersonnel SET name = %s, assigned_postal_code = %s, availability = %s WHERE delivery_person_id = %s",
            (body.name.strip(), body.assigned_postal_code.strip(), int(body.availability), courier_id))
        db.connection.commit()
    return {"ok": True}


@router.delete("/couriers/{courier_id}")
def delete_courier(courier_id: int, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT 1 FROM deliveryassignment WHERE delivery_person_id = %s LIMIT 1", (courier_id,))
        if cursor.fetchone():
            raise HTTPException(409, "This courier has deliveries on record and can't be removed. Set them to unavailable instead.")
        db.execute_query("DELETE FROM deliverypersonnel WHERE delivery_person_id = %s", (courier_id,))
        db.connection.commit()
    return {"ok": True}


# ---------------------------------------------------------------- menu

class MenuItem(BaseModel):
    name: str
    type: str = "Pizza"
    price: float | None = None           # drinks and desserts; pizza prices are calculated
    ingredient_ids: list[int] = []


def ingredient_totals(db, ingredient_ids):
    marks = ",".join(["%s"] * len(ingredient_ids))
    cursor = db.execute_query(
        f"""
        SELECT SUM(cost) AS total_cost,
               MIN(is_vegetarian) AS all_vegetarian, MIN(is_vegan) AS all_vegan
        FROM ingredient
        WHERE ingredient_id IN ({marks})
        """, tuple(ingredient_ids))
    return cursor.fetchone()


def checked_price(body: MenuItem) -> Decimal:
    if body.price is None or body.price <= 0:
        raise HTTPException(422, "Enter a price above zero.")
    return Decimal(str(round(body.price, 2))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.get("/menu")
def menu(response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT type, menu_item_id AS id, name, price FROM menu_item ORDER BY type, name")
        items = cursor.fetchall()
        cursor = db.execute_query(
            """
            SELECT pi.pizza_id, i.ingredient_id, i.name, i.is_vegetarian, i.is_vegan
            FROM pizza_ingredient pi
            JOIN ingredient i ON i.ingredient_id = pi.ingredient_id
            ORDER BY i.name
            """)
        links = cursor.fetchall()
    for item in items:
        mine = [link for link in links if link["pizza_id"] == item["id"]] if item["type"] == "Pizza" else []
        item["ingredient_ids"] = [link["ingredient_id"] for link in mine]
        item["ingredients"] = [link["name"] for link in mine]
        # a pizza is vegetarian or vegan when every ingredient is, the same rule the shop uses
        item["vegetarian"] = bool(mine) and all(link["is_vegetarian"] for link in mine)
        item["vegan"] = bool(mine) and all(link["is_vegan"] for link in mine)
    return plain(items)


@router.post("/menu")
def add_menu_item(body: MenuItem, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Enter a name.")
    if body.type not in ("Pizza", "Drink", "Dessert"):
        raise HTTPException(422, "Choose pizza, drink or dessert.")
    with database() as db:
        try:
            if body.type == "Pizza":
                if not body.ingredient_ids:
                    raise HTTPException(422, "Pick at least one ingredient.")
                totals = ingredient_totals(db, body.ingredient_ids)
                price = pizza_price(totals["total_cost"])
                if price <= 0:
                    raise HTTPException(422, "The ingredients cost nothing, so there is no price.")
            else:
                price = checked_price(body)
            cursor = db.execute_query("INSERT INTO menu_item (name, type, price) VALUES (%s, %s, %s)",
                                      (name, body.type, float(price)))
            item_id = cursor.lastrowid
            if body.type == "Pizza":
                db.execute_query(
                    "INSERT INTO pizza (pizza_id, name, size, price, is_vegetarian, is_vegan, profit_margin, vat, base_price) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (item_id, name, "Medium", float(price), int(totals["all_vegetarian"] or 0),
                     int(totals["all_vegan"] or 0), float(PROFIT_MARGIN), float(VAT), 0.0))
                for ingredient_id in body.ingredient_ids:
                    db.execute_query("INSERT INTO pizza_ingredient (pizza_id, ingredient_id) VALUES (%s, %s)",
                                     (item_id, ingredient_id))
            db.connection.commit()
        except HTTPException:
            db.connection.rollback()
            raise
        except Exception:
            db.connection.rollback()
            raise HTTPException(500, "Saving the menu item failed.")
    return {"ok": True, "price": float(price)}


@router.put("/menu/{item_id}")
def edit_menu_item(item_id: int, body: MenuItem, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Enter a name.")
    with database() as db:
        cursor = db.execute_query("SELECT type FROM menu_item WHERE menu_item_id = %s", (item_id,))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(404, "Menu item not found.")
        try:
            if item["type"] == "Pizza":
                if not body.ingredient_ids:
                    raise HTTPException(422, "Pick at least one ingredient.")
                totals = ingredient_totals(db, body.ingredient_ids)
                price = pizza_price(totals["total_cost"])
                if price <= 0:
                    raise HTTPException(422, "The ingredients cost nothing, so there is no price.")
            else:
                price = checked_price(body)
            db.execute_query("UPDATE menu_item SET name = %s, price = %s WHERE menu_item_id = %s",
                             (name, float(price), item_id))
            if item["type"] == "Pizza":
                db.execute_query(
                    "UPDATE pizza SET name = %s, price = %s, is_vegetarian = %s, is_vegan = %s WHERE pizza_id = %s",
                    (name, float(price), int(totals["all_vegetarian"] or 0), int(totals["all_vegan"] or 0), item_id))
                db.execute_query("DELETE FROM pizza_ingredient WHERE pizza_id = %s", (item_id,))
                for ingredient_id in body.ingredient_ids:
                    db.execute_query("INSERT INTO pizza_ingredient (pizza_id, ingredient_id) VALUES (%s, %s)",
                                     (item_id, ingredient_id))
            db.connection.commit()
        except HTTPException:
            db.connection.rollback()
            raise
        except Exception:
            db.connection.rollback()
            raise HTTPException(500, "Saving the menu item failed.")
    return {"ok": True, "price": float(price)}


@router.delete("/menu/{item_id}")
def delete_menu_item(item_id: int, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        db.execute_query("DELETE FROM pizza_ingredient WHERE pizza_id = %s", (item_id,))
        db.execute_query("DELETE FROM pizza WHERE pizza_id = %s", (item_id,))
        db.execute_query("DELETE FROM menu_item WHERE menu_item_id = %s", (item_id,))
        db.connection.commit()
    return {"ok": True}


# ---------------------------------------------------------------- ingredients

class Ingredient(BaseModel):
    name: str
    cost: float
    is_vegetarian: bool = False
    is_vegan: bool = False


def recalculate_pizza_prices(db) -> int:
    """After an ingredient changes, every pizza price follows its ingredients again."""
    cursor = db.execute_query("SELECT pizza_id, price, profit_margin, vat, base_price FROM pizza")
    changed = 0
    for pizza in cursor.fetchall():
        cursor = db.execute_query(
            """
            SELECT SUM(i.cost) AS total_cost
            FROM pizza_ingredient pi
            JOIN ingredient i ON pi.ingredient_id = i.ingredient_id
            WHERE pi.pizza_id = %s
            """, (pizza["pizza_id"],))
        price = pizza_price(cursor.fetchone()["total_cost"], pizza["profit_margin"], pizza["vat"], pizza["base_price"])
        if price <= 0:
            continue
        if price != pizza["price"]:
            changed += 1
        db.execute_query("UPDATE pizza SET price = %s WHERE pizza_id = %s", (float(price), pizza["pizza_id"]))
        db.execute_query("UPDATE menu_item SET price = %s WHERE menu_item_id = %s AND type = 'Pizza'",
                         (float(price), pizza["pizza_id"]))
    db.connection.commit()
    return changed


def check_ingredient(body: Ingredient):
    if not body.name.strip():
        raise HTTPException(422, "Enter a name.")
    if body.cost < 0:
        raise HTTPException(422, "The cost can't be negative.")


@router.get("/ingredients")
def ingredients(response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT i.ingredient_id AS id, i.name, i.cost, i.is_vegetarian, i.is_vegan,
                   (SELECT COUNT(*) FROM pizza_ingredient pi WHERE pi.ingredient_id = i.ingredient_id) AS used_in
            FROM ingredient i
            ORDER BY i.name
            """)
        return plain(cursor.fetchall())


@router.post("/ingredients")
def add_ingredient(body: Ingredient, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_ingredient(body)
    with database() as db:
        db.execute_query("INSERT INTO ingredient (name, cost, is_vegetarian, is_vegan) VALUES (%s, %s, %s, %s)",
                         (body.name.strip(), body.cost, int(body.is_vegetarian), int(body.is_vegan)))
        db.connection.commit()
    return {"ok": True}


@router.put("/ingredients/{ingredient_id}")
def edit_ingredient(ingredient_id: int, body: Ingredient, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_ingredient(body)
    with database() as db:
        db.execute_query(
            "UPDATE ingredient SET name = %s, cost = %s, is_vegetarian = %s, is_vegan = %s WHERE ingredient_id = %s",
            (body.name.strip(), body.cost, int(body.is_vegetarian), int(body.is_vegan), ingredient_id))
        db.connection.commit()
        changed = recalculate_pizza_prices(db)
    return {"ok": True, "pizzas_repriced": changed}


@router.delete("/ingredients/{ingredient_id}")
def delete_ingredient(ingredient_id: int, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT COUNT(*) AS count FROM pizza_ingredient WHERE ingredient_id = %s", (ingredient_id,))
        if cursor.fetchone()["count"]:
            raise HTTPException(409, "This ingredient is on a pizza. Take it off those pizzas first.")
        db.execute_query("DELETE FROM ingredient WHERE ingredient_id = %s", (ingredient_id,))
        db.connection.commit()
    return {"ok": True}


# ---------------------------------------------------------------- discount codes

class DiscountCode(BaseModel):
    code: str
    expiration_date: str
    discount_percentage: float
    is_used: bool = False


def check_code(body: DiscountCode):
    if not body.code.strip():
        raise HTTPException(422, "Enter a code.")
    try:
        datetime.datetime.strptime(body.expiration_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(422, "Choose an expiry date.")
    if not 0 <= body.discount_percentage <= 100:
        raise HTTPException(422, "The discount is a percentage between 0 and 100.")


@router.get("/codes")
def codes(response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query("SELECT * FROM discountcode ORDER BY expiration_date DESC, code")
        return plain(cursor.fetchall())


@router.post("/codes")
def add_code(body: DiscountCode, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_code(body)
    with database() as db:
        cursor = db.execute_query("SELECT 1 FROM discountcode WHERE code = %s", (body.code.strip(),))
        if cursor.fetchone():
            raise HTTPException(409, "That code already exists.")
        db.execute_query(
            "INSERT INTO discountcode (code, expiration_date, discount_percentage, is_used) VALUES (%s, %s, %s, %s)",
            (body.code.strip(), body.expiration_date, body.discount_percentage, 0))
        db.connection.commit()
    return {"ok": True}


@router.put("/codes/{code}")
def edit_code(code: str, body: DiscountCode, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    check_code(body)
    with database() as db:
        db.execute_query(
            "UPDATE discountcode SET expiration_date = %s, discount_percentage = %s, is_used = %s WHERE code = %s",
            (body.expiration_date, body.discount_percentage, int(body.is_used), code))
        db.connection.commit()
    return {"ok": True}


@router.delete("/codes/{code}")
def delete_code(code: str, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        db.execute_query("DELETE FROM discountcode WHERE code = %s", (code,))
        db.connection.commit()
    return {"ok": True}


# ---------------------------------------------------------------- history, receipts, earnings

@router.get("/history")
def history(response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, c.name AS customer_name, c.last_name, co.total_price, co.status,
                   co.delivery_method, co.confirmation_number
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            ORDER BY co.order_date DESC
            """)
        return plain(cursor.fetchall())


@router.get("/orders/{order_id}")
def order_detail(order_id: int, response: Response, sid: str | None = Cookie(None)):
    require_staff(sid, response)
    with database() as db:
        cursor = db.execute_query(
            """
            SELECT co.order_id, co.order_date, c.name AS customer_name, c.last_name, c.address, co.total_price,
                   co.status, co.delivery_method, co.confirmation_number
            FROM customerorder co
            JOIN customer c ON co.customer_id = c.customer_id
            WHERE co.order_id = %s
            """, (order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(404, "Order not found.")
        order["items"] = order_items(db, order_id)
    return plain(order)


@router.get("/earnings")
def earnings(response: Response, sid: str | None = Cookie(None), start: str = "", end: str = "",
             region: str = "", gender: str = "All", min_age: int | None = None, max_age: int | None = None):
    require_staff(sid, response)
    start = start or "1900-01-01"
    end = end or datetime.date.today().strftime("%Y-%m-%d")
    for value in (start, end):
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(422, "The dates are not valid.")
    if (min_age is not None and min_age < 0) or (max_age is not None and max_age < 0):
        raise HTTPException(422, "An age can't be negative.")

    query = """
        SELECT co.order_id, co.order_date, c.name, c.gender, c.birthdate, c.address, co.total_price
        FROM customerorder co
        JOIN customer c ON co.customer_id = c.customer_id
        WHERE DATE(co.order_date) BETWEEN %s AND %s
    """
    params = [start, end]
    if region.strip():
        query += " AND c.address LIKE %s"
        params.append(f"%{region.strip()}%")
    if gender != "All":
        query += " AND c.gender = %s"
        params.append(gender)
    filtering = min_age is not None or max_age is not None
    if filtering:
        query += " AND c.birthdate IS NOT NULL"
    query += " ORDER BY co.order_date"

    with database() as db:
        cursor = db.execute_query(query, tuple(params))
        rows = cursor.fetchall()

    today = datetime.date.today()
    records, by_date, by_gender, total = [], {}, {}, Decimal("0.00")
    for row in rows:
        birthdate = row.pop("birthdate")
        row["age"] = None
        if birthdate:
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            if min_age is not None and age < min_age:
                continue
            if max_age is not None and age > max_age:
                continue
            row["age"] = age
        elif filtering:
            continue
        price = row["total_price"] or Decimal("0.00")
        total += price
        day = row["order_date"].date().isoformat()
        by_date[day] = by_date.get(day, Decimal("0.00")) + price
        by_gender[row["gender"]] = by_gender.get(row["gender"], Decimal("0.00")) + price
        records.append(row)
    return plain({
        "records": records, "total": total,
        "by_date": [{"date": day, "earnings": amount} for day, amount in sorted(by_date.items())],
        "by_gender": [{"gender": name, "earnings": amount} for name, amount in by_gender.items()],
    })
