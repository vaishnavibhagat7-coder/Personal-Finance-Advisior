from datetime import date
from decimal import Decimal
from app.models import Income, Expense, ExpenseCategory


def test_income_crud_and_isolation(auth_client_a, auth_client_b, app, user_a, user_b):
    """Test full CRUD on income and strict isolation between users."""
    today = date.today()

    # 1. User A adds income
    res = auth_client_a.post('/finance/income/add', data={
        'source': 'Salary',
        'amount': '45000.00',
        'date': today.isoformat(),
        'description': 'Tech Company Salary'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Income record added successfully' in res.data

    with app.app_context():
        inc_a = Income.query.filter_by(user_id=user_a.id).first()
        assert inc_a is not None
        assert inc_a.amount == Decimal('45000.00')
        inc_a_id = inc_a.id

    # 2. User B tries to view or edit User A's income (Forbidden 403)
    res_b_edit = auth_client_b.get(f'/finance/income/edit/{inc_a_id}')
    assert res_b_edit.status_code == 403

    res_b_delete = auth_client_b.post(f'/finance/income/delete/{inc_a_id}')
    assert res_b_delete.status_code == 403

    # User B's income list should be empty
    res_b_list = auth_client_b.get(f'/finance/income?month={today.month}&year={today.year}')
    assert b'Tech Company Salary' not in res_b_list.data

    # 3. User A edits income
    res_edit = auth_client_a.post(f'/finance/income/edit/{inc_a_id}', data={
        'source': 'Salary',
        'amount': '50000.00',
        'date': today.isoformat(),
        'description': 'Updated Salary with Bonus'
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b'Income record updated successfully' in res_edit.data

    with app.app_context():
        updated_inc = Income.query.get(inc_a_id)
        assert updated_inc.amount == Decimal('50000.00')

    # 4. User A deletes income
    res_del = auth_client_a.post(f'/finance/income/delete/{inc_a_id}', follow_redirects=True)
    assert res_del.status_code == 200
    assert b'Income record removed' in res_del.data

    with app.app_context():
        assert Income.query.get(inc_a_id) is None


def test_expense_crud_and_isolation(auth_client_a, auth_client_b, app, user_a, user_b):
    """Test full CRUD on expenses and category assignment."""
    today = date.today()

    with app.app_context():
        cat = ExpenseCategory.query.filter_by(name='Food & Dining').first()
        assert cat is not None
        cat_id = cat.id

    # 1. User A records expense
    res = auth_client_a.post('/finance/expenses/add', data={
        'category_id': cat_id,
        'amount': '1250.50',
        'date': today.isoformat(),
        'payment_method': 'UPI',
        'merchant': 'Blue Tokai Cafe',
        'notes': 'Coffee and sandwiches'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Expense recorded successfully' in res.data

    with app.app_context():
        exp = Expense.query.filter_by(user_id=user_a.id).first()
        assert exp is not None
        assert exp.amount == Decimal('1250.50')
        exp_id = exp.id

    # 2. User B cannot edit or delete User A's expense
    assert auth_client_b.get(f'/finance/expenses/edit/{exp_id}').status_code == 403
    assert auth_client_b.post(f'/finance/expenses/delete/{exp_id}').status_code == 403

    # 3. User A edits expense
    res_edit = auth_client_a.post(f'/finance/expenses/edit/{exp_id}', data={
        'category_id': cat_id,
        'amount': '1500.00',
        'date': today.isoformat(),
        'payment_method': 'UPI',
        'merchant': 'Blue Tokai Cafe',
        'notes': 'Updated bill'
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b'Expense updated successfully' in res_edit.data

    with app.app_context():
        assert Expense.query.get(exp_id).amount == Decimal('1500.00')

    # 4. User A deletes expense
    res_del = auth_client_a.post(f'/finance/expenses/delete/{exp_id}', follow_redirects=True)
    assert res_del.status_code == 200
    assert b'Expense removed' in res_del.data

    with app.app_context():
        assert Expense.query.get(exp_id) is None


def test_invalid_negative_amount_rejection(auth_client_a):
    """Test server-side rejection of negative amounts."""
    res_income = auth_client_a.post('/finance/income/add', data={
        'source': 'Salary',
        'amount': '-500.00',
        'date': date.today().isoformat()
    })
    assert b'Amount must be greater than zero' in res_income.data

    res_expense = auth_client_a.post('/finance/expenses/add', data={
        'category_id': 1,
        'amount': '0.00',
        'date': date.today().isoformat(),
        'payment_method': 'Cash'
    })
    assert b'Amount must be greater than zero' in res_expense.data
