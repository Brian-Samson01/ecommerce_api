import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .factories import UserFactory, StaffUserFactory, ProductFactory, OutOfStockProductFactory


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
def product(db):
    return ProductFactory(price=100, stock_quantity=10)


def auth_client(client, user):
    response = client.post(reverse('login'), {
        'email': user.email, 'password': 'TestPass123!'
    }, format='json')
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ── Place Orders ──────────────────────────────────────────

@pytest.mark.django_db
class TestPlaceOrder:

    def test_place_order_success(self, client, user, product):
        auth_client(client, user)
        response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 2}]
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['total_price'] == '200.00'

    def test_stock_reduced_after_order(self, client, user, product):
        auth_client(client, user)
        client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 3}]
        }, format='json')
        product.refresh_from_db()
        assert product.stock_quantity == 7  # 10 - 3

    def test_order_unauthenticated(self, client, product):
        response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_order_out_of_stock(self, client, user, db):
        out_of_stock = OutOfStockProductFactory()
        auth_client(client, user)
        response = client.post(reverse('order_list'), {
            'items': [{'product_id': out_of_stock.id, 'quantity': 1}]
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_exceeds_stock(self, client, user, product):
        auth_client(client, user)
        response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 999}]
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_empty_items(self, client, user):
        auth_client(client, user)
        response = client.post(reverse('order_list'), {
            'items': []
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Order Visibility ──────────────────────────────────────

@pytest.mark.django_db
class TestOrderVisibility:

    def test_user_sees_only_own_orders(self, client, db):
        user1 = UserFactory()
        user2 = UserFactory()
        product = ProductFactory(stock_quantity=20)

        # user1 places an order
        auth_client(client, user1)
        client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')

        # user2 should see 0 orders
        auth_client(client, user2)
        response = client.get(reverse('order_list'))
        assert response.data['count'] == 0

    def test_staff_sees_all_orders(self, client, db):
        user = UserFactory()
        staff = StaffUserFactory()
        product = ProductFactory(stock_quantity=20)

        auth_client(client, user)
        client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')

        auth_client(client, staff)
        response = client.get(reverse('order_list'))
        assert response.data['count'] >= 1


# ── Cancel Orders ─────────────────────────────────────────

@pytest.mark.django_db
class TestCancelOrder:

    def test_cancel_pending_order(self, client, user, product):
        auth_client(client, user)
        order_response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 2}]
        }, format='json')
        order_id = order_response.data['id']

        response = client.post(reverse('order_cancel', kwargs={'pk': order_id}))
        assert response.status_code == status.HTTP_200_OK

        # Stock should be restored
        product.refresh_from_db()
        assert product.stock_quantity == 10

    def test_cancel_other_users_order(self, client, db):
        user1 = UserFactory()
        user2 = UserFactory()
        product = ProductFactory(stock_quantity=10)

        auth_client(client, user1)
        order_response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')
        order_id = order_response.data['id']

        # user2 tries to cancel user1's order
        auth_client(client, user2)
        response = client.post(reverse('order_cancel', kwargs={'pk': order_id}))
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Status Transitions ────────────────────────────────────

@pytest.mark.django_db
class TestStatusTransitions:

    def test_valid_status_transition(self, client, staff, product):
        user = UserFactory()
        auth_client(client, user)
        order_response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')
        order_id = order_response.data['id']

        auth_client(client, staff)
        response = client.patch(
            reverse('order_status', kwargs={'pk': order_id}),
            {'status': 'confirmed'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'

    def test_invalid_status_transition(self, client, staff, product):
        user = UserFactory()
        auth_client(client, user)
        order_response = client.post(reverse('order_list'), {
            'items': [{'product_id': product.id, 'quantity': 1}]
        }, format='json')
        order_id = order_response.data['id']

        auth_client(client, staff)
        response = client.patch(
            reverse('order_status', kwargs={'pk': order_id}),
            {'status': 'delivered'},  # can't skip from pending → delivered
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'allowed_transitions' in response.data