"""
Veritabanını sıfırlar ve frontend ile uyumlu örnek veri yükler.
Çalıştırma: python -m backend.seed
"""
from datetime import datetime, timezone, timedelta

from passlib.context import CryptContext

from .database import Base, engine, SessionLocal
from .models import User, Customer, Supplier, Product, Order, OrderDetail, ChatMessage

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1) Owner kullanıcı (frontend: email + password login)
        # Demo için 4 farklı rolde kullanıcı
        owner = User(name="Owner Admin", email="owner@kobi.local",
                     hashed_password=bcrypt_context.hash("password123"), role="Admin")
        biz = User(name="Business User", email="biz@kobi.local",
                   hashed_password=bcrypt_context.hash("password123"), role="Business Owner")
        sales = User(name="Sales Rep", email="sales@kobi.local",
                     hashed_password=bcrypt_context.hash("password123"), role="Sales Manager")
        inv = User(name="Stock Keeper", email="inventory@kobi.local",
                   hashed_password=bcrypt_context.hash("password123"), role="Inventory Staff")
        db.add_all([owner, biz, sales, inv])

        # 2) Suppliers
        s1 = Supplier(name="Anatolia Wholesale Foods", email="orders@anatolia.example", phone="+90 312 111 11 11")
        s2 = Supplier(name="Bursa Handcrafts Co.", email="info@bursacrafts.example", phone="+90 224 222 22 22")
        db.add_all([s1, s2])
        db.flush()

        # 3) Products (frontend kategori listesinden seçildi)
        products = [
            Product(name="Organic Tomato 1kg", category="Food",
                    price=4.5, stock_quantity=8, critical_stock_level=20, supplier_id=s1.id),
            Product(name="Cucumber 1kg", category="Food",
                    price=3.0, stock_quantity=120, critical_stock_level=20, supplier_id=s1.id),
            Product(name="Olive Oil 1L", category="Food",
                    price=12.0, stock_quantity=45, critical_stock_level=10, supplier_id=s1.id),
            Product(name="Handmade Basket", category="Home Decoration",
                    price=18.0, stock_quantity=15, critical_stock_level=5, supplier_id=s2.id),
            Product(name="Linen Tablecloth", category="Home Textile",
                    price=24.0, stock_quantity=4, critical_stock_level=8, supplier_id=s2.id),
            Product(name="Handmade Soap", category="Personal Care",
                    price=5.5, stock_quantity=60, critical_stock_level=15, supplier_id=s2.id),
            Product(name="Scented Candle", category="Home Fragrance",
                    price=8.0, stock_quantity=30, critical_stock_level=10, supplier_id=s2.id),
        ]
        db.add_all(products)
        db.flush()

        # 4) Customers
        c1 = Customer(name="Emma Johnson", email="emma@example.com", phone="+90 555 111 22 33")
        c2 = Customer(name="Michael Brown", email="michael@example.com", phone="+90 555 444 55 66")
        c3 = Customer(name="Sofia Garcia", email="sofia@example.com", phone="+90 555 777 88 99")
        db.add_all([c1, c2, c3])
        db.flush()

        now = datetime.now(timezone.utc)
        today = now
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        # 5) Orders (frontend tek ürünlü bekliyor - her birinde tek detay)
        orders = [
            Order(customer_id=c1.id, status="Completed", total_amount=12.0,
                  order_date=two_days_ago, created_at=two_days_ago,
                  tracking_no="TRK-001", shipping_carrier="Aras Cargo",
                  estimated_delivery=two_days_ago + timedelta(days=3)),
            Order(customer_id=c2.id, status="Preparing", total_amount=18.0,
                  order_date=today, created_at=today,
                  estimated_delivery=today + timedelta(days=3)),
            Order(customer_id=c1.id, status="Pending", total_amount=6.0,
                  order_date=today, created_at=today,
                  estimated_delivery=today + timedelta(days=3)),
            Order(customer_id=c3.id, status="Pending", total_amount=24.0,
                  order_date=yesterday, created_at=yesterday,
                  estimated_delivery=yesterday + timedelta(days=3)),
        ]
        db.add_all(orders)
        db.flush()

        # 6) OrderDetails
        db.add_all([
            OrderDetail(order_id=orders[0].id, product_id=products[2].id, quantity=1, unit_price=12.0),
            OrderDetail(order_id=orders[1].id, product_id=products[3].id, quantity=1, unit_price=18.0),
            OrderDetail(order_id=orders[2].id, product_id=products[5].id, quantity=1, unit_price=5.5),
            OrderDetail(order_id=orders[3].id, product_id=products[4].id, quantity=1, unit_price=24.0),
        ])

        # 7) Chat geçmişi (AI üyesi için)
        db.add_all([
            ChatMessage(customer_id=c1.id, role="user", content="Hello"),
            ChatMessage(customer_id=c1.id, role="assistant", content="Hi! How can I help you?"),
        ])

        db.commit()

        print("[seed] OK")
        print("  Demo logins (all password=password123):")
        print("    owner@kobi.local      -> Admin (full access)")
        print("    biz@kobi.local        -> Business Owner (full access)")
        print("    sales@kobi.local      -> Sales Manager (orders only)")
        print("    inventory@kobi.local  -> Inventory Staff (stock only)")
        print(f"  {len(products)} products, 3 customers, {len(orders)} orders, 2 suppliers loaded")
        print("  DB: backend/smb_app.db")
    finally:
        db.close()


if __name__ == "__main__":
    run()
