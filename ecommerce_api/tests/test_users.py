import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .factories import UserFactory, StaffUserFactory


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def staff_user(db):
    return StaffUserFactory()


def get_tokens(client, email, password):
    """Helper — logs in and returns access token"""
    response = client.post(reverse('login'), {
        'email': email, 'password': password
    }, format='json')
    return response.data.get('access')


# ── Registration ──────────────────────────────────────────

@pytest.mark.django_db
class TestRegistration:

    def test_register_success(self, client):
        response = client.post(reverse('register'), {
            'username':  'testuser',
            'email':     'test@example.com',
            'password':  'SecurePass123!',
            'password2': 'SecurePass123!',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']

    def test_register_password_mismatch(self, client):
        response = client.post(reverse('register'), {
            'username':  'testuser',
            'email':     'test@example.com',
            'password':  'SecurePass123!',
            'password2': 'WrongPass456!',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, client, user):
        response = client.post(reverse('register'), {
            'username':  'newuser',
            'email':     user.email,       # already taken
            'password':  'SecurePass123!',
            'password2': 'SecurePass123!',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, client):
        response = client.post(reverse('register'), {
            'username':  'testuser',
            'email':     'test@example.com',
            'password':  '123',
            'password2': '123',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Login ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:

    def test_login_success(self, client, user):
        response = client.post(reverse('login'), {
            'email':    user.email,
            'password': 'TestPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, client, user):
        response = client.post(reverse('login'), {
            'email':    user.email,
            'password': 'WrongPassword!',
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        response = client.post(reverse('login'), {
            'email':    'nobody@example.com',
            'password': 'TestPass123!',
        }, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Profile ───────────────────────────────────────────────

@pytest.mark.django_db
class TestProfile:

    def test_get_profile_authenticated(self, client, user):
        token = get_tokens(client, user.email, 'TestPass123!')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.get(reverse('profile'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_get_profile_unauthenticated(self, client):
        response = client.get(reverse('profile'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, client, user):
        token = get_tokens(client, user.email, 'TestPass123!')
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = client.patch(reverse('profile'), {
            'username': 'updated_username'
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'updated_username'