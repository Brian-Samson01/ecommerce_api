from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductSearchView,
    LowStockView,
)

urlpatterns = [
    # Categories
    path('categories/',      CategoryListCreateView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(),  name='category_detail'),

    # Products
    path('',                 ProductListCreateView.as_view(),  name='product_list'),
    path('<int:pk>/',        ProductDetailView.as_view(),      name='product_detail'),

    # Search & Utility
    path('search/',          ProductSearchView.as_view(),      name='product_search'),
    path('low-stock/',       LowStockView.as_view(),           name='low_stock'),
]