from app.models import User


def test_user_registration(client, app):
    """Test successful user registration."""
    res = client.post('/register', data={
        'full_name': 'Charlie Brown',
        'email': 'charlie@example.com',
        'occupation': 'Student',
        'currency': '₹',
        'password': 'SecurePassword123!',
        'confirm_password': 'SecurePassword123!'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Registration successful' in res.data
    with app.app_context():
        u = User.query.filter_by(email='charlie@example.com').first()
        assert u is not None
        assert u.full_name == 'Charlie Brown'
        assert u.occupation == 'Student'
        assert u.check_password('SecurePassword123!') is True


def test_duplicate_email_registration(client, user_a):
    """Test registering with an already existing email is rejected."""
    res = client.post('/register', data={
        'full_name': 'Duplicate Alice',
        'email': 'alice@example.com',
        'occupation': 'Student',
        'currency': '₹',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'already exists' in res.data


def test_login_success(client, user_a):
    """Test login with correct credentials."""
    res = client.post('/login', data={
        'email': 'alice@example.com',
        'password': 'Password123!'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Welcome back, Alice Smith' in res.data
    assert b'Financial Overview' in res.data


def test_login_incorrect_password(client, user_a):
    """Test login failure with wrong password."""
    res = client.post('/login', data={
        'email': 'alice@example.com',
        'password': 'WrongPassword!'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Invalid email or password' in res.data


def test_protected_routes_redirect_unauthenticated(client):
    """Test that unauthenticated access redirects to login."""
    protected_urls = [
        '/dashboard/',
        '/finance/expenses',
        '/finance/income',
        '/budgets/',
        '/advisor/',
        '/goals/',
        '/reports/',
        '/profile/'
    ]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code in (302, 301)
        assert '/login' in res.headers['Location']


def test_logout(auth_client_a):
    """Test user logout."""
    res = auth_client_a.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'You have been securely signed out' in res.data
