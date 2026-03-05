from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_detail', 'quantity', 'price']
        read_only_fields = ['price']  # price is set automatically from product


class CreateOrderItemSerializer(serializers.Serializer):
    """Used only when creating an order — validates incoming items"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError(f'Product with id {value} does not exist.')

        if product.stock_quantity < 1:
            raise serializers.ValidationError(f'"{product.name}" is out of stock.')
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user_email', 'status',
            'total_price', 'items', 'created_at'
        ]
        read_only_fields = ['total_price', 'created_at', 'user_email']


class CreateOrderSerializer(serializers.Serializer):
    """Handles full order creation with item validation"""
    items = CreateOrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('An order must have at least one item.')

        # Check for duplicate products in the same order
        product_ids = [item['product_id'] for item in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Duplicate products in order. Adjust quantity instead.')
        return value

    def validate(self, attrs):
        """Check that requested quantities don't exceed stock"""
        for item in attrs['items']:
            product = Product.objects.get(id=item['product_id'])
            if item['quantity'] > product.stock_quantity:
                raise serializers.ValidationError(
                    f'Only {product.stock_quantity} units of "{product.name}" available.'
                )
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        items_data = validated_data['items']

        # Create the order
        order = Order.objects.create(user=user)

        # Create each order item and reduce stock
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price       # snapshot price at time of purchase
            )
            # Reduce stock
            product.stock_quantity -= item_data['quantity']
            product.save()

        # Calculate and save total
        order.calculate_total()
        return order