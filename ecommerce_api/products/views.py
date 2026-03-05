from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductListSerializer,
)
from .permissions import IsStaffOrReadOnly
from .filters import ProductFilter


# ─────────────────────────────────────────
#  CATEGORY VIEWS
# ─────────────────────────────────────────

class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/categories/       — list all categories (public)
    POST /api/products/categories/       — create category (staff only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/categories/<id>/  — view category
    PUT    /api/products/categories/<id>/  — update (staff only)
    DELETE /api/products/categories/<id>/  — delete (staff only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


# ─────────────────────────────────────────
#  PRODUCT VIEWS
# ─────────────────────────────────────────

class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/         — list all products (public, paginated)
    POST /api/products/         — create product (authenticated only)
    """
    queryset = Product.objects.select_related('category').all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        # Use lightweight serializer for list, full for create
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/<id>/  — view product details (public)
    PUT    /api/products/<id>/  — update product (authenticated)
    PATCH  /api/products/<id>/  — partial update (authenticated)
    DELETE /api/products/<id>/  — delete product (authenticated)
    """
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ProductSearchView(generics.ListAPIView):
    """
    GET /api/products/search/?q=<term>
    Searches across name, description, and category name
    Supports partial matches
    """
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Product.objects.none()

        return Product.objects.select_related('category').filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['query'] = request.query_params.get('q', '')
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'query': request.query_params.get('q', ''),
            'count': queryset.count(),
            'results': serializer.data
        })


class LowStockView(generics.ListAPIView):
    """
    GET /api/products/low-stock/   — staff only, products with stock < 10
    """
    serializer_class = ProductListSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        threshold = int(self.request.query_params.get('threshold', 10))
        return Product.objects.filter(stock_quantity__lte=threshold).order_by('stock_quantity')