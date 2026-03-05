import factory
from faker import Faker
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order, OrderItem

fake = Faker()
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyFunction(lambda: fake.user_name())
    email    = factory.LazyFunction(lambda: fake.unique.email())
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_staff = False


class StaffUserFactory(UserFactory):
    is_staff = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name        = factory.LazyFunction(lambda: fake.unique.word().capitalize())
    description = factory.LazyFunction(lambda: fake.sentence())


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name           = factory.LazyFunction(lambda: fake.unique.catch_phrase())
    description    = factory.LazyFunction(lambda: fake.paragraph())
    price          = factory.LazyFunction(lambda: round(fake.pyfloat(min_value=1, max_value=1000), 2))
    stock_quantity = factory.LazyFunction(lambda: fake.random_int(min=1, max=100))
    image_url      = factory.LazyFunction(lambda: fake.image_url())
    category       = factory.SubFactory(CategoryFactory)


class OutOfStockProductFactory(ProductFactory):
    stock_quantity = 0


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user        = factory.SubFactory(UserFactory)
    total_price = factory.LazyFunction(lambda: round(fake.pyfloat(min_value=10, max_value=500), 2))
    status      = 'pending'