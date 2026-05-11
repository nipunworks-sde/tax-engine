from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "taxengine2024"

# Demo users
USERS = {
    "nipun@gmail.com": {"password": "123456", "name": "Nipun"},
    "demo@gmail.com":  {"password": "123456", "name": "Demo User"},
}

# ── New Regime Tax Calculation ──────────────────────────────────

def calculate_new_regime(income):
    tax = 0
    slabs = [
        (300000, 0.00),
        (300000, 0.05),
        (300000, 0.10),
        (300000, 0.15),
        (300000, 0.20),
        (float('inf'), 0.30),
    ]
    remaining = max(0, income - 300000)
    for limit, rate in slabs[1:]:
        if remaining <= 0:
            break
        taxable = min(remaining, limit)
        tax += taxable * rate
        remaining -= taxable

    if income <= 700000:
        tax = 0

    tax += tax * 0.04  # 4% cess
    return round(tax)

# ── Old Regime Tax Calculation ──────────────────────────────────

def calculate_old_regime(income, deductions):
    standard_deduction = 50000
    sec_80c = min(deductions.get("sec80c", 0), 150000)
    sec_80d = min(deductions.get("sec80d", 0), 25000)
    hra     = deductions.get("hra", 0)

    taxable = max(0, income - standard_deduction - sec_80c - sec_80d - hra)

    slabs = [
        (250000, 0.00),
        (250000, 0.05),
        (500000, 0.20),
        (float('inf'), 0.30),
    ]

    tax = 0
    remaining = taxable
    for limit, rate in slabs:
        if remaining <= 0:
            break
        taxable_in_slab = min(remaining, limit)
        tax += taxable_in_slab * rate
        remaining -= taxable_in_slab

    if taxable <= 500000:
        tax = 0

    tax += tax * 0.04  # 4% cess
    return round(tax)

# ── Slab Breakdown ──────────────────────────────────────────────

def get_slab_breakdown(income, regime):
    breakdown = []
    if regime == "new":
        slabs = [
            (300000, 0.00, "Up to ₹3L"),
            (300000, 0.05, "₹3L - ₹6L"),
            (300000, 0.10, "₹6L - ₹9L"),
            (300000, 0.15, "₹9L - ₹12L"),
            (300000, 0.20, "₹12L - ₹15L"),
            (float('inf'), 0.30, "Above ₹15L"),
        ]
        remaining = max(0, income - 300000)
        for limit, rate, label in slabs[1:]:
            if remaining <= 0:
                break
            taxable = min(remaining, limit)
            tax = round(taxable * rate)
            if taxable > 0:
                breakdown.append({
                    "slab": label,
                    "rate": f"{int(rate*100)}%",
                    "amount": taxable,
                    "tax": tax
                })
            remaining -= taxable
    return breakdown

# ── Tax Saving Tips ─────────────────────────────────────────────

def get_tax_saving_tips(income, new_tax, old_tax, deductions):
    tips = []
    sec_80c = deductions.get("sec80c", 0)
    sec_80d = deductions.get("sec80d", 0)

    if sec_80c < 150000:
        remaining = 150000 - sec_80c
        tips.append(f"Invest ₹{remaining:,} more in 80C (PPF, ELSS, LIC) to save up to ₹{round(remaining*0.3):,} in tax")

    if sec_80d < 25000:
        remaining = 25000 - sec_80d
        tips.append(f"Pay ₹{remaining:,} more in health insurance under 80D to save ₹{round(remaining*0.2):,}")

    if new_tax < old_tax:
        tips.append(f"New Regime saves you ₹{old_tax - new_tax:,} — consider switching!")
    else:
        tips.append(f"Old Regime saves you ₹{new_tax - old_tax:,} — maximize your deductions!")

    if income > 1000000:
        tips.append("Invest in NPS (80CCD) for extra ₹50,000 deduction beyond 80C limit")

    if income > 1500000:
        tips.append("Consider tax-free bonds or ELSS mutual funds for additional savings")

    return tips

# ── Income Range Data ───────────────────────────────────────────

def get_income_range_data(base_income):
    ranges = []
    incomes = [
        base_income * 0.5,
        base_income * 0.75,
        base_income,
        base_income * 1.25,
        base_income * 1.5,
    ]
    for inc in incomes:
        new_t = calculate_new_regime(inc)
        old_t = calculate_old_regime(inc, {})
        ranges.append({
            "income": round(inc),
            "new_tax": new_t,
            "old_tax": old_t,
        })
    return ranges

# ── Routes ──────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("calculator"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")
        user     = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = {"email": email, "name": user["name"]}
            return redirect(url_for("calculator"))
        error = "Invalid email or password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/calculator")
def calculator():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("calculator.html", user=session["user"])

@app.route("/calculate", methods=["POST"])
def calculate():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data   = request.json
    income = float(data.get("income", 0))
    deductions = {
        "sec80c": float(data.get("sec80c", 0)),
        "sec80d": float(data.get("sec80d", 0)),
        "hra":    float(data.get("hra", 0)),
    }

    new_tax = calculate_new_regime(income)
    old_tax = calculate_old_regime(income, deductions)
    tips    = get_tax_saving_tips(income, new_tax, old_tax, deductions)
    breakdown = get_slab_breakdown(income, "new")
    range_data = get_income_range_data(income)

    better_regime = "New Regime" if new_tax <= old_tax else "Old Regime"
    savings       = abs(new_tax - old_tax)

    return jsonify({
        "new_tax":       new_tax,
        "old_tax":       old_tax,
        "better_regime": better_regime,
        "savings":       savings,
        "tips":          tips,
        "income":        income,
        "take_home_new": round(income - new_tax),
        "take_home_old": round(income - old_tax),
        "breakdown":     breakdown,
        "range_data":    range_data,
    })

if __name__ == "__main__":
    app.run(debug=True)