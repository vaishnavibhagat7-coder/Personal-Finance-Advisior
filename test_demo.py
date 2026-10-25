from app.models import User, Income, Expense, Budget, SavingsGoal
from seed_demo import seed_demo_data, reset_demo_data


def test_seed_demo_and_reset(app):
    """Test seeding demo data for demo@finwise.ai and then safely resetting it."""
    with app.app_context():
        # Seed demo data
        seed_demo_data(app)

        demo_user = User.query.filter_by(email="demo@finwise.ai").first()
        assert demo_user is not None
        assert demo_user.full_name == "Aarav Sharma"
        assert demo_user.occupation == "Salaried Professional"

        incomes = Income.query.filter_by(user_id=demo_user.id).all()
        assert len(incomes) >= 6

        expenses = Expense.query.filter_by(user_id=demo_user.id).all()
        assert len(expenses) > 0

        budgets = Budget.query.filter_by(user_id=demo_user.id).all()
        assert len(budgets) > 0

        goals = SavingsGoal.query.filter_by(user_id=demo_user.id).all()
        assert len(goals) >= 3

        # Now test clean reset
        reset_demo_data(app)
        assert User.query.filter_by(email="demo@finwise.ai").first() is None
        assert Income.query.filter_by(user_id=demo_user.id).count() == 0
        assert Expense.query.filter_by(user_id=demo_user.id).count() == 0
        assert Budget.query.filter_by(user_id=demo_user.id).count() == 0
        assert SavingsGoal.query.filter_by(user_id=demo_user.id).count() == 0
