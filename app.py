import json
import os
from collections import defaultdict

USER_DATA_FILE = 'user_data.json'

# Load persistent data
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'r') as f:
        user_data = defaultdict(dict, json.load(f))
else:
    user_data = defaultdict(dict)

# Save function
def save_user_data():
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=4)

from flask import Flask, render_template, request, redirect, url_for, session
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'kook-secret'  # Required for session management

# In-memory storage: user -> company -> evaluations
user_data = defaultdict(dict)

# ---------------- Welcome / Home / Logout ----------------
@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            session['username'] = username
            return redirect(url_for('home'))
    return render_template('welcome.html')

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('welcome'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

# ---------------- Growth Route ----------------
@app.route('/growth', methods=['GET', 'POST'])
def growth():
    metrics = get_growth_metrics()
    if request.method == 'POST':
        username = session.get('username', 'Guest')
        company = request.form.get("company", "Unnamed Company")
        total_growth_score = 0
        metric_scores = []

        for i, (metric_name, _) in enumerate(metrics):
            try:
                score = int(request.form.get(f'score_{i}', 0))
                if 1 <= score <= 5:
                    metric_scores.append({"metric": metric_name, "score": score})
                    total_growth_score += score
                else:
                    metric_scores.append({"metric": metric_name, "score": 0})
            except ValueError:
                metric_scores.append({"metric": metric_name, "score": 0})

        if total_growth_score >= 60:
            result = "Strong Growth Potential, high upside."
        elif 45 <= total_growth_score < 60:
            result = "Solid Growth Potential, worth watching."
        else:
            result = "Riskier or unproven growth."

        user_data[username].setdefault(company, {})['growth'] = {
            "total_score": total_growth_score,
            "metric_scores": metric_scores,
            "result": result
        }
        save_user_data()  # persist

        return render_template(
            'growth_result.html',
            company=company,
            total_score=total_growth_score,
            metric_scores=metric_scores,
            result=result
        )

    return render_template('growth_form.html', metrics=enumerate(metrics))

def get_growth_metrics():
    return [
        ("Revenue Growth (YoY)", ">15% annually"),
        ("EPS Growth (YoY)", ">20% annually"),
        ("Total Addressable Market (TAM)", "Expanding multi-billion"),
        ("Gross Margin", ">50%"),
        ("Operating Margin", ">15% or increasing"),
        ("Free Cash Flow (FCF)", "Positive & growing"),
        ("Return on Equity (ROE)", ">15%"),
        ("Return on Invested Capital (ROIC)", ">10%"),
        ("PEG Ratio", "< 1.5"),
        ("Insider Ownership", ">5% or increasing"),
        ("Institutional Ownership", ">60% or growing"),
        ("Customer/User Growth", "Accelerating"),
        ("Customer Retention / NRR", ">100% NRR or low churn"),
        ("Competitive Advantage (Moat)", "Clear & defensible"),
        ("Debt Levels", "Low or decreasing")
    ]

# ---------------- Company Evaluation ----------------
@app.route('/company', methods=['GET', 'POST'])
def company():
    if request.method == 'POST':
        username = session.get('username', 'Guest')
        data = request.form
        company = data['company']

        try:
            pe_ratio = float(data['pe_ratio'])
            current_assets = float(data['current_assets'])
            current_liabilities = float(data['current_liabilities'])
            total_assets = float(data['total_assets'])
            total_liabilities = float(data['total_liabilities'])
            operating_income = float(data['operating_income'])
            total_revenue = float(data['total_revenue'])
            free_cash_flow = float(data['free_cash_flow'])
            shares_outstanding = float(data['shares_outstanding'])
        except (ValueError, KeyError):
            return "Please enter valid numeric values for all inputs."

        evaluations = []

        # P/E Ratio
        if pe_ratio > 20:
            evaluations.append({"metric": "P/E Ratio", "detail": "Overvalued, consider waiting for a better entry."})
        elif 10 < pe_ratio <= 20:
            evaluations.append({"metric": "P/E Ratio", "detail": f"{company} is fairly or undervalued, that's a good sign!"})
        else:
            evaluations.append({"metric": "P/E Ratio", "detail": "Low P/E. Could be a value play or risky—check other metrics."})

        # Current Ratio
        current_ratio = current_assets / current_liabilities if current_liabilities else 0
        evaluations.append({
            "metric": "Current Ratio",
            "detail": "Healthy short-term financial position." if current_ratio >= 1 else "Short-term assets are insufficient to cover liabilities. Risky!"
        })

        # Long-Term Ratio
        long_term_ratio = total_assets / total_liabilities if total_liabilities else 0
        evaluations.append({
            "metric": "Long-Term Ratio",
            "detail": "Strong long-term financial stability." if long_term_ratio >= 1 else "Insufficient long-term assets to cover liabilities. Risky!"
        })

        # Operating Margin
        operating_margin = operating_income / total_revenue if total_revenue else 0
        op_margin_percent = operating_margin * 100
        if operating_margin < 0.05:
            detail = f"Low profit margin ({op_margin_percent:.2f}%). Red flag."
        elif operating_margin < 0.10:
            detail = f"Healthy profit margin ({op_margin_percent:.2f}%)."
        else:
            detail = f"High profit margin ({op_margin_percent:.2f}%). Ensure sustainability."
        evaluations.append({"metric": "Operating Margin", "detail": detail})

        # Free Cash Flow per Share
        fcf_per_share = free_cash_flow / shares_outstanding if shares_outstanding else 0
        if fcf_per_share < 4:
            detail = "Weak FCF. May not provide good returns."
        elif fcf_per_share <= 7:
            detail = "Moderate FCF. Reasonably strong investment candidate."
        else:
            detail = "Excellent FCF. Promising if debt is low."
        evaluations.append({"metric": "Free Cash Flow per Share", "detail": detail})

        # Verdict
        strong_count = sum(1 for e in evaluations if any(w in e['detail'].lower() for w in ["healthy", "excellent", "strong", "fairly"]))
        if strong_count >= 4:
            verdict = f"{company} shows strong financial health and may be a good investment."
        elif strong_count == 3:
            verdict = f"{company} appears solid but warrants further research."
        else:
            verdict = f"{company} may carry higher risk. Proceed with caution."

        user_data[username].setdefault(company, {})['company'] = {
            "evaluations": evaluations,
            "verdict": verdict
        }
        save_user_data()

        return render_template('company_result.html', company=company, evaluations=evaluations, verdict=verdict)

    return render_template('company.html')

# ---------------- Risk Assessment & Investment Strategy ----------------
risk_questions = [
    {"text": "1. You have an offer to invest 15% of your net worth in a deal with an 80% chance of profit. You'd say:",
     "options": {"A": "Not worth it.", "B": "7x return", "C": "3x return", "D": "1x return"}},
    {"text": "2. Comfortable assuming $10,000 debt for $20,000 gain?",
     "options": {"A": "Totally uncomfortable. I would never do it.", "B": "Somewhat uncomfortable. I would probably never do it", "C": "Somewhat uncomfortable. But, I might do it.", "D": "Very comfortable. I would definitely do it."}},
    {"text": "3. You have a lottery ticket with 25% chance of $100,000. You would sell it for no less than:",
     "options": {"A": "$15,000", "B": "$20,000", "C": "$35,000", "D": "$60,000"}},
    {"text": "4. How often do you bet over $150 on gambling activities:",
     "options": {"A": "Never", "B": "Few times", "C": "Once this year", "D": "Two or more times"}},
    {"text": "5. If a stock you bought doubled you would:",
     "options": {"A": "Sell all", "B": "Sell half", "C": "Hold", "D": "Buy more"}},
    {"text": "6. Your CD is maturing and rates are down. You would most likely put that money in which of the following?:",
     "options": {"A": "Savings bond", "B": "Short-term bond", "C": "Long-term bond", "D": "Stock fund"}},
    {"text": "7. When deciding where to invest a large sum of money you:",
     "options": {"A": "Delay", "B": "Let others decide", "C": "Ask advisor", "D": "Decide myself"}},
    {"text": "8. How do you make investment decisions:",
     "options": {"A": "Never alone", "B": "Sometimes alone", "C": "Often alone", "D": "Always alone"}},
    {"text": "9. How is your current luck in investing:",
     "options": {"A": "Terrible", "B": "Average", "C": "Better than avg", "D": "Fantastic"}},
    {"text": "10. Why are your investments successful:",
     "options": {"A": "Fate is on my side", "B": "I was in the right place at the right time", "C": "When opportunities come, I take advantage of them", "D": "I carefully planned them to work out that way."}},
]

risk_score_map = {"A": 1, "B": 2, "C": 3, "D": 4}

def interpret_risk_score(score):
    if score <= 19:
        return "You are a conservative investor, you prefer low risk and steady returns. You still may need to take calculated risks to meet financial goals."
    elif 20 <= score <= 29:
        return "You are a moderate investor, you like to balance risk and reward. You are likely open to reasonable risks without major discomfort."
    else:
        return "You are an aggressive investor, you seek high returns, and accept volatility. You're comfortable taking significant risks for the potential of high returns."

# Investment Strategy Advisor
def investment_strategy_advisor(score):
    advisor_info = {"title": "", "goals": [], "portfolio": {}, "tips": []}

    if score <= 19:
        advisor_info["title"] = "Conservative Investor"
        advisor_info["goals"] = ["Preserve Capital", "Earn modest, stable returns", "Minimize volatility"]
        advisor_info["portfolio"] = {
            "Short-Term Bond Funds": "Low volatility, low interest rate sensitivity",
            "Intermediate-Term Bonds": "Balanced yield and safety",
            "Municipal Bond Funds": "Tax-efficient income (high tax brackets)",
            "Dividend Equity Funds": "Conservative exposure to stocks with income focus",
            "Balanced / Allocation Funds": "40/60 or 30/70 stock-to-bond ratio for stability",
            "Money Market Funds": "Near-cash equivalents, very low risk",
            "Target-Date Funds (Near Term)": "Automatically reduce risk as target date approaches",
            "Real Estate (REITs) (limited)": "Income + diversification, modest allocation"
        }
        advisor_info["tips"] = [
            "Avoid high-yield (junk) bonds and small-cap equity funds",
            "Keep equity exposure under 40% of total portfolio"
        ]
    elif 20 <= score <= 29:
        advisor_info["title"] = "Moderate Investor"
        advisor_info["goals"] = ["Grow wealth over time", "Accept moderate risk for better returns", "Maintain diversification"]
        advisor_info["portfolio"] = {
            "Blend (Core) Equity Funds": "Balanced growth and value exposure",
            "Mid-Cap and Large-Cap Funds": "Growth potential with more stability",
            "Dividend / Income Funds": "Earn income while still being in the stock market",
            "Target-Date Funds (Mid-Term)": "Risk-reducing over time",
            "60/40 or 70/30 Allocation Funds": "Good mix of stocks and bonds",
            "International Equity Funds": "Diversification outside U.S.",
            "REITs or Infrastructure Funds": "Inflation hedge, some income",
            "High-Quality Corporate Bonds": "Steady income with moderate risk"
        }
        advisor_info["tips"] = [
            "Avoid putting too much in sector-specific or emerging market funds",
            "Rebalance annually to maintain target allocation"
        ]
    else:
        advisor_info["title"] = "Aggressive Investor"
        advisor_info["goals"] = ["Maximize capital appreciation", "Tolerate short-term losses for long-term gains", "Seek alpha and thematic growth"]
        advisor_info["portfolio"] = {
            "Small-Cap and Micro-Cap Funds": "High growth potential, albeit volatile",
            "Growth Equity Funds": "Invest in companies with strong earnings growth",
            "Emerging Market Funds": "High-risk, high-return international exposure",
            "Technology / Innovation ETFs": "Targeted growth in AI, cloud, biotech, etc.",
            "Thematic / ESG / Blockchain ETFs": "Trend-driven and speculative growth",
            "Actively Managed Funds": "Try to outperform the market via expert management",
            "International Equity Funds": "Broaden high-growth potential",
            "High-Yield Bonds (Junk)": "For aggressive fixed income exposure",
            "Private Equity or Alt ETFs": "Non-traditional assets for high returns"
        }
        advisor_info["tips"] = [
            "Maintain a small percentage (10–20%) in bonds or stable funds for downside protection",
            "Watch sector and single-country overexposure",
            "Even aggressive investors should limit high-risk assets to a portion of portfolio"
        ]

    return advisor_info

@app.route('/risk', methods=['GET', 'POST'])
def risk():
    username = session.get('username', 'Guest')
    if request.method == 'POST':
        score = 0
        for i in range(len(risk_questions)):
            answer = request.form.get(f'q{i}')
            score += risk_score_map.get(answer, 0)

        message = interpret_risk_score(score)
        advisor = investment_strategy_advisor(score)

        # Save to persistent memory
        user_data[username]['risk'] = {
            "score": score,
            "message": message,
            "advisor": advisor
        }
        save_user_data()

        return render_template('risk_result.html', score=score, message=message, advisor=advisor)

    return render_template('risk.html', questions=risk_questions, enumerate=enumerate)

# ---------------- Memory ----------------
@app.route('/memory')
def memory():
    username = session.get('username', 'Guest')
    companies = list(user_data[username].keys())
    return render_template('memory.html', companies=companies)

@app.route('/memory/<company>')
def memory_detail(company):
    username = session.get('username', 'Guest')
    data = user_data[username].get(company)
    return render_template('memory_detail.html', company=company, data=data)

# ---------------- Delete Company ----------------
@app.route('/memory/<company>/delete', methods=['POST'])
def delete_company(company):
    username = session.get('username', 'Guest')
    if username in user_data and company in user_data[username]:
        del user_data[username][company]
        save_user_data()
    return redirect(url_for('memory'))

# ---------------- Run App ----------------
if __name__ == '__main__':
    app.run(debug=True)