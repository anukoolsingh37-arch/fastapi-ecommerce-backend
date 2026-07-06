from datetime import datetime
from database import engine, SessionLocal
from auth.hashing import Hash
import models


def seed_data():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Category).count() == 0:
            categories = [
                {'name': 'Electronics', 'description': 'Phones, laptops, and smart devices.'},
                {'name': 'Fashion', 'description': 'Clothing, shoes, and accessories.'},
                {'name': 'Home', 'description': 'Home decor, kitchen, and furniture.'},
                {'name': 'Accessories', 'description': 'Bags, watches, and travel essentials.'}
            ]
            for category in categories:
                db.add(models.Category(**category))
            db.commit()

        category_index = {c.name: c.id for c in db.query(models.Category).all()}

        if db.query(models.Product).count() == 0:
            products = [
                {
                    'title': 'Smart Noise-Cancelling Headphones',
                    'description': 'Premium audio with active noise cancellation and 30-hour battery life.',
                    'price': 129.99,
                    'stock': 24,
                    'image': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Electronics'],
                    'featured': True
                },
                {
                    'title': 'Classic Leather Sneakers',
                    'description': 'Comfortable everyday sneakers with soft cushioning and modern style.',
                    'price': 79.99,
                    'stock': 18,
                    'image': 'https://images.unsplash.com/photo-1528701800489-1c0f0ad0fd13?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Fashion'],
                    'featured': True
                },
                {
                    'title': 'Retro Analog Watch',
                    'description': 'Timeless design with a premium leather strap and water resistance.',
                    'price': 149.00,
                    'stock': 12,
                    'image': 'https://images.unsplash.com/photo-1518546305920-bcc7af1ca392?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Accessories'],
                    'featured': False
                },
                {
                    'title': 'Wireless Bluetooth Speaker',
                    'description': 'Compact speaker with rich bass and built-in voice assistant support.',
                    'price': 59.50,
                    'stock': 35,
                    'image': 'https://images.unsplash.com/photo-1517309114536-4192b98ab91a?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Electronics'],
                    'featured': False
                },
                {
                    'title': 'Minimal Desk Lamp',
                    'description': 'Sleek illumination with adjustable brightness and warm LED lighting.',
                    'price': 44.75,
                    'stock': 26,
                    'image': 'https://images.unsplash.com/photo-1523413651479-597eb2da0ad6?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Home'],
                    'featured': False
                },
                {
                    'title': 'Travel Backpack',
                    'description': 'Durable carry-on backpack with padded laptop sleeve and multiple pockets.',
                    'price': 69.99,
                    'stock': 19,
                    'image': 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Accessories'],
                    'featured': True
                },
                {
                    'title': 'Portable Power Bank',
                    'description': 'High-capacity USB-C power bank for long trips and quick charging.',
                    'price': 34.99,
                    'stock': 27,
                    'image': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Electronics'],
                    'featured': True
                },
                {
                    'title': 'Cashmere Blend Scarf',
                    'description': 'Soft and warm scarf with a luxurious feel for everyday wear.',
                    'price': 39.50,
                    'stock': 22,
                    'image': 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Fashion'],
                    'featured': False
                },
                {
                    'title': 'Modern Ceramic Vase',
                    'description': 'Minimal matte vase that works perfectly on shelves and tables.',
                    'price': 29.99,
                    'stock': 14,
                    'image': 'https://images.unsplash.com/photo-1519710164239-da123dc03ef4?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Home'],
                    'featured': False
                },
                {
                    'title': 'Stylish Sunglasses',
                    'description': 'UV protection sunglasses with a lightweight frame.',
                    'price': 54.00,
                    'stock': 30,
                    'image': 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80',
                    'category_id': category_index['Accessories'],
                    'featured': True
                }
            ]
            for product in products:
                db.add(models.Product(**product))
            db.commit()

        product_map = {p.title: p.id for p in db.query(models.Product).all()}
        if db.query(models.Review).count() == 0:
            reviews = [
                {'product_id': product_map.get('Smart Noise-Cancelling Headphones'), 'user': 'alex@example.com', 'rating': 5, 'comment': 'Fantastic sound and very comfortable.'},
                {'product_id': product_map.get('Classic Leather Sneakers'), 'user': 'maria@example.com', 'rating': 4, 'comment': 'Great style, a little tight at first.'},
                {'product_id': product_map.get('Wireless Bluetooth Speaker'), 'user': 'jordan@example.com', 'rating': 5, 'comment': 'Exceptional bass for a compact speaker.'},
                {'product_id': product_map.get('Minimal Desk Lamp'), 'user': 'sasha@example.com', 'rating': 4, 'comment': 'Looks great on my desk and brightens the room.'},
                {'product_id': product_map.get('Travel Backpack'), 'user': 'nina@example.com', 'rating': 5, 'comment': 'Very durable and holds everything I need.'}
            ]
            for review in reviews:
                if review['product_id']:
                    db.add(models.Review(**review))
            db.commit()

        if db.query(models.Coupon).count() == 0:
            coupons = [
                {'code': 'WELCOME10', 'description': '10% off your first purchase', 'discount_percent': 10.0, 'active': True, 'max_uses': 100},
                {'code': 'SPRING15', 'description': '15% off selected items', 'discount_percent': 15.0, 'active': True, 'max_uses': 50},
                {'code': 'SAVE20', 'description': '20% off when you spend $100 or more', 'discount_percent': 20.0, 'active': True, 'max_uses': 30}
            ]
            for coupon in coupons:
                db.add(models.Coupon(**coupon))
            db.commit()

        if not db.query(models.User).filter(models.User.username == 'admin').first():
            db.add(models.User(
                username='admin',
                email='admin@example.com',
                password=Hash.bcrypt('adminpass'),
                is_admin=True
            ))
            db.commit()

        if not db.query(models.User).filter(models.User.username == 'demo').first():
            db.add(models.User(
                username='demo',
                email='demo@example.com',
                password=Hash.bcrypt('demopass'),
                is_admin=False
            ))
            db.commit()

        demo_user = db.query(models.User).filter(models.User.username == 'demo').first()
        if demo_user and db.query(models.Order).filter(models.Order.customer == demo_user.email).count() == 0:
            starter_product = db.query(models.Product).filter(models.Product.title == 'Portable Power Bank').first()
            if starter_product and starter_product.stock > 0:
                demo_order = models.Order(
                    total_price=starter_product.price,
                    discount_amount=0.0,
                    coupon_code=None,
                    customer=demo_user.email,
                    customer_id=demo_user.id,
                    status='delivered'
                )
                db.add(demo_order)
                db.flush()
                order_item = models.OrderItem(
                    order_id=demo_order.id,
                    product_id=starter_product.id,
                    product_name=starter_product.title,
                    quantity=1,
                    price=starter_product.price
                )
                db.add(order_item)
                starter_product.stock -= 1
                db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    seed_data()
    print('Database seeded successfully.')
