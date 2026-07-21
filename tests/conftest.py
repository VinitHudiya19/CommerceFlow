import pytest

# Force SQLAlchemy to import all models so relationships can configure correctly
from app.users.models import User, Address, RefreshToken
from app.products.models import Product, Category, ProductImage
from app.inventory.models import Inventory
from app.cart.models import Cart, CartItem
from app.orders.models import Order, OrderItem
from app.payments.models import Payment
from app.reviews.models import Review
from app.wishlist.models import WishlistItem

@pytest.fixture(scope="session", autouse=True)
def init_models():
    # This fixture ensures all models are imported at the session start
    pass
