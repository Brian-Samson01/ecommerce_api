import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .factories import UserFactory, StaffUserFactory, CategoryFactory, ProductFactory, OutOfStockProductFactory


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def user(db):
    return UserFactory()

@pytest.fixture
def staff(db):
    return StaffUserFactory()

@pytest.fixture
def category(db):
    return CategoryFactory()

@pytest.fixture
def product(db):
    return ProductFactory()


def auth_client(client, user):
    response = client.post(reverse('login'), {
        'email': user.email, 'password': 'TestPass123!'
    }, format='json')
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ── Product Listing ───────────────────────────────────────

@pytest.mark.django_db
class TestProductListing:

    def test_list_products_public(self, client, product):
        response = client.get(reverse('product_list'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_pagination_present(self, client, db):
        ProductFactory.create_batch(15)
        response = client.get(reverse('product_list'))
        assert 'next' in response.data
        assert len(response.data['results']) == 10  # PAGE_SIZE

    def test_filter_by_category(self, client, db):
        cat = CategoryFactory(name='Gadgets')
        ProductFactory.create_batch(3, category=cat)
        ProductFactory.create_batch(2)   # different category
        response = client.get(reverse('product_list') + '?category=Gadgets')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_filter_by_price_range(self, client, db):
        ProductFactory(price=50)
        ProductFactory(price=150)
        ProductFactory(price=300)
        response = client.get(reverse('product_list') + '?min_price=100&max_price=200')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_filter_in_stock(self, client, db):
        ProductFactory.create_batch(3)            # in stock
        OutOfStockProductFactory.create_batch(2)  # out of stock
        response = client.get(reverse('product_list') + '?in_stock=true')
        assert response.data['count'] == 3


# ── Product Search ────────────────────────────────────────

@pytest.mark.django_db
class TestProductSearch:

    def test_search_by_name(self, client, db):
        ProductFactory(name='Wireless Headphones')
        ProductFactory(name='Running Shoes')
        response = client.get(reverse('product_search') + '?q=wireless')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_search_empty_query_returns_none(self, client, db):
        ProductFactory.create_batch(3)
        response = client.get(reverse('product_search') + '?q=')
        assert response.data['count'] == 0

    def test_search_partial_match(self, client, db):
        ProductFactory(name='Bluetooth Speaker')
        response = client.get(reverse('product_search') + '?q=blue')
        assert response.data['count'] == 1


# ── Product CRUD ──────────────────────────────────────────

@pytest.mark.django_db
class TestProductCRUD:

    def test_create_product_authenticated(self, client, user, category):
        auth_client(client, user)
        response = client.post(reverse('product_list'), {
            'name':           'Test Product',
            'description':    'A test product',
            'price':          '49.99',
            'stock_quantity': 10,
            'category':       category.id,
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Test Product'

    def test_create_product_unauthenticated(self, client, category):
        response = client.post(reverse('product_list'), {
            'name':     'Test Product',
            'price':    '49.99',
            'category': category.id,
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_negative_price(self, client, user, category):
        auth_client(client, user)
        response = client.post(reverse('product_list'), {
            'name':           'Bad Product',
            'price':          '-10.00',
            'stock_quantity': 5,
            'category':       category.id,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_product(self, client, user, product):
        auth_client(client, user)
        response = client.patch(
            reverse('product_detail', kwargs={'pk': product.id}),
            {'price': '199.99'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['price'] == '199.99'

    def test_delete_product(self, client, user, product):
        auth_client(client, user)
        response = client.delete(
            reverse('product_detail', kwargs={'pk': product.id})
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_nonexistent_product(self, client):
        response = client.get(reverse('product_detail', kwargs={'pk': 99999}))
        assert response.status_code == status.HTTP_404_NOT_FOUND