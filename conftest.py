import pytest
from datetime import date
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import User, ExpenseCategory
from app.utils import seed_default_categories


@pytest.fixture
def app():
    """Create application configured for testing with in-memory database."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        seed_default_categories(db.session, ExpenseCategory)
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def user_a(app):
    """Primary test user."""
    with app.app_context():
        user = User(
            email='alice@example.com',
            full_name='Alice Smith',
            occupation='Salaried Professional',
            currency='₹',
            monthly_income_target=Decimal('50000.00'),
            monthly_savings_target=Decimal('15000.00'),
            financial_priorities='Save for emergency buffer'
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email='alice@example.com').first()


@pytest.fixture
def user_b(app):
    """Secondary test user for verifying strict data isolation."""
    with app.app_context():
        user = User(
            email='bob@example.com',
            full_name='Bob Jones',
            occupation='Student',
            currency='₹',
            monthly_income_target=Decimal('10000.00'),
            monthly_savings_target=Decimal('2000.00')
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email='bob@example.com').first()


@pytest.fixture
def auth_client_a(client, user_a):
    """Client authenticated as User A."""
    client.post('/login', data={'email': 'alice@example.com', 'password': 'Password123!'}, follow_redirects=True)
    return client


@pytest.fixture
def auth_client_b(app, user_b):
    """Client authenticated as User B."""
    c = app.test_client()
    c.post('/login', data={'email': 'bob@example.com', 'password': 'Password123!'}, follow_redirects=True)
    return c
