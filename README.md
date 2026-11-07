# Pizza ordering system

A desktop pizza shop on a MySQL database, built for the Databases course at Maastricht University (2024). Customers order through one app, staff run the kitchen, deliveries and reporting through another; both share a 16-table relational schema.

## What it does

**Customer app**
- Register and log in (passwords stored as SHA-256 hashes)
- Menu of pizzas, drinks and desserts with vegetarian and vegan labels and the ingredients of each pizza
- Basket with discount codes, a birthday discount and a loyalty reward: every 10th pizza is free
- Prices built from the ingredients plus a 40% margin and 9% VAT
- Order confirmation, estimated delivery time, order history and cancellation

**Staff app**
- Real-time and active orders, with status updates from pending to delivered
- Delivery management: orders grouped by postal code and assigned to available couriers
- Menu, ingredient and discount code management
- Order history, receipts and an earnings report with charts

## Database

16 tables: customers, orders and order items, pizzas with their ingredients, drinks, desserts, menus, discount codes, couriers, delivery assignments and postal areas. The schema is in [db/schema.sql](db/schema.sql); [db/seed.sql](db/seed.sql) fills it with the menu and made-up customers and orders.

## Stack

Python · Tkinter with ttkbootstrap · MySQL (mysql-connector-python) · matplotlib

## Run it

Requirements: Python 3.10+ and MySQL 8 (or MariaDB).

```
mysql -u root -p < db/schema.sql
mysql -u root -p < db/seed.sql
pip install -r requirements.txt
```

Set the database login (or copy `.env.example` and export its values), then start either app from the repository root:

```
set DB_PASSWORD=your-mysql-password      # macOS/Linux: export DB_PASSWORD=...
python -m customer_app.main              # log in as demo / demo
python -m staff_app.main
```

## Note

The original GitLab repository is no longer accessible, so this code was recovered from my last saved versions (October 2024). The only changes are that the database login now comes from environment variables and the library versions are pinned to those of 2024. All people and orders in the example data are made up.
