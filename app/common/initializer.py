from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.users.models import User, Role
from app.products.models import Category, Product, ProductImage
from app.inventory.models import Inventory
from app.security.passwd import hash_password

async def seed_data(db: AsyncSession):
    # Check if data already exists
    user_stmt = select(User)
    result = await db.execute(user_stmt)
    if result.scalars().first():
        print("Database already contains data. Skipping seeding.")
        return

    print("Seeding database with demo accounts and product catalog...")

    # 1. Seed Users
    admin = User(
        fullName="CommerceFlow Admin",
        email="admin@commerceflow.com",
        passwordHash=hash_password("admin123"),
        phone="1234567890",
        role=Role.ADMIN,
        verified=True
    )
    customer = User(
        fullName="CommerceFlow Customer",
        email="customer@commerceflow.com",
        passwordHash=hash_password("customer123"),
        phone="0987654321",
        role=Role.CUSTOMER,
        verified=True
    )
    db.add_all([admin, customer])
    await db.flush() # Populate IDs

    print("Seeding Categories...")
    # 2. Seed Categories
    electronics = Category(name="Electronics", description="Premium work setup gear")
    apparel = Category(name="Apparel", description="Minimalist everyday wear")
    office = Category(name="Office", description="Elegant desk organization utilities")
    db.add_all([electronics, apparel, office])
    await db.flush()

    print("Seeding Products...")
    # 3. Seed Products
    p1 = Product(
        name="Minimal Mechanical Keyboard",
        description="75% layout, hot-swappable switches, wireless connectivity, and premium aluminum frame.",
        price=Decimal("129.99"),
        categoryId=electronics.id,
        active=True
    )
    p2 = Product(
        name="Wool Felt Desk Mat",
        description="Premium merino wool felt desk pad to protect your workspace and improve mouse tracking.",
        price=Decimal("49.99"),
        categoryId=office.id,
        active=True
    )
    p3 = Product(
        name="Minimal Hardcover Notebook",
        description="A5 size, dotted grid, premium 120gsm ink-proof paper with black linen hardcover cover.",
        price=Decimal("24.99"),
        categoryId=office.id,
        active=True
    )
    p4 = Product(
        name="Heavyweight Hoodie",
        description="450gsm organic cotton French terry hoodie. Structured fit, pre-shrunk, double-lined hood.",
        price=Decimal("89.99"),
        categoryId=apparel.id,
        active=True
    )
    p5 = Product(
        name="Waterproof Roll-top Backpack",
        description="20L capacity, matte finish waterproof fabric, padded laptop compartment, and quick-access side pockets.",
        price=Decimal("149.99"),
        categoryId=apparel.id,
        active=True
    )
    db.add_all([p1, p2, p3, p4, p5])
    await db.flush()

    # 4. Seed Product Images
    img1 = ProductImage(productId=p1.id, imageUrl="https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&q=80&w=600")
    img2 = ProductImage(productId=p2.id, imageUrl="https://images.unsplash.com/photo-1632292224971-0d45778bd364?auto=format&fit=crop&q=80&w=600")
    img3 = ProductImage(productId=p3.id, imageUrl="https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&q=80&w=600")
    img4 = ProductImage(productId=p4.id, imageUrl="https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&q=80&w=600")
    img5 = ProductImage(productId=p5.id, imageUrl="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&q=80&w=600")
    db.add_all([img1, img2, img3, img4, img5])

    # 5. Seed Inventory
    inv1 = Inventory(productId=p1.id, quantity=45, lowStockThreshold=10)
    inv2 = Inventory(productId=p2.id, quantity=150, lowStockThreshold=10)
    inv3 = Inventory(productId=p3.id, quantity=200, lowStockThreshold=10)
    inv4 = Inventory(productId=p4.id, quantity=8, lowStockThreshold=10) # Low stock alert trigger
    inv5 = Inventory(productId=p5.id, quantity=60, lowStockThreshold=10)
    db.add_all([inv1, inv2, inv3, inv4, inv5])

    await db.commit()
    print("Database seeding completed successfully.")
