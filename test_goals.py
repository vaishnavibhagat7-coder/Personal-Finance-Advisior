from datetime import date
from decimal import Decimal
from app.models import SavingsGoal, SavingsContribution
from app.extensions import db
from app.utils import shift_months


def test_savings_goal_lifecycle_and_contributions(auth_client_a, app, user_a):
    """Test goal creation, contribution logs, completion trigger, and math."""
    target_dt = shift_months(date.today(), 5)

    # 1. Create goal
    res = auth_client_a.post('/goals/add', data={
        'name': 'Laptop Upgrade',
        'target_amount': '50000.00',
        'current_amount': '10000.00',
        'target_date': target_dt.isoformat(),
        'description': 'MacBook Pro for AI and development',
        'status': 'In Progress'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'created successfully' in res.data

    with app.app_context():
        goal = SavingsGoal.query.filter_by(user_id=user_a.id, name='Laptop Upgrade').first()
        assert goal is not None
        assert goal.target_amount == Decimal('50000.00')
        assert goal.current_amount == Decimal('10000.00')
        assert goal.remaining_amount == Decimal('40000.00')
        assert goal.progress_percentage == Decimal('20.0')
        assert goal.months_remaining == 5
        # Suggested monthly contribution: 40000 / 5 = 8000
        assert goal.suggested_monthly_contribution == Decimal('8000.00')
        goal_id = goal.id

    # 2. Add contribution
    res_contrib = auth_client_a.post(f'/goals/{goal_id}/contribute', data={
        'amount': '15000.00',
        'date': date.today().isoformat(),
        'note': 'Bonus payment deposit'
    }, follow_redirects=True)
    assert res_contrib.status_code == 200
    assert b'Successfully contributed' in res_contrib.data

    with app.app_context():
        g = SavingsGoal.query.get(goal_id)
        assert g.current_amount == Decimal('25000.00')
        assert g.progress_percentage == Decimal('50.0')
        assert len(g.contributions) == 1
        assert g.contributions[0].amount == Decimal('15000.00')

    # 3. Add contribution completing the goal
    auth_client_a.post(f'/goals/{goal_id}/contribute', data={
        'amount': '25000.00',
        'date': date.today().isoformat(),
        'note': 'Final installment'
    }, follow_redirects=True)

    with app.app_context():
        completed_g = SavingsGoal.query.get(goal_id)
        assert completed_g.current_amount == Decimal('50000.00')
        assert completed_g.progress_percentage == Decimal('100.0')
        assert completed_g.status == 'Completed'
        assert completed_g.remaining_amount == Decimal('0.00')


def test_invalid_negative_contribution(auth_client_a, app, user_a):
    """Test rejection of negative or zero contributions."""
    with app.app_context():
        goal = SavingsGoal(
            user_id=user_a.id,
            name='Emergency Fund',
            target_amount=Decimal('100000.00')
        )
        db.session.add(goal)
        db.session.commit()
        goal_id = goal.id

    res = auth_client_a.post(f'/goals/{goal_id}/contribute', data={
        'amount': '-100.00',
        'date': date.today().isoformat()
    }, follow_redirects=True)

    assert b'Contribution error' in res.data
    with app.app_context():
        g = SavingsGoal.query.get(goal_id)
        assert g.current_amount == Decimal('0.00')
