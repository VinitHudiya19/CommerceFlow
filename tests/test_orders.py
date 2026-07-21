import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from app.orders.service import place_order
from app.orders.schemas import OrderRequest
from app.users.models import User, Address
from app.cart.models import Cart, CartItem
from app.products.models import Product
from app.inventory.models import Inventory
from app.common.exceptions import BadRequestException

@pytest.mark.asyncio
async def test_place_order_user_unverified():
    # Arrange
    db = MagicMock()
    db.execute = AsyncMock()
    user = User(id=1, email="test@example.com", verified=False)
    
    mock_user_result = MagicMock()
    mock_user_result.scalars().first.return_value = user
    db.execute.return_value = mock_user_result

    request = OrderRequest(addressId=1)

    # Act & Assert
    with pytest.raises(BadRequestException) as exc:
        await place_order(user_id=1, request=request, db=db)
    assert "verify your email address" in str(exc.value.message)

@pytest.mark.asyncio
async def test_place_order_cart_empty():
    # Arrange
    db = MagicMock()
    db.execute = AsyncMock()
    user = User(id=1, email="test@example.com", verified=True)
    cart = Cart(id=10, userId=1, items=[]) # Empty Cart

    # Setup database mocks sequentially
    mock_res_user = MagicMock()
    mock_res_user.scalars().first.return_value = user
    
    mock_res_cart = MagicMock()
    mock_res_cart.scalars().first.return_value = cart
    
    db.execute.side_effect = [mock_res_user, mock_res_cart]

    request = OrderRequest(addressId=1)

    # Act & Assert
    with pytest.raises(BadRequestException) as exc:
        await place_order(user_id=1, request=request, db=db)
    assert "cart is empty" in str(exc.value.message)

@pytest.mark.asyncio
@patch("app.orders.service.process_order_placement_task")
async def test_place_order_successful(mock_celery_task):
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    user = User(id=1, email="test@example.com", verified=True)
    
    address = Address(
        id=2, 
        userId=1, 
        label="Home", 
        addressLine1="123 Main St", 
        city="Delhi", 
        state="Delhi", 
        pincode="110001"
    )
    
    product = Product(id=20, name="Sample Product", price=Decimal("100.00"), categoryId=5)
    cart_item = CartItem(id=30, cartId=10, productId=20, quantity=2, unitPrice=Decimal("100.00"), product=product)
    cart = Cart(id=10, userId=1, items=[cart_item])
    
    inventory = Inventory(id=40, productId=20, quantity=10, lowStockThreshold=5)

    # Database returns mock objects in order of queries
    mock_res_user = MagicMock()
    mock_res_user.scalars().first.return_value = user
    
    mock_res_cart = MagicMock()
    mock_res_cart.scalars().first.return_value = cart
    
    mock_res_addr = MagicMock()
    mock_res_addr.scalars().first.return_value = address
    
    mock_res_inv = MagicMock()
    mock_res_inv.scalars().first.return_value = inventory

    added_entities = []
    def mock_add(entity):
        added_entities.append(entity)
    db.add.side_effect = mock_add

    from datetime import datetime
    async def mock_flush():
        for entity in added_entities:
            if getattr(entity, "id", None) is None:
                entity.id = 100
            if getattr(entity, "createdAt", None) is None:
                entity.createdAt = datetime.utcnow()
    db.flush = mock_flush
    db.commit = mock_flush # Also run on commit to capture order_items

    db.execute.side_effect = [
        mock_res_user, # findUser
        mock_res_cart, # getCart
        mock_res_addr, # findAddress
        mock_res_inv   # findInventory
    ]

    request = OrderRequest(addressId=2)

    # Act
    response = await place_order(user_id=1, request=request, db=db)

    # Assert
    assert response is not None
    assert response.totalAmount == Decimal("200.00")
    assert response.status == "PENDING"
    assert "Home: 123 Main St" in response.deliveryAddress
    assert len(response.items) == 1
    assert response.items[0].productName == "Sample Product"

    # Celery task should be triggered
    mock_celery_task.delay.assert_called_once_with(response.id)
