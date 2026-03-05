from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Order, OrderItem
from .serializers import OrderSerializer, CreateOrderSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/orders/   — list YOUR orders (staff sees all orders)
    POST /api/orders/   — place a new order
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.prefetch_related('items__product').all()
        return Order.objects.prefetch_related('items__product').filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class OrderDetailView(generics.RetrieveAPIView):
    """
    GET /api/orders/<id>/  — view a single order
    Users can only see their own orders, staff can see all
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.prefetch_related('items__product').all()
        return Order.objects.prefetch_related('items__product').filter(user=user)


class CancelOrderView(APIView):
    """
    POST /api/orders/<id>/cancel/  — cancel a pending order
    Restores stock quantities back to products
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # Only owner or staff can cancel
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to cancel this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Can only cancel pending orders
        if order.status != 'pending':
            return Response(
                {'error': f'Cannot cancel an order with status "{order.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Restore stock for each item
        for item in order.items.select_related('product').all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()

        order.status = 'cancelled'
        order.save()

        return Response(
            {'message': f'Order #{order.id} has been cancelled and stock restored.'},
            status=status.HTTP_200_OK
        )


class UpdateOrderStatusView(APIView):
    """
    PATCH /api/orders/<id>/status/  — staff only, update order status
    Body: { "status": "shipped" }
    """
    permission_classes = [IsAuthenticated]

    VALID_TRANSITIONS = {
        'pending':   ['confirmed', 'cancelled'],
        'confirmed': ['shipped',   'cancelled'],
        'shipped':   ['delivered'],
        'delivered': [],
        'cancelled': [],
    }

    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can update order status.'},
                status=status.HTTP_403_FORBIDDEN
            )

        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        allowed = self.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            return Response(
                {
                    'error': f'Cannot transition from "{order.status}" to "{new_status}".',
                    'allowed_transitions': allowed
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        return Response(OrderSerializer(order).data)


class OrderSummaryView(APIView):
    """
    GET /api/orders/summary/  — staff only, quick stats dashboard
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Staff access only.'},
                status=status.HTTP_403_FORBIDDEN
            )

        orders = Order.objects.all()
        summary = {
            'total_orders':    orders.count(),
            'pending':         orders.filter(status='pending').count(),
            'confirmed':       orders.filter(status='confirmed').count(),
            'shipped':         orders.filter(status='shipped').count(),
            'delivered':       orders.filter(status='delivered').count(),
            'cancelled':       orders.filter(status='cancelled').count(),
            'total_revenue':   sum(
                o.total_price for o in orders.filter(status='delivered')
            ),
        }
        return Response(summary)