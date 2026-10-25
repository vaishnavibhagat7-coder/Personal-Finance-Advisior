import os
from datetime import date, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import User, Income, Expense, Budget, SavingsGoal, SavingsContribution, ExpenseCategory, AIInsight
from app.utils import seed_default_categories, to_decimal, shift_months


def reset_demo_data(app=None):
    """Safely reset and remove the demo user and all associated records without touching other users."""
    if app is None:
        app = create_app()

    with app.app_context():
        demo_email = "demo@finwise.ai"
        demo_user = User.query.filter_by(email=demo_email).first()
        if demo_user:
            Income.query.filter_by(user_id=demo_user.id).delete()
            Expense.query.filter_by(user_id=demo_user.id).delete()
            Budget.query.filter_by(user_id=demo_user.id).delete()
            SavingsGoal.query.filter_by(user_id=demo_user.id).delete()
            SavingsContribution.query.filter_by(user_id=demo_user.id).delete()
            AIInsight.query.filter_by(user_id=demo_user.id).delete()
            db.session.delete(demo_user)
            db.session.commit()
            print("Demo account records cleared.")
        else:
            print("No demo user found.")


def seed_demo_data(app=None):
    if app is None:
        app = create_app()

    with app.app_context():
        # Ensure default categories exist
        seed_default_categories(db.session, ExpenseCategory)

        # 1. Clean or create demo user
        reset_demo_data(app)

        demo_user = User(
            email=demo_email,
            full_name="Aarav Sharma",
            occupation="Salaried Professional",
            currency="₹",
            monthly_income_target=Decimal("85000.00"),
            monthly_savings_target=Decimal("20000.00"),
            financial_priorities="Build 6-month emergency fund, purchase a high-performance laptop, and curtail food delivery expenses.",
            financial_notes="Working in tech, hybrid schedule. Looking to optimize monthly investments while maintaining a disciplined lifestyle budget."
        )
        demo_user.set_password("Demo@12345")
        db.session.add(demo_user)
        db.session.commit()

        # Fetch category map
        categories = {c.name: c.id for c in ExpenseCategory.query.filter_by(is_default=True).all()}

        today = date.today()

        # 2. Seed 6 Months of Realistic Historical Data
        for i in range(5, -1, -1):
            m_date = shift_months(today, -i)
            year = m_date.year
            month = m_date.month

            # Income: Primary Salary
            salary_date = date(year, month, 1)
            db.session.add(Income(
                user_id=demo_user.id,
                source="Salary",
                amount=Decimal("82500.00"),
                date=salary_date,
                description="Monthly Tech Salary (Direct Deposit)"
            ))

            # Additional occasional freelance or investment return
            if i in (1, 3, 5):
                db.session.add(Income(
                    user_id=demo_user.id,
                    source="Freelance",
                    amount=Decimal("15000.00"),
                    date=date(year, month, 14),
                    description="Full-stack UI consulting project"
                ))

            # Expenses across categories
            # Rent & Housing
            if "Rent and Housing" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Rent and Housing"],
                    amount=Decimal("24000.00"),
                    date=date(year, month, 3),
                    payment_method="Net Banking",
                    merchant="Apartment Society Rent",
                    notes="Monthly residential flat lease"
                ))

            # Groceries
            if "Groceries" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Groceries"],
                    amount=Decimal("4500.00"),
                    date=date(year, month, 6),
                    payment_method="UPI",
                    merchant="Blinkit / Zepto",
                    notes="Weekly organic groceries and pantry staples"
                ))
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Groceries"],
                    amount=Decimal("4200.00"),
                    date=date(year, month, 20),
                    payment_method="Credit Card",
                    merchant="Nature's Basket",
                    notes="Mid-month supermarket restocking"
                ))

            # Utilities
            if "Utilities" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Utilities"],
                    amount=Decimal("2800.00"),
                    date=date(year, month, 8),
                    payment_method="UPI",
                    merchant="State Electricity Board & Fiber Net",
                    notes="Broadband wifi and electricity bill"
                ))

            # Food & Dining
            if "Food & Dining" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Food & Dining"],
                    amount=Decimal("3400.00"),
                    date=date(year, month, 10),
                    payment_method="UPI",
                    merchant="Swiggy / Zomato",
                    notes="Weekend dining orders"
                ))
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Food & Dining"],
                    amount=Decimal("2850.00"),
                    date=date(year, month, 22),
                    payment_method="Credit Card",
                    merchant="Social Cafe Bistro",
                    notes="Team lunch and coffee meet"
                ))

            # Transportation
            if "Transportation" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Transportation"],
                    amount=Decimal("3800.00"),
                    date=date(year, month, 12),
                    payment_method="UPI",
                    merchant="Uber / Fuel Station",
                    notes="Office commute rides and petrol"
                ))

            # Subscriptions
            if "Subscriptions" in categories:
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Subscriptions"],
                    amount=Decimal("1199.00"),
                    date=date(year, month, 15),
                    payment_method="Credit Card",
                    merchant="Netflix & Spotify Premium",
                    notes="Streaming services auto-debit"
                ))

            # Shopping / Personal Care
            if "Shopping" in categories:
                shopping_amt = Decimal("6200.00") if i == 0 else Decimal("3500.00")
                db.session.add(Expense(
                    user_id=demo_user.id,
                    category_id=categories["Shopping"],
                    amount=shopping_amt,
                    date=date(year, month, 18),
                    payment_method="Credit Card",
                    merchant="Amazon India",
                    notes="Workstation accessories and apparel"
                ))

            # 3. Monthly Budgets for the current month and previous month
            if i <= 1:
                budget_specs = [
                    ("Rent and Housing", Decimal("25000.00")),
                    ("Groceries", Decimal("10000.00")),
                    ("Food & Dining", Decimal("6000.00")),
                    ("Transportation", Decimal("5000.00")),
                    ("Utilities", Decimal("3500.00")),
                    ("Shopping", Decimal("5000.00")),
                    ("Subscriptions", Decimal("1500.00"))
                ]
                for cat_title, limit_val in budget_specs:
                    if cat_title in categories:
                        db.session.add(Budget(
                            user_id=demo_user.id,
                            category_id=categories[cat_title],
                            month=month,
                            year=year,
                            amount_limit=limit_val
                        ))

        # 4. Savings Goals & Contributions
        g1 = SavingsGoal(
            user_id=demo_user.id,
            name="6-Month Emergency Fund",
            target_amount=Decimal("250000.00"),
            current_amount=Decimal("150000.00"),
            target_date=shift_months(today, 8),
            description="High-yield liquid fund to sustain 6 months of living expenses.",
            status="In Progress"
        )
        db.session.add(g1)

        g2 = SavingsGoal(
            user_id=demo_user.id,
            name="MacBook Pro M3 Max",
            target_amount=Decimal("180000.00"),
            current_amount=Decimal("120000.00"),
            target_date=shift_months(today, 4),
            description="Next-gen development workstation for local LLM inference and engineering projects.",
            status="In Progress"
        )
        db.session.add(g2)

        g3 = SavingsGoal(
            user_id=demo_user.id,
            name="Himachal Trekking Expedition",
            target_amount=Decimal("35000.00"),
            current_amount=Decimal("35000.00"),
            target_date=shift_months(today, 1),
            description="Annual mountain adventure vacation with college friends.",
            status="Completed"
        )
        db.session.add(g3)
        db.session.commit()

        # Add contribution records for goals
        db.session.add(SavingsContribution(
            goal_id=g1.id,
            user_id=demo_user.id,
            amount=Decimal("25000.00"),
            date=shift_months(today, -1),
            note="Transferred bonus payout directly to liquid fund"
        ))
        db.session.add(SavingsContribution(
            goal_id=g2.id,
            user_id=demo_user.id,
            amount=Decimal("20000.00"),
            date=today - timedelta(days=12),
            note="Monthly tech fund allocation"
        ))

        db.session.commit()
        print("Demo data seeded successfully for demo@finwise.ai (Password: Demo@12345)")


if __name__ == '__main__':
    seed_demo_data()
