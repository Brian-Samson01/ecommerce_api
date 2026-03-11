# Ecommerce API

REST API for a simple ecommerce platform built with Django and Django REST Framework. It provides JWT authentication, product catalog management, and order processing with stock updates.

**Features**
- JWT auth: register, login, refresh, logout
- User profile and password change
- Products and categories with search, filters, ordering
- Low stock report for staff
- Orders with item validation, stock updates, status workflow, summary stats
- Pagination on list endpoints (page size 10)

**Tech Stack**
- Django 5.2, Django REST Framework
- SimpleJWT, django-filter
- SQLite (default)
- pytest

**Quick Start**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` in the project root:
```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000
```

Run migrations and start the server:
```powershell
python manage.py migrate
python manage.py runserver
```

Optional admin user:
```powershell
python manage.py createsuperuser
```

**Environment Variables**
- `SECRET_KEY` required when `DEBUG=False`
- `DEBUG` set to `True` or `False`
- `ALLOWED_HOSTS` comma-separated list (required when `DEBUG=False`)
- `CSRF_TRUSTED_ORIGINS` comma-separated list (optional)

**Authentication**
Use the access token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

**API Endpoints**

Users
- `POST /api/users/register/` - create account and return tokens
- `POST /api/users/login/` - get access and refresh tokens
- `POST /api/users/token/refresh/` - refresh access token
- `POST /api/users/logout/` - blacklist refresh token
- `GET /api/users/profile/` - view profile
- `PUT /api/users/profile/` - update profile
- `POST /api/users/change-password/` - change password
- `GET /api/users/` - staff sees all users, non-staff sees only self

Products
- `GET /api/products/` - list products (paginated)
- `POST /api/products/` - create product (authenticated)
- `GET /api/products/<id>/` - product detail
- `PUT/PATCH/DELETE /api/products/<id>/` - update or delete (authenticated)
- `GET /api/products/categories/` - list categories
- `POST /api/products/categories/` - create category (staff)
- `GET /api/products/categories/<id>/` - category detail
- `PUT/DELETE /api/products/categories/<id>/` - update or delete (staff)
- `GET /api/products/search/?q=term` - search products
- `GET /api/products/low-stock/?threshold=10` - low stock report (staff)

Product Filters and Ordering
- `min_price` and `max_price` (price range)
- `category` or `category_id`
- `in_stock=true|false`
- `search` (name, description, category name)
- `ordering=price`, `ordering=-price`, `ordering=created_at`

Orders
- `GET /api/orders/` - list your orders (staff sees all)
- `POST /api/orders/` - create order
- `GET /api/orders/<id>/` - order detail
- `POST /api/orders/<id>/cancel/` - cancel pending order
- `PATCH /api/orders/<id>/status/` - update status (staff)
- `GET /api/orders/summary/` - summary stats (staff)

Order Status Transitions
- `pending -> confirmed, cancelled`
- `confirmed -> shipped, cancelled`
- `shipped -> delivered`
- `delivered -> (no transitions)`
- `cancelled -> (no transitions)`

**Request Examples**

Register
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo\",\"email\":\"demo@example.com\",\"password\":\"StrongPass123!\",\"password2\":\"StrongPass123!\"}"
```

Login
```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"demo@example.com\",\"password\":\"StrongPass123!\"}"
```

Create Order
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"items\":[{\"product_id\":1,\"quantity\":2},{\"product_id\":3,\"quantity\":1}]}"
```

**Testing**
```powershell
pytest
```
