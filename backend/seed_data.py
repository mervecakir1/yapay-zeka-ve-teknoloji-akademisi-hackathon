from datetime import datetime
from database import SessionLocal
from models import User, Customer, Product, Order, OrderDetail, Inventory

db = SessionLocal()

# Clear old data
db.query(OrderDetail).delete()
db.query(Inventory).delete()
db.query(Order).delete()
db.query(Product).delete()
db.query(Customer).delete()
db.query(User).delete()
db.commit()

# Users
users = [
    User(user_id=1, name="Admin User", email="admin@aiecommerce.com", password="admin123", role="Admin"),
    User(user_id=2, name="Business Owner", email="owner@aiecommerce.com", password="owner123", role="Business Owner"),
    User(user_id=3, name="Inventory Staff", email="inventory@aiecommerce.com", password="staff123", role="Inventory Staff"),
]

# Customers
customers = [
    Customer(customer_id=1, name="Emma Johnson", email="emma@example.com", phone="+90 555 111 2233"),
    Customer(customer_id=2, name="Olivia Smith", email="olivia@example.com", phone="+90 555 222 3344"),
    Customer(customer_id=3, name="Sophia Brown", email="sophia@example.com", phone="+90 555 333 4455"),
    Customer(customer_id=4, name="Ava Miller", email="ava@example.com", phone="+90 555 444 5566"),
    Customer(customer_id=5, name="Mia Davis", email="mia@example.com", phone="+90 555 555 6677"),
    Customer(customer_id=6, name="Charlotte Moore", email="charlotte@example.com", phone="+90 555 666 7788"),
    Customer(customer_id=7, name="Amelia Taylor", email="amelia@example.com", phone="+90 555 777 8899"),
    Customer(customer_id=8, name="Harper Anderson", email="harper@example.com", phone="+90 555 888 9900"),
    Customer(customer_id=9, name="Evelyn Thomas", email="evelyn@example.com", phone="+90 555 999 0011"),
    Customer(customer_id=10, name="Abigail Jackson", email="abigail@example.com", phone="+90 555 101 1122"),
    Customer(customer_id=11, name="Emily White", email="emily@example.com", phone="+90 555 202 2233"),
    Customer(customer_id=12, name="Elizabeth Harris", email="elizabeth@example.com", phone="+90 555 303 3344"),
    Customer(customer_id=13, name="Sofia Martin", email="sofia@example.com", phone="+90 555 404 4455"),
    Customer(customer_id=14, name="Avery Thompson", email="avery@example.com", phone="+90 555 505 5566"),
    Customer(customer_id=15, name="Ella Garcia", email="ella@example.com", phone="+90 555 606 6677"),
    Customer(customer_id=16, name="Scarlett Martinez", email="scarlett@example.com", phone="+90 555 707 7788"),
    Customer(customer_id=17, name="Grace Robinson", email="grace@example.com", phone="+90 555 808 8899"),
    Customer(customer_id=18, name="Lily Clark", email="lily@example.com", phone="+90 555 909 9900"),
    Customer(customer_id=19, name="Chloe Lewis", email="chloe@example.com", phone="+90 555 121 3344"),
    Customer(customer_id=20, name="Victoria Walker", email="victoria@example.com", phone="+90 555 232 4455"),
]

# Products
products = [
    Product(product_id=1, product_name="Handmade Soap", category="Personal Care", price=7, stock_quantity=35, critical_stock_level=15),
    Product(product_id=2, product_name="Natural Olive Oil", category="Food", price=18, stock_quantity=8, critical_stock_level=10),
    Product(product_id=3, product_name="Organic Honey", category="Food", price=12, stock_quantity=5, critical_stock_level=10),
    Product(product_id=4, product_name="Handmade Candle", category="Home Decoration", price=9, stock_quantity=22, critical_stock_level=8),
    Product(product_id=5, product_name="Ceramic Coffee Cup", category="Home & Kitchen", price=16, stock_quantity=18, critical_stock_level=10),
    Product(product_id=6, product_name="Natural Lip Balm", category="Cosmetics", price=6, stock_quantity=40, critical_stock_level=15),
    Product(product_id=7, product_name="Handmade Bracelet", category="Accessories", price=14, stock_quantity=12, critical_stock_level=10),
    Product(product_id=8, product_name="Knitted Scarf", category="Textile", price=20, stock_quantity=9, critical_stock_level=12),
    Product(product_id=9, product_name="Organic Herbal Tea", category="Beverage", price=8, stock_quantity=6, critical_stock_level=12),
    Product(product_id=10, product_name="Handmade Necklace", category="Accessories", price=19, stock_quantity=25, critical_stock_level=10),
    Product(product_id=11, product_name="Natural Face Cream", category="Cosmetics", price=15, stock_quantity=14, critical_stock_level=10),
    Product(product_id=12, product_name="Decorative Pillow Cover", category="Home Textile", price=13, stock_quantity=30, critical_stock_level=12),
    Product(product_id=13, product_name="Handmade Tote Bag", category="Fashion", price=22, stock_quantity=11, critical_stock_level=10),
    Product(product_id=14, product_name="Organic Jam", category="Food", price=9, stock_quantity=7, critical_stock_level=10),
    Product(product_id=15, product_name="Lavender Room Spray", category="Home Fragrance", price=10, stock_quantity=28, critical_stock_level=12),
    Product(product_id=16, product_name="Handmade Hair Clip", category="Accessories", price=5, stock_quantity=45, critical_stock_level=15),
    Product(product_id=17, product_name="Ceramic Plate", category="Home & Kitchen", price=24, stock_quantity=10, critical_stock_level=10),
    Product(product_id=18, product_name="Natural Body Lotion", category="Cosmetics", price=13, stock_quantity=16, critical_stock_level=10),
    Product(product_id=19, product_name="Handmade Keychain", category="Accessories", price=4, stock_quantity=50, critical_stock_level=20),
    Product(product_id=20, product_name="Organic Dried Fruit Box", category="Food", price=17, stock_quantity=6, critical_stock_level=10),
    Product(product_id=21, product_name="Macrame Wall Hanging", category="Home Decoration", price=28, stock_quantity=13, critical_stock_level=8),
    Product(product_id=22, product_name="Handmade Earrings", category="Accessories", price=11, stock_quantity=32, critical_stock_level=12),
    Product(product_id=23, product_name="Natural Shampoo Bar", category="Personal Care", price=9, stock_quantity=17, critical_stock_level=10),
    Product(product_id=24, product_name="Organic Tomato Paste", category="Food", price=14, stock_quantity=4, critical_stock_level=10),
    Product(product_id=25, product_name="Handmade Baby Blanket", category="Baby Products", price=35, stock_quantity=8, critical_stock_level=8),
    Product(product_id=26, product_name="Embroidered Table Runner", category="Home Textile", price=26, stock_quantity=15, critical_stock_level=10),
    Product(product_id=27, product_name="Natural Facial Serum", category="Cosmetics", price=21, stock_quantity=9, critical_stock_level=10),
    Product(product_id=28, product_name="Handmade Wallet", category="Fashion", price=18, stock_quantity=23, critical_stock_level=10),
    Product(product_id=29, product_name="Ceramic Vase", category="Home Decoration", price=32, stock_quantity=7, critical_stock_level=8),
    Product(product_id=30, product_name="Organic Spice Set", category="Food", price=16, stock_quantity=19, critical_stock_level=12),
    Product(product_id=31, product_name="Handmade Notebook", category="Stationery", price=10, stock_quantity=34, critical_stock_level=15),
    Product(product_id=32, product_name="Soy Wax Candle Set", category="Home Fragrance", price=25, stock_quantity=6, critical_stock_level=10),
    Product(product_id=33, product_name="Crochet Bag", category="Fashion", price=30, stock_quantity=12, critical_stock_level=10),
    Product(product_id=34, product_name="Natural Hand Cream", category="Cosmetics", price=8, stock_quantity=26, critical_stock_level=12),
    Product(product_id=35, product_name="Handmade Wooden Tray", category="Home & Kitchen", price=27, stock_quantity=9, critical_stock_level=10),
    Product(product_id=36, product_name="Organic Fig Jam", category="Food", price=11, stock_quantity=5, critical_stock_level=10),
    Product(product_id=37, product_name="Knitted Cardigan", category="Textile", price=45, stock_quantity=4, critical_stock_level=6),
    Product(product_id=38, product_name="Handmade Bookmark", category="Stationery", price=3, stock_quantity=60, critical_stock_level=20),
    Product(product_id=39, product_name="Natural Bath Salt", category="Personal Care", price=12, stock_quantity=14, critical_stock_level=10),
    Product(product_id=40, product_name="Personalized Gift Box", category="Gift Products", price=38, stock_quantity=7, critical_stock_level=8),
]

# Orders
orders = [
    Order(order_id=128, customer_id=1, order_date=datetime(2026, 5, 9), order_status="Preparing", total_amount=54),
    Order(order_id=127, customer_id=2, order_date=datetime(2026, 5, 9), order_status="Completed", total_amount=35),
    Order(order_id=126, customer_id=3, order_date=datetime(2026, 5, 8), order_status="Pending", total_amount=24),
    Order(order_id=125, customer_id=4, order_date=datetime(2026, 5, 8), order_status="Preparing", total_amount=36),
    Order(order_id=124, customer_id=5, order_date=datetime(2026, 5, 8), order_status="Completed", total_amount=32),
    Order(order_id=123, customer_id=6, order_date=datetime(2026, 5, 7), order_status="Pending", total_amount=36),
    Order(order_id=122, customer_id=7, order_date=datetime(2026, 5, 7), order_status="Completed", total_amount=14),
    Order(order_id=121, customer_id=8, order_date=datetime(2026, 5, 7), order_status="Preparing", total_amount=40),
    Order(order_id=120, customer_id=9, order_date=datetime(2026, 5, 6), order_status="Cancelled", total_amount=24),
    Order(order_id=119, customer_id=10, order_date=datetime(2026, 5, 6), order_status="Completed", total_amount=19),
    Order(order_id=118, customer_id=11, order_date=datetime(2026, 5, 6), order_status="Preparing", total_amount=30),
    Order(order_id=117, customer_id=12, order_date=datetime(2026, 5, 5), order_status="Pending", total_amount=26),
    Order(order_id=116, customer_id=13, order_date=datetime(2026, 5, 5), order_status="Completed", total_amount=22),
    Order(order_id=115, customer_id=14, order_date=datetime(2026, 5, 5), order_status="Preparing", total_amount=36),
    Order(order_id=114, customer_id=15, order_date=datetime(2026, 5, 4), order_status="Completed", total_amount=30),
    Order(order_id=113, customer_id=16, order_date=datetime(2026, 5, 4), order_status="Pending", total_amount=40),
    Order(order_id=112, customer_id=17, order_date=datetime(2026, 5, 4), order_status="Completed", total_amount=48),
    Order(order_id=111, customer_id=18, order_date=datetime(2026, 5, 3), order_status="Preparing", total_amount=39),
    Order(order_id=110, customer_id=19, order_date=datetime(2026, 5, 3), order_status="Completed", total_amount=40),
    Order(order_id=109, customer_id=20, order_date=datetime(2026, 5, 3), order_status="Pending", total_amount=34),
]

# Order Details
order_details = [
    OrderDetail(order_detail_id=1, order_id=128, product_id=2, quantity=3, unit_price=18),
    OrderDetail(order_detail_id=2, order_id=127, product_id=1, quantity=5, unit_price=7),
    OrderDetail(order_detail_id=3, order_id=126, product_id=3, quantity=2, unit_price=12),
    OrderDetail(order_detail_id=4, order_id=125, product_id=4, quantity=4, unit_price=9),
    OrderDetail(order_detail_id=5, order_id=124, product_id=5, quantity=2, unit_price=16),
    OrderDetail(order_detail_id=6, order_id=123, product_id=6, quantity=6, unit_price=6),
    OrderDetail(order_detail_id=7, order_id=122, product_id=7, quantity=1, unit_price=14),
    OrderDetail(order_detail_id=8, order_id=121, product_id=8, quantity=2, unit_price=20),
    OrderDetail(order_detail_id=9, order_id=120, product_id=9, quantity=3, unit_price=8),
    OrderDetail(order_detail_id=10, order_id=119, product_id=10, quantity=1, unit_price=19),
    OrderDetail(order_detail_id=11, order_id=118, product_id=11, quantity=2, unit_price=15),
    OrderDetail(order_detail_id=12, order_id=117, product_id=12, quantity=2, unit_price=13),
    OrderDetail(order_detail_id=13, order_id=116, product_id=13, quantity=1, unit_price=22),
    OrderDetail(order_detail_id=14, order_id=115, product_id=14, quantity=4, unit_price=9),
    OrderDetail(order_detail_id=15, order_id=114, product_id=15, quantity=3, unit_price=10),
    OrderDetail(order_detail_id=16, order_id=113, product_id=16, quantity=8, unit_price=5),
    OrderDetail(order_detail_id=17, order_id=112, product_id=17, quantity=2, unit_price=24),
    OrderDetail(order_detail_id=18, order_id=111, product_id=18, quantity=3, unit_price=13),
    OrderDetail(order_detail_id=19, order_id=110, product_id=19, quantity=10, unit_price=4),
    OrderDetail(order_detail_id=20, order_id=109, product_id=20, quantity=2, unit_price=17),
]

# Inventory records are created from product stock information
inventory_items = []

for product in products:
    inventory_items.append(
        Inventory(
            inventory_id=product.product_id,
            product_id=product.product_id,
            current_stock=product.stock_quantity,
            critical_level=product.critical_stock_level,
            last_updated=datetime.now()
        )
    )

db.add_all(users)
db.add_all(customers)
db.add_all(products)
db.add_all(orders)
db.add_all(order_details)
db.add_all(inventory_items)

db.commit()
db.close()

print("Large sample data inserted successfully.")