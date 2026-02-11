from flask import Flask, render_template, request

app = Flask(__name__)

TOOLS = [
    {"name": "BMI 计算器", "desc": "计算身体质量指数（BMI）并给出参考区间。", "url": "/bmi"},
    # 未来继续加：
    # {"name": "饮水量计算器", "desc": "根据体重估算每日饮水建议。", "url": "/water"},
    # {"name": "睡眠周期计算器", "desc": "给出建议的入睡/起床时间点。", "url": "/sleep"},
]

@app.get("/")
def home():
    return render_template("index.html", tools=TOOLS)

@app.route("/bmi", methods=["GET", "POST"])
def bmi_page():
    bmi = None
    category = None
    error = None

    if request.method == "POST":
        try:
            height_cm = float(request.form["height_cm"])
            weight_kg = float(request.form["weight_kg"])
            if height_cm <= 0 or weight_kg <= 0:
                raise ValueError("invalid")

            h = height_cm / 100.0
            bmi = round(weight_kg / (h * h), 2)

            if bmi < 18.5:
                category = "偏瘦"
            elif bmi < 24.0:
                category = "正常"
            elif bmi < 28.0:
                category = "偏胖"
            else:
                category = "肥胖"
        except Exception:
            error = "请输入正确的身高/体重数字（例如：170 和 60）"

    return render_template("bmi.html", bmi=bmi, category=category, error=error)

@app.get("/about")
def about():
    return render_template("about.html")

@app.get("/privacy")
def privacy():
    return render_template("privacy.html")

@app.get("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    print("Starting Flask...")
    app.run(host="127.0.0.1", port=5000, debug=True)
