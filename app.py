from flask import Flask, render_template, request

app = Flask(__name__)

TOOLS = [
    {
        "name": "BMI 计算器",
        "desc": "计算身体质量指数（BMI）并给出参考区间。",
        "url": "/bmi",
        "category": "体重管理",
        "keywords": ["bmi", "体重", "身高", "肥胖", "减肥"],
    },
    {
        "name": "饮水量计算器",
        "desc": "根据体重估算每日建议饮水量（ml）。",
        "url": "/water",
        "category": "生活习惯",
        "keywords": ["饮水", "喝水", "水量", "ml", "升"],
    },
    {
        "name": "睡眠周期计算器",
        "desc": "给出建议的入睡/起床时间点（按 90 分钟周期）。",
        "url": "/sleep",
        "category": "睡眠",
        "keywords": ["睡眠", "起床", "入睡", "90分钟", "周期"],
    },
    {
        "name": "基础代谢率 BMR",
        "desc": "使用 Mifflin-St Jeor 公式估算基础代谢（kcal/天）。",
        "url": "/bmr",
        "category": "热量代谢",
        "keywords": ["bmr", "基础代谢", "热量", "kcal"],
    },
    {
        "name": "每日热量需求 TDEE",
        "desc": "根据活动水平估算每日维持热量（kcal/天）。",
        "url": "/calorie",
        "category": "热量代谢",
        "keywords": ["tdee", "热量需求", "活动水平", "kcal"],
    },
]

@app.get("/")
def home():
    return render_template("index.html", tools=TOOLS)

# 1) BMI
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
                raise ValueError

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

# 2) 饮水量（简单：30~35 ml/kg）
@app.route("/water", methods=["GET", "POST"])
def water_page():
    low = high = None
    error = None

    if request.method == "POST":
        try:
            weight_kg = float(request.form["weight_kg"])
            if weight_kg <= 0:
                raise ValueError
            low = int(round(weight_kg * 30))
            high = int(round(weight_kg * 35))
        except Exception:
            error = "请输入正确的体重数字（例如：60）"

    return render_template("water.html", low=low, high=high, error=error)

# 3) 睡眠周期（90 分钟/周期 + 入睡缓冲 15 分钟）
@app.route("/sleep", methods=["GET", "POST"])
def sleep_page():
    # 输出若干个建议时间（字符串）
    results = []
    error = None

    def parse_time(s: str):
        # "HH:MM"
        hh, mm = s.split(":")
        hh = int(hh)
        mm = int(mm)
        if hh < 0 or hh > 23 or mm < 0 or mm > 59:
            raise ValueError
        return hh * 60 + mm

    def fmt(total_min: int):
        total_min %= (24 * 60)
        hh = total_min // 60
        mm = total_min % 60
        return f"{hh:02d}:{mm:02d}"

    if request.method == "POST":
        mode = request.form.get("mode")  # "wake" or "sleep"
        t = request.form.get("time_hhmm", "").strip()

        try:
            base = parse_time(t)
            cycle = 90
            buffer_fall_asleep = 15  # 入睡缓冲

            # 建议给 4~6 个选项
            if mode == "wake":
                # 已知起床时间 -> 推算入睡时间
                # 入睡时间 = 起床 - (N * 90) - 15
                for n in range(6, 3, -1):  # 6,5,4
                    sleep_time = base - n * cycle - buffer_fall_asleep
                    results.append(f"建议 {n} 个周期：{fmt(sleep_time)} 入睡")
            else:
                # 已知入睡时间 -> 推算起床时间
                # 起床时间 = 入睡 + 15 + (N * 90)
                for n in range(4, 7):  # 4,5,6
                    wake_time = base + buffer_fall_asleep + n * cycle
                    results.append(f"建议 {n} 个周期：{fmt(wake_time)} 起床")
        except Exception:
            error = "请输入正确时间（例如：23:30）"

    return render_template("sleep.html", results=results, error=error)

# 4) BMR（Mifflin-St Jeor）
@app.route("/bmr", methods=["GET", "POST"])
def bmr_page():
    bmr = None
    error = None

    if request.method == "POST":
        try:
            sex = request.form["sex"]  # "male" or "female"
            age = int(request.form["age"])
            height_cm = float(request.form["height_cm"])
            weight_kg = float(request.form["weight_kg"])
            if age <= 0 or height_cm <= 0 or weight_kg <= 0:
                raise ValueError

            # Mifflin-St Jeor
            base = 10 * weight_kg + 6.25 * height_cm - 5 * age
            if sex == "male":
                bmr = int(round(base + 5))
            else:
                bmr = int(round(base - 161))
        except Exception:
            error = "请输入正确数值（例如：男/30岁/170cm/60kg）"

    return render_template("bmr.html", bmr=bmr, error=error)

# 5) 每日热量需求 TDEE（BMR * 活动系数）
@app.route("/calorie", methods=["GET", "POST"])
def calorie_page():
    tdee = None
    bmr = None
    error = None

    activity_levels = {
        "1.2": "久坐（几乎不运动）",
        "1.375": "轻度（每周 1-3 天）",
        "1.55": "中度（每周 3-5 天）",
        "1.725": "较高（每周 6-7 天）",
        "1.9": "非常高（体力劳动/高强度训练）",
    }

    if request.method == "POST":
        try:
            sex = request.form["sex"]
            age = int(request.form["age"])
            height_cm = float(request.form["height_cm"])
            weight_kg = float(request.form["weight_kg"])
            factor = float(request.form["factor"])
            if str(factor) not in activity_levels and f"{factor}" not in activity_levels:
                # 允许 float 显示差异
                pass

            if age <= 0 or height_cm <= 0 or weight_kg <= 0:
                raise ValueError

            base = 10 * weight_kg + 6.25 * height_cm - 5 * age
            bmr = (base + 5) if sex == "male" else (base - 161)
            tdee = int(round(bmr * factor))
            bmr = int(round(bmr))
        except Exception:
            error = "请输入正确数值与活动水平"

    return render_template("calorie.html", tdee=tdee, bmr=bmr, error=error)

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
    app.run(debug=True)
