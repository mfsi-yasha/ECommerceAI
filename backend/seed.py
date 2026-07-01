import sys
import os

# Ensure the app module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Product, ProductMetadata, Base

# Make sure tables exist (they should be created by alembic, but just in case)
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(Product).count() > 0:
        print("Database already seeded. Cleaning up old data...")
        db.query(Product).delete()
        db.commit()

    products_data = [
        # Mobiles
        {
            "name": "iPhone 15 Pro",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Apple",
                "color": "Titanium Blue",
                "storage": "256GB",
                "price": "1099",
                "image_url": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Samsung",
                "color": "Titanium Black",
                "storage": "512GB",
                "price": "1299",
                "image_url": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Google Pixel 8 Pro",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Google",
                "color": "Obsidian",
                "storage": "128GB",
                "price": "999",
                "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351cb31b?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "OnePlus 12",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "OnePlus",
                "color": "Flowy Emerald",
                "storage": "256GB",
                "price": "799",
                "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351cb31b?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Xiaomi 14 Pro",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Xiaomi",
                "color": "Black",
                "storage": "256GB",
                "price": "899",
                "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351cb31b?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Sony Xperia 1 V",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Sony",
                "color": "Khaki Green",
                "storage": "256GB",
                "price": "1199",
                "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351cb31b?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Motorola Edge 50 Pro",
            "type": "Electronics",
            "subtype": "Mobile",
            "meta": {
                "brand": "Motorola",
                "color": "Luxe Lavender",
                "storage": "256GB",
                "price": "699",
                "image_url": "https://images.unsplash.com/photo-1598327105666-5b89351cb31b?auto=format&fit=crop&w=500&q=60"
            }
        },
        # Laptops
        {
            "name": "MacBook Pro 16 M3 Max",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "Apple",
                "cpu": "M3 Max",
                "ram": "36GB",
                "storage": "1TB SSD",
                "price": "3499",
                "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Dell XPS 15",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "Dell",
                "cpu": "Intel Core i9",
                "ram": "32GB",
                "storage": "1TB SSD",
                "price": "2299",
                "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Lenovo ThinkPad X1 Carbon Gen 11",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "Lenovo",
                "cpu": "Intel Core i7",
                "ram": "16GB",
                "storage": "512GB SSD",
                "price": "1799",
                "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "ASUS ROG Zephyrus G14",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "ASUS",
                "cpu": "AMD Ryzen 9",
                "ram": "16GB",
                "storage": "1TB SSD",
                "price": "1599",
                "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "HP Spectre x360",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "HP",
                "cpu": "Intel Core i7",
                "ram": "16GB",
                "storage": "1TB SSD",
                "price": "1499",
                "image_url": "https://images.unsplash.com/photo-1593642702749-b7d2a804fbcf?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Razer Blade 15",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "Razer",
                "cpu": "Intel Core i7",
                "ram": "16GB",
                "storage": "1TB SSD",
                "price": "2499",
                "image_url": "https://images.unsplash.com/photo-1593642532842-98d0fd5ebc1a?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Acer Swift 3",
            "type": "Electronics",
            "subtype": "Laptop",
            "meta": {
                "brand": "Acer",
                "cpu": "AMD Ryzen 7",
                "ram": "8GB",
                "storage": "512GB SSD",
                "price": "749",
                "image_url": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?auto=format&fit=crop&w=500&q=60"
            }
        },
        # Clothes
        {
            "name": "Men's Classic White T-Shirt",
            "type": "Apparel",
            "subtype": "Shirt",
            "meta": {
                "brand": "Basics",
                "size": "M",
                "color": "White",
                "material": "100% Cotton",
                "price": "25",
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Women's Denim Jacket",
            "type": "Apparel",
            "subtype": "Jacket",
            "meta": {
                "brand": "Levi's",
                "size": "S",
                "color": "Light Blue",
                "material": "Denim",
                "price": "85",
                "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Unisex Cozy Hoodie",
            "type": "Apparel",
            "subtype": "Sweatshirt",
            "meta": {
                "brand": "ComfortWear",
                "size": "L",
                "color": "Heather Grey",
                "material": "Cotton Blend",
                "price": "55",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Men's Slim Fit Jeans",
            "type": "Apparel",
            "subtype": "Pants",
            "meta": {
                "brand": "Wrangler",
                "size": "32x32",
                "color": "Dark Wash",
                "material": "Denim",
                "price": "60",
                "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Women's Summer Floral Dress",
            "type": "Apparel",
            "subtype": "Dress",
            "meta": {
                "brand": "SunnyDays",
                "size": "M",
                "color": "Yellow/Floral",
                "material": "Viscose",
                "price": "45",
                "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=500&q=60"
            }
        },
        {
            "name": "Running Sneakers",
            "type": "Apparel",
            "subtype": "Shoes",
            "meta": {
                "brand": "Nike",
                "size": "10",
                "color": "Black/White",
                "material": "Mesh",
                "price": "120",
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=500&q=60"
            }
        },
    ]

    for item in products_data:
        product = Product(
            name=item["name"],
            type=item["type"],
            subtype=item["subtype"]
        )
        db.add(product)
        db.flush() # get the product id

        for k, v in item["meta"].items():
            meta = ProductMetadata(
                product_id=product.id,
                meta_key=k,
                meta_value=str(v)
            )
            db.add(meta)
            
    db.commit()
    print(f"Successfully seeded {len(products_data)} products.")

if __name__ == "__main__":
    seed()
