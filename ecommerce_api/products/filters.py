import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    # Price range  → /api/products/?min_price=10&max_price=100
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    # Category by name  → /api/products/?category=electronics
    category = django_filters.CharFilter(
        field_name='category__name', lookup_expr='iexact'
    )

    # Category by id  → /api/products/?category_id=3
    category_id = django_filters.NumberFilter(field_name='category__id')

    # Stock availability  → /api/products/?in_stock=true
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Product
        fields = ['category', 'category_id', 'min_price', 'max_price', 'in_stock']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)