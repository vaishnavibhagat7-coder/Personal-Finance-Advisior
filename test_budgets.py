from datetime import date
from decimal import Decimal
from app.models import Budget, Expense, ExpenseCategory, Income
from app.extensions import db


def test_budget_thresholds_and_overspending(auth_client_a, app, user_a):
    """Test budget creation and 4-tier health threshold evaluation."""
    today = date.today()

    with app.app_context():
        food_cat = ExpenseCategory.query.filter_by(name='Food & Dining').first()
        assert food_cat is not None
        cat_id = food_cat.id

    # 1. Set budget limit of 10,000 for Food & Dining
    res = auth_client_a.post('/budgets/set', data={
        'category_id': cat_id,
        'month': today.month,
        'year': today.year,
        'amount_limit': '10000.00'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Budget saved successfully' in res.data or b'Updated budget limit' in res.data

    # Helper function to check status on index
    def get_budget_status(spend_amt):
        with app.app_context():
            Expense.query.filter_by(user_id=user_a.id).delete()
            if spend_amt > 0:
                db.session.add(Expense(
                    user_id=user_a.id,
                    category_id=cat_id,
                    amount=Decimal(str(spend_amt)),
                    date=today,
                    payment_method='UPI'
                ))
            db.session.commit()
        return auth_client_a.get(f'/budgets/?month={today.month}&year={today.year}')

    # Tier 1: Normal (< 75%) -> e.g. 5,000 spent (50%)
    res_normal = get_budget_status(5000.00)
    assert b'Normal' in res_normal.data

    # Tier 2: Approaching Limit (75% to < 90%) -> e.g. 8,000 spent (80%)
    res_approaching = get_budget_status(8000.00)
    assert b'Approaching Limit' in res_approaching.data

    # Tier 3: Near Limit (90% to 100%) -> e.g. 9,500 spent (95%)
    res_near = get_budget_status(9500.00)
    assert b'Near Limit' in res_near.data

    # Tier 4: Overspending (> 100%) -> e.g. 11,000 spent (110%)
    res_over = get_budget_status(11000.00)
    assert b'Overspending' in res_over.data


def test_auto_generate_budget_engine(auth_client_a, app, user_a):
    """Test rule-based budget suggestion generator based on income & occupation."""
    today = date.today()

    # Record 60,000 income
    with app.app_context():
        db.session.add(Income(
            user_id=user_a.id,
            source='Salary',
            amount=Decimal('60000.00'),
            date=today
        ))
        db.session.commit()

    res = auth_client_a.post('/budgets/auto-generate', data={
        'month': today.month,
        'year': today.year
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Generated' in res.data
    assert b'budget limits' in res.data

    with app.app_context():
        budgets = Budget.query.filter_by(user_id=user_a.id, month=today.month, year=today.year).all()
        assert len(budgets) > 0
        total_budgeted = sum(b.amount_limit for b in budgets)
        # Never allocate more than available income!
        assert total_budgeted <= Decimal('60000.00')
