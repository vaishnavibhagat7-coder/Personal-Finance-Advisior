import os
import json
import logging
from decimal import Decimal
from datetime import date
from flask import current_app
from app.models import Income, Expense, Budget, SavingsGoal, ExpenseCategory
from app.utils import to_decimal, format_currency, get_month_bounds, get_month_name

logger = logging.getLogger(__name__)


def aggregate_user_financial_data(user, year: int, month: int):
    """
    Deterministically calculate user financial numbers in Python.
    Never trust AI for arithmetic or account balance calculation.
    """
    start_date, end_date = get_month_bounds(year, month)
    
    # Incomes for the month
    incomes = Income.query.filter(
        Income.user_id == user.id,
        Income.date >= start_date,
        Income.date <= end_date
    ).all()
    total_income = sum((to_decimal(i.amount) for i in incomes), Decimal('0.00'))
    
    # Expenses for the month
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    total_expenses = sum((to_decimal(e.amount) for e in expenses), Decimal('0.00'))
    
    # Net balance & savings rate
    net_balance = total_income - total_expenses
    if total_income > Decimal('0.00'):
        savings_rate = (net_balance / total_income) * Decimal('100.0')
    else:
        savings_rate = Decimal('0.00')

    # Category breakdown
    category_totals = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else "Uncategorized"
        category_totals[cat_name] = category_totals.get(cat_name, Decimal('0.00')) + to_decimal(exp.amount)

    category_breakdown = [
        {"category": k, "amount": v, "percentage": (v / total_expenses * Decimal('100.0')) if total_expenses > 0 else Decimal('0.0')}
        for k, v in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    # Budgets for the month
    budgets = Budget.query.filter(
        Budget.user_id == user.id,
        Budget.month == month,
        Budget.year == year
    ).all()
    
    budget_analysis = []
    total_budgeted = Decimal('0.00')
    overbudget_categories = []
    approaching_categories = []

    for b in budgets:
        limit = to_decimal(b.amount_limit)
        total_budgeted += limit
        spent = category_totals.get(b.category.name, Decimal('0.00'))
        rem = limit - spent
        pct = (spent / limit * Decimal('100.0')) if limit > 0 else Decimal('0.0')

        status = 'Normal'
        if pct > Decimal('100.0'):
            status = 'Overspending'
            overbudget_categories.append({"category": b.category.name, "spent": spent, "limit": limit, "over": spent - limit})
        elif pct >= Decimal('90.0'):
            status = 'Near Limit'
            approaching_categories.append({"category": b.category.name, "spent": spent, "limit": limit, "remaining": rem})
        elif pct >= Decimal('75.0'):
            status = 'Approaching Limit'
            approaching_categories.append({"category": b.category.name, "spent": spent, "limit": limit, "remaining": rem})

        budget_analysis.append({
            "category": b.category.name,
            "limit": limit,
            "spent": spent,
            "remaining": rem,
            "percentage": pct,
            "status": status
        })

    # Active savings goals
    goals = SavingsGoal.query.filter_by(user_id=user.id).all()
    goals_data = [{
        "name": g.name,
        "target": to_decimal(g.target_amount),
        "saved": to_decimal(g.current_amount),
        "progress_pct": g.progress_percentage,
        "status": g.status
    } for g in goals]

    # Rule-based financial health score (0 - 100)
    health_score = 60
    if total_income > Decimal('0.00'):
        if savings_rate >= Decimal('30.0'):
            health_score += 25
        elif savings_rate >= Decimal('20.0'):
            health_score += 15
        elif savings_rate >= Decimal('10.0'):
            health_score += 5
        elif savings_rate < Decimal('0.0'):
            health_score -= 30

    if overbudget_categories:
        health_score -= min(30, len(overbudget_categories) * 10)
    else:
        health_score += 10

    if goals:
        health_score += 5
    health_score = max(10, min(100, health_score))

    return {
        "user_name": user.full_name,
        "occupation": user.occupation or "Salaried Professional",
        "currency": user.currency or "₹",
        "priorities": user.financial_priorities or "General financial health and disciplined savings",
        "notes": user.financial_notes or "",
        "year": year,
        "month": month,
        "month_name": get_month_name(month),
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance,
        "savings_rate": savings_rate,
        "monthly_savings_target": to_decimal(user.monthly_savings_target),
        "category_breakdown": category_breakdown,
        "budgets": budget_analysis,
        "total_budgeted": total_budgeted,
        "overbudget_categories": overbudget_categories,
        "approaching_categories": approaching_categories,
        "goals": goals_data,
        "health_score": health_score
    }


def generate_rule_based_advice(data: dict) -> dict:
    """
    Intelligent, rule-based financial advice generator.
    Always active as a reliable baseline and offline fallback.
    """
    curr = data["currency"]
    inc = data["total_income"]
    exp = data["total_expenses"]
    bal = data["net_balance"]
    rate = data["savings_rate"]
    occ = data["occupation"]
    over = data["overbudget_categories"]
    breakdown = data["category_breakdown"]
    goals = data["goals"]

    sections = {}

    # 1. Executive Summary & Health Check
    if inc == Decimal('0.00') and exp == Decimal('0.00'):
        sections["summary"] = (
            f"No financial transactions have been recorded for {data['month_name']} {data['year']}. "
            "Add your income and daily expenses to unlock comprehensive financial intelligence and personalized guidance."
        )
    elif bal >= Decimal('0.00'):
        sections["summary"] = (
            f"Positive cashflow month for {data['month_name']} {data['year']}. You earned {format_currency(inc, curr)} "
            f"and spent {format_currency(exp, curr)}, leaving a positive surplus of {format_currency(bal, curr)} "
            f"({rate:.1f}% savings rate). Financial Health Score: {data['health_score']}/100."
        )
    else:
        sections["summary"] = (
            f"Deficit alert for {data['month_name']} {data['year']}. Your expenses of {format_currency(exp, curr)} "
            f"exceeded your income of {format_currency(inc, curr)} by {format_currency(abs(bal), curr)}. "
            f"Immediate expense reprioritization is advised. Financial Health Score: {data['health_score']}/100."
        )

    # 2. Overspending & Budget Alerts
    alerts = []
    if over:
        for item in over:
            alerts.append(
                f"**Overspending Warning**: In '{item['category']}', you spent {format_currency(item['spent'], curr)} "
                f"against your budget limit of {format_currency(item['limit'], curr)} "
                f"(Exceeded by {format_currency(item['over'], curr)})."
            )
    elif exp > inc and inc > 0:
        alerts.append("Overall monthly spending exceeds earned income. Check high-discretionary categories.")
    else:
        alerts.append("All category budgets are currently disciplined and within safe thresholds.")
    sections["alerts"] = alerts

    # 3. Spending Habits & Top Categories Analysis
    habits = []
    if breakdown:
        top_cat = breakdown[0]
        habits.append(
            f"Your largest expenditure category is **{top_cat['category']}** consuming "
            f"{format_currency(top_cat['amount'], curr)} ({top_cat['percentage']:.1f}% of total outflow)."
        )
        if len(breakdown) > 1 and breakdown[1]["percentage"] > Decimal('20.0'):
            habits.append(
                f"Second major expense is **{breakdown[1]['category']}** at "
                f"{format_currency(breakdown[1]['amount'], curr)} ({breakdown[1]['percentage']:.1f}%)."
            )
    sections["habits"] = habits

    # 4. Tailored Recommendations based on Occupation & Financial Priorities
    recs = []
    if occ == "Student":
        recs.append("As a student, prioritize tracking small recurring expenses (cafes, takeout, subscriptions). Aim to put aside at least 10%–15% into an emergency buffer.")
        recs.append("Take advantage of student discounts on transit, software, and educational subscriptions.")
    elif occ == "Freelancer":
        recs.append("Due to irregular income streams, build a 6-month buffer fund rather than the standard 3 months.")
        recs.append("Set aside 20%–25% of every invoice payment immediately into a separate tax and contingency account.")
    elif occ == "Household Manager":
        recs.append("Audit recurring monthly utility bills and grocery subscriptions. Bulk purchasing staples can yield 10%–15% monthly savings.")
        recs.append("Align household member allowances with defined category limits to avoid mid-month budget overruns.")
    else:  # Salaried Professional
        recs.append("Automate a transfer of at least 20% of your salary on payday directly to your savings and investment accounts (pay yourself first).")
        recs.append("Evaluate discretionary spends (dining out, lifestyle shopping) and restrict them to 30% of net income using the 50/30/20 guideline.")

    # Emergency Fund Guidance
    monthly_burn = exp if exp > 0 else (inc if inc > 0 else Decimal('25000.00'))
    emergency_target_3m = monthly_burn * Decimal('3.0')
    emergency_target_6m = monthly_burn * Decimal('6.0')
    recs.append(
        f"**Emergency Fund Target**: Based on current spending, your recommended 3-month survival fund is "
        f"{format_currency(emergency_target_3m, curr)}, and a 6-month full cushion is {format_currency(emergency_target_6m, curr)}."
    )
    sections["recommendations"] = recs

    # 5. Next Month Planning Steps
    steps = [
        f"Set realistic category budget limits for next month before the 1st of the month.",
        f"Review unallocated surplus ({format_currency(max(Decimal('0.00'), bal), curr)}) and assign at least 50% to your active savings goals."
    ]
    if goals:
        steps.append(f"Continue scheduled contributions toward your '{goals[0]['name']}' goal.")
    else:
        steps.append("Create a dedicated Savings Goal for an Emergency Fund in the Savings Goals module.")
    sections["next_steps"] = steps

    return sections


def query_gemini_advisor(data: dict, user_prompt: str = None) -> tuple[str, bool]:
    """
    Query the Gemini API using Google GenAI SDK.
    Returns (response_text, is_live_ai).
    Falls back gracefully to the rule-based engine if API key is not configured or fails.
    """
    api_key = current_app.config.get('GEMINI_API_KEY')
    model_name = current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    if not api_key:
        logger.info("GEMINI_API_KEY is not configured; using intelligent rule-based engine.")
        rule_advice = generate_rule_based_advice(data)
        
        # Build clean markdown response from rule engine
        text = f"### Financial Health Assessment ({data['month_name']} {data['year']})\n\n"
        text += f"**Financial Health Score**: {data['health_score']}/100\n\n"
        text += f"{rule_advice['summary']}\n\n"
        
        text += "#### Budget & Overspending Alerts\n"
        for a in rule_advice['alerts']:
            text += f"- {a}\n"
            
        text += "\n#### Spending Patterns & Analysis\n"
        for h in rule_advice['habits']:
            text += f"- {h}\n"
            
        text += "\n#### Actionable Financial Recommendations\n"
        for r in rule_advice['recommendations']:
            text += f"- {r}\n"
            
        text += "\n#### Next Month Strategy\n"
        for s in rule_advice['next_steps']:
            text += f"1. {s}\n"
            
        text += "\n\n> *Note: Running on FinWise Rule-Based Advisory Engine. To activate live Gemini AI insights, configure `GEMINI_API_KEY` in `.env`.*"
        return text, False

    # Attempt to query Google GenAI SDK
    try:
        # Prepare sanitized financial summary for AI (no passwords, no sensitive PII)
        summary_payload = {
            "user_name": data["user_name"],
            "occupation": data["occupation"],
            "currency": data["currency"],
            "month": f"{data['month_name']} {data['year']}",
            "total_income": str(data["total_income"]),
            "total_expenses": str(data["total_expenses"]),
            "net_balance": str(data["net_balance"]),
            "savings_rate_percent": f"{data['savings_rate']:.1f}%",
            "monthly_savings_target": str(data["monthly_savings_target"]),
            "top_categories": [
                {"category": c["category"], "amount": str(c["amount"]), "pct": f"{c['percentage']:.1f}%"}
                for c in data["category_breakdown"][:6]
            ],
            "budget_status": [
                {"category": b["category"], "limit": str(b["limit"]), "spent": str(b["spent"]), "status": b["status"]}
                for b in data["budgets"]
            ],
            "savings_goals": [
                {"goal": g["name"], "target": str(g["target"]), "saved": str(g["saved"]), "progress": f"{g['progress_pct']:.1f}%"}
                for g in data["goals"]
            ],
            "financial_priorities": data["priorities"],
            "health_score": data["health_score"]
        }

        system_instruction = (
            "You are FinWise AI, an expert, encouraging, and highly ethical financial advisor. "
            "You analyze personal finance metrics strictly computed and provided by the backend. "
            "Never perform or contradict the arithmetic balances provided in the context. "
            "Never provide speculative stock picks, guaranteed returns, or regulated investment advice. "
            "Provide structured, clear, empathetic, and actionable advice with markdown headings, bullet points, "
            "overspending warnings, emergency fund guidance, and next month steps tailored to the user's occupation."
        )

        user_content = (
            f"Here is the verified financial summary for {data['user_name']}:\n"
            f"```json\n{json.dumps(summary_payload, indent=2)}\n```\n\n"
        )
        if user_prompt:
            user_content += f"The user asked the following specific question:\n\"{user_prompt}\"\nAnswer their question directly based on their financial data above."
        else:
            user_content += (
                "Please provide a comprehensive monthly financial advice report including:\n"
                "1. Executive Financial Health Summary & Rating\n"
                "2. Spending Habit & Overspending Analysis\n"
                "3. Tailored Saving Opportunities & Emergency Fund Guidance\n"
                "4. 3 Concrete Action Steps for Next Month."
            )

        # First try the official modern google.genai SDK
        ai_response_text = None
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=f"{system_instruction}\n\n{user_content}"
            )
            ai_response_text = response.text
        except ImportError:
            # Fallback to google.generativeai if google-genai is not available
            import google.generativeai as gai
            gai.configure(api_key=api_key)
            model = gai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
            response = model.generate_content(user_content)
            ai_response_text = response.text

        if ai_response_text and len(ai_response_text.strip()) > 0:
            disclaimer = "\n\n---\n*Disclaimer: FinWise AI provides educational and budgeting suggestions based on your recorded transactions. It does not provide regulated investment or legal advice.*"
            return ai_response_text.strip() + disclaimer, True
        else:
            raise ValueError("Empty response received from Gemini API.")

    except Exception as e:
        logger.error(f"Error querying Gemini AI: {e}")
        # Graceful fallback to rule-based engine with transparent disclosure
        rule_advice = generate_rule_based_advice(data)
        fallback_text = (
            f"> [!WARNING]\n"
            f"> Live Gemini API service was temporarily unavailable or reported: `{type(e).__name__}`. "
            f"FinWise AI has automatically activated the offline rule-based advisory engine.\n\n"
            f"### Financial Analysis ({data['month_name']} {data['year']})\n\n"
            f"**Health Score**: {data['health_score']}/100\n\n"
            f"{rule_advice['summary']}\n\n"
            f"#### Category Spending & Budget Alerts\n"
        )
        for a in rule_advice['alerts']:
            fallback_text += f"- {a}\n"
        fallback_text += "\n#### Actionable Recommendations\n"
        for r in rule_advice['recommendations']:
            fallback_text += f"- {r}\n"
        return fallback_text, False


def answer_financial_chat(user, user_message: str, year: int, month: int) -> dict:
    """
    Interactive Q&A chat endpoint grounded in user's real transactions and budgets.
    """
    data = aggregate_user_financial_data(user, year, month)
    response_text, is_live = query_gemini_advisor(data, user_prompt=user_message)
    return {
        "reply": response_text,
        "is_live_ai": is_live,
        "month": data["month_name"],
        "year": year
    }
