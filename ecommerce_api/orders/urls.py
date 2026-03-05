from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    CancelOrderView,
    UpdateOrderStatusView,
    OrderSummaryView,
)

urlpatterns = [
    path('',                         OrderListCreateView.as_view(),  name='order_list'),
    path('<int:pk>/',                 OrderDetailView.as_view(),      name='order_detail'),
    path('<int:pk>/cancel/',          CancelOrderView.as_view(),      name='order_cancel'),
    path('<int:pk>/status/',          UpdateOrderStatusView.as_view(),name='order_status'),
    path('summary/',                  OrderSummaryView.as_view(),     name='order_summary'),
]
