from __future__ import annotations
from flask import Flask, render_template, request, Response, url_for
from math import pow, floor

app = Flask(__name__)

# -----------------------
# Helpers
# -----------------------
SITE_NAME = "健康工具站"
BASE_URL_ENV = None  # 如果你有自定义域名，后面可改成 "https://xxx.com"


def canonical_url(path: str) -> str:
    """Return canonical absolute URL if BASE_URL_ENV set, else relative."""
    if BASE_URL_ENV:
        return BASE_URL_ENV.rstrip("/") + path
    return path


def to_float(s: str) -> float | None:
    try:
        return float(str(s).strip())
    except Exception:
        return None


def to_int(s: str) -> int | None:
    try:
        return int(str(s).strip())
    except Exception:
        return None


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def round1(x: float) -> float:
    return round(x, 1)


def round0(x: float) -> int:
    return int(round(x))


def mifflin_st_jeor(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    # BMR: male = 10W + 6.25H - 5A + 5; female = 10W + 6.25H - 5A - 161
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "male" else -161)


def bmi_category_cn(bmi: float) -> str:
    # 常见中国成人参考（你BMI页面也用了这个区间）
    if bmi < 18.5:
        return "偏瘦"
    if bmi < 24.0:
        return "正常"
    if bmi < 28.0:
        return "偏胖"
    return "肥胖"


def bmi_progress(bmi: float) -> int:
    # Map BMI 15-35 to 0-100 for gauge
    p = (bmi - 15.0) / (35.0 - 15.0) * 100.0
    return int(round(clamp(p, 0, 100)))


def bodyfat_us_navy(sex: str, height_cm: float, neck_cm: float, waist_cm: float, hip_cm: float | None) -> float:
    """
    US Navy body fat estimation
    This uses log10; formula differs for male/female.
    """
    import math
    h = height_cm
    n = neck_cm
    w = waist_cm
    if sex == "male":
        # %BF = 495 / (1.0324 - 0.19077*log10(waist-neck) + 0.15456*log10(height)) - 450
        return 495 / (1.0324 - 0.19077 * math.log10(w - n) + 0.15456 * math.log10(h)) - 450
    else:
        if hip_cm is None:
            raise ValueError("female requires hip")
        hip = hip_cm
        # %BF = 495 / (1.29579 - 0.35004*log10(waist+hip-neck) + 0.22100*log10(height)) - 450
        return 495 / (1.29579 - 0.35004 * math.log10(w + hip - n) + 0.22100 * math.log10(h)) - 450


def ideal_weight_methods(height_cm: float, sex: str) -> dict:
    """
    Return multiple ideal weight estimates (kg) based on classic formulas.
    Height in cm.
    """
    h_in = height_cm / 2.54  # inches
    over_5ft = max(0.0, h_in - 60.0)

    if sex == "male":
        devine = 50.0 + 2.3 * over_5ft
        robinson = 52.0 + 1.9 * over_5ft
        miller = 56.2 + 1.41 * over_5ft
        hamwi = 48.0 + 2.7 * over_5ft
    else:
        devine = 45.5 + 2.3 * over_5ft
        robinson = 49.0 + 1.7 * over_5ft
        miller = 53.1 + 1.36 * over_5ft
        hamwi = 45.5 + 2.2 * over_5ft

    avg = (devine + robinson + miller + hamwi) / 4.0
    return {
        "Devine": devine,
        "Robinson": robinson,
        "Miller": miller,
        "Hamwi": hamwi,
        "Average": avg,
    }


def waist_risk(wc_cm: float, height_cm: float) -> tuple[float, str]:
    """Waist-to-height ratio (WHtR)"""
    whtr = wc_cm / height_cm
    # 简化分级（常见建议：<0.5较好，0.5-0.6需注意，>=0.6风险更高）
    if whtr < 0.5:
        level = "较好"
    elif whtr < 0.6:
        level = "需要注意"
    else:
        level = "风险较高"
    return whtr, level


def protein_grams(weight_kg: float, goal: str) -> tuple[float, str]:
    """
    Simple protein suggestion:
    - maintain: 1.2 g/kg
    - fat_loss: 1.6 g/kg
    - muscle_gain: 1.8 g/kg
    """
    if goal == "fat_loss":
        gpk = 1.6
        label = "减脂期"
    elif goal == "muscle_gain":
        gpk = 1.8
        label = "增肌期"
    else:
        gpk = 1.2
        label = "日常维持"
    return weight_kg * gpk, label


def steps_to_kcal(steps: int, weight_kg: float) -> float:
    """
    Rough estimate: kcal per step depends on body weight and stride.
    A common heuristic: 0.04-0.06 kcal per step for average adult.
    We'll scale by weight: base 0.05 at 60kg.
    """
    kcal_per_step = 0.05 * (weight_kg / 60.0)
    return steps * kcal_per_step


def deficit_plan(tdee: float, mode: str) -> tuple[int, str]:
    """
    Suggest daily target kcal based on simple deficit/surplus.
    """
    if mode == "loss_fast":
        delta = -500
        label = "减脂（较快）"
    elif mode == "loss_easy":
        delta = -300
        label = "减脂（温和）"
    elif mode == "gain":
        delta = 250
        label = "增重/增肌（温和）"
    else:
        delta = 0
        label = "维持体重"
    target = max(1200, int(round(tdee + delta)))
    return target, label


def weeks_to_goal(current_kg: float, target_kg: float, rate_kg_per_week: float) -> float:
    diff = abs(target_kg - current_kg)
    if rate_kg_per_week <= 0:
        return float("inf")
    return diff / rate_kg_per_week


# -----------------------
# SEO: robots + sitemap
# -----------------------
@app.get("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {canonical_url('/sitemap.xml')}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    pages = [
        "/",
        "/bmi",
        "/bmr",
        "/calorie",
        "/water",
        "/sleep",
        "/bodyfat",
        "/ideal-weight",
        "/waist",
        "/protein",
        "/steps",
        "/deficit",
        "/goal-time",
        "/about",
        "/privacy",
        "/contact",
    ]
    # Simple XML sitemap
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        loc = canonical_url(p)
        xml.append("  <url>")
        xml.append(f"    <loc>{loc}</loc>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


# -----------------------
# Pages
# -----------------------
@app.get("/")
def index():
    meta = {
        "title": f"{SITE_NAME} - 在线健康计算工具（BMI/BMR/TDEE/体脂率等）",
        "description": "免费在线健康工具站：BMI、基础代谢(BMR)、每日热量需求(TDEE)、体脂率、理想体重、腰围风险、蛋白质需求、步数热量等。结构清晰、支持快速计算与参考说明。",
        "canonical": canonical_url("/"),
    }
    tools = [
        {"name": "BMI 计算器（高级版）", "path": "/bmi", "desc": "含区间、可视化与建议"},
        {"name": "基础代谢率 BMR", "path": "/bmr", "desc": "Mifflin-St Jeor 公式估算"},
        {"name": "每日热量需求 TDEE", "path": "/calorie", "desc": "活动水平 + BMR 估算"},
        {"name": "体脂率计算（US Navy）", "path": "/bodyfat", "desc": "围度估算体脂率"},
        {"name": "理想体重计算", "path": "/ideal-weight", "desc": "多种经典公式对比"},
        {"name": "腰围风险（WHtR）", "path": "/waist", "desc": "腰围/身高比参考"},
        {"name": "蛋白质需求", "path": "/protein", "desc": "按目标建议摄入"},
        {"name": "步数转热量", "path": "/steps", "desc": "粗略估算步行消耗"},
        {"name": "热量缺口/目标热量", "path": "/deficit", "desc": "减脂/增肌日摄入建议"},
        {"name": "目标体重所需时间", "path": "/goal-time", "desc": "按周变化速度估算"},
        {"name": "每日饮水量", "path": "/water", "desc": "按体重估算建议"},
        {"name": "睡眠周期", "path": "/sleep", "desc": "90 分钟周期时间点"},
    ]
    return render_template("index.html", meta=meta, tools=tools)


@app.get("/about")
def about():
    meta = {
        "title": f"关于 - {SITE_NAME}",
        "description": "关于健康工具站：提供常见健康指标的在线计算与参考说明，帮助你更好理解数据。",
        "canonical": canonical_url("/about"),
    }
    return render_template("about.html", meta=meta)


@app.get("/privacy")
def privacy():
    meta = {
        "title": f"隐私政策 - {SITE_NAME}",
        "description": "隐私政策：本网站不要求账号，不出售个人信息；输入数据仅用于当次计算展示（服务器日志除外）。",
        "canonical": canonical_url("/privacy"),
    }
    return render_template("privacy.html", meta=meta)


@app.get("/contact")
def contact():
    meta = {
        "title": f"联系 - {SITE_NAME}",
        "description": "联系页面：反馈建议、Bug 报告与合作咨询。",
        "canonical": canonical_url("/contact"),
    }
    return render_template("contact.html", meta=meta)


# -----------------------
# Tool: BMI (Advanced)
# -----------------------
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    error = None
    bmi_val = None
    category = None
    progress = None
    ideal_min = ideal_max = None
    to_min = to_max = None
    suggestion_title = "行动建议（仅供参考）"
    suggestions = []
    risk_note = "提示：本工具仅用于一般参考，不构成医疗建议。"

    height_cm_in = ""
    weight_kg_in = ""

    if request.method == "POST":
        height_cm_in = request.form.get("height_cm", "")
        weight_kg_in = request.form.get("weight_kg", "")
        h = to_float(height_cm_in)
        w = to_float(weight_kg_in)

        if not h or not w or h <= 0 or w <= 0:
            error = "请输入正确的身高与体重。"
        else:
            hm = h / 100.0
            bmi_raw = w / (hm * hm)
            bmi_val = round1(bmi_raw)
            category = bmi_category_cn(bmi_raw)
            progress = bmi_progress(bmi_raw)

            # Ideal range by BMI 18.5–23.9
            ideal_min = round1(18.5 * hm * hm)
            ideal_max = round1(23.9 * hm * hm)

            if bmi_raw < 18.5:
                to_min = round1(ideal_min - w)
            elif bmi_raw > 23.9:
                to_max = round1(w - ideal_max)

            # Suggestions
            if bmi_raw < 18.5:
                suggestions = [
                    "优先保证规律三餐与足够蛋白质摄入。",
                    "每周进行 2–3 次力量训练，提升肌肉量与体能。",
                    "关注睡眠质量与压力水平，避免长期熬夜。",
                ]
            elif bmi_raw < 24.0:
                suggestions = [
                    "保持当前体重趋势，重点关注腰围与体脂率。",
                    "每周累计 150 分钟中等强度运动更容易长期维持。",
                    "饮食上优先选择高纤维、足够蛋白质与稳定作息。",
                ]
            elif bmi_raw < 28.0:
                suggestions = [
                    "先算 TDEE，尝试每天减少约 300–500 kcal 的热量缺口。",
                    "增加步行与力量训练，帮助维持代谢与肌肉量。",
                    "记录 2–4 周趋势再调整，不必被单日波动影响。",
                ]
            else:
                suggestions = [
                    "从温和热量缺口与规律运动开始，优先提升可坚持性。",
                    "建议结合腰围/体脂率与体检指标进行综合评估。",
                    "如有慢病或不适，优先咨询专业人士获取个性化建议。",
                ]

    meta = {
        "title": "BMI 计算器（高级版）- 健康工具站",
        "description": "在线 BMI 计算器：支持身高体重输入，输出 BMI 数值、成人参考范围、健康体重区间与行动建议，并推荐 BMR/TDEE 等相关工具。",
        "canonical": canonical_url("/bmi"),
    }

    return render_template(
        "bmi.html",
        meta=meta,
        error=error,
        bmi=bmi_val,
        category=category,
        progress=progress,
        ideal_min=ideal_min,
        ideal_max=ideal_max,
        to_min=to_min,
        to_max=to_max,
        suggestion_title=suggestion_title,
        suggestions=suggestions,
        risk_note=risk_note,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
    )


# -----------------------
# Tool: BMR
# -----------------------
@app.route("/bmr", methods=["GET", "POST"])
def bmr():
    error = None
    bmr_val = None

    sex_in = "male"
    age_in = ""
    height_cm_in = ""
    weight_kg_in = ""

    if request.method == "POST":
        sex_in = request.form.get("sex", "male")
        age_in = request.form.get("age", "")
        height_cm_in = request.form.get("height_cm", "")
        weight_kg_in = request.form.get("weight_kg", "")

        age = to_int(age_in)
        h = to_float(height_cm_in)
        w = to_float(weight_kg_in)

        if sex_in not in ("male", "female"):
            error = "性别选择不正确。"
        elif age is None or age <= 0 or age > 120:
            error = "请输入正确年龄。"
        elif not h or h <= 0 or h > 250:
            error = "请输入正确身高（cm）。"
        elif not w or w <= 0 or w > 300:
            error = "请输入正确体重（kg）。"
        else:
            bmr_val = round0(mifflin_st_jeor(sex_in, age, h, w))

    meta = {
        "title": "基础代谢率 BMR - 健康工具站",
        "description": "在线 BMR 计算器：使用 Mifflin-St Jeor 公式估算基础代谢率（kcal/天），并提供用途说明与下一步工具推荐（TDEE、BMI 等）。",
        "canonical": canonical_url("/bmr"),
    }
    return render_template(
        "bmr.html",
        meta=meta,
        error=error,
        bmr=bmr_val,
        sex_in=sex_in,
        age_in=age_in,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
    )


# -----------------------
# Tool: TDEE (calorie)
# -----------------------
@app.route("/calorie", methods=["GET", "POST"])
def calorie():
    error = None
    tdee_val = None

    sex_in = "male"
    age_in = ""
    height_cm_in = ""
    weight_kg_in = ""
    activity_in = "1.2"

    if request.method == "POST":
        sex_in = request.form.get("sex", "male")
        age_in = request.form.get("age", "")
        height_cm_in = request.form.get("height_cm", "")
        weight_kg_in = request.form.get("weight_kg", "")
        activity_in = request.form.get("activity", "1.2")

        age = to_int(age_in)
        h = to_float(height_cm_in)
        w = to_float(weight_kg_in)
        act = to_float(activity_in)

        if sex_in not in ("male", "female"):
            error = "性别选择不正确。"
        elif age is None or age <= 0 or age > 120:
            error = "请输入正确年龄。"
        elif not h or h <= 0 or h > 250:
            error = "请输入正确身高（cm）。"
        elif not w or w <= 0 or w > 300:
            error = "请输入正确体重（kg）。"
        elif not act or act < 1.1 or act > 2.5:
            error = "活动水平不正确。"
        else:
            b = mifflin_st_jeor(sex_in, age, h, w)
            tdee_val = round0(b * act)

    meta = {
        "title": "每日热量需求 TDEE - 健康工具站",
        "description": "在线 TDEE 计算器：基于 BMR 与活动水平估算每日总能量消耗，并提供减脂/维持/增肌使用建议与相关工具链接。",
        "canonical": canonical_url("/calorie"),
    }
    return render_template(
        "calorie.html",
        meta=meta,
        error=error,
        tdee=tdee_val,
        sex_in=sex_in,
        age_in=age_in,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
        activity_in=str(activity_in),
    )


# -----------------------
# Tool: Water
# -----------------------
@app.route("/water", methods=["GET", "POST"])
def water():
    error = None
    water_ml = None
    water_l = None
    weight_kg_in = ""

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "")
        w = to_float(weight_kg_in)
        if not w or w <= 0 or w > 300:
            error = "请输入正确体重（kg）。"
        else:
            # 30–35 ml/kg: use 33 as middle
            water_ml = round0(w * 33.0)
            water_l = round1(water_ml / 1000.0)

    meta = {
        "title": "每日饮水量计算 - 健康工具站",
        "description": "按体重估算每日饮水量建议（ml/L），并提供影响因素与实践建议。免费在线工具。",
        "canonical": canonical_url("/water"),
    }
    return render_template(
        "water.html",
        meta=meta,
        error=error,
        water_ml=water_ml,
        water_l=water_l,
        weight_kg_in=weight_kg_in,
    )


# -----------------------
# Tool: Sleep cycle
# -----------------------
@app.route("/sleep", methods=["GET", "POST"])
def sleep():
    error = None
    mode_in = "sleep_now"
    time_hm_in = ""
    times = []

    def parse_hm(s: str):
        s = s.strip()
        if ":" not in s:
            return None
        hh, mm = s.split(":", 1)
        h = to_int(hh)
        m = to_int(mm)
        if h is None or m is None:
            return None
        if h < 0 or h > 23 or m < 0 or m > 59:
            return None
        return h, m

    def fmt(h: int, m: int) -> str:
        return f"{h:02d}:{m:02d}"

    def add_minutes(h: int, m: int, minutes: int) -> tuple[int, int]:
        total = h * 60 + m + minutes
        total %= (24 * 60)
        return total // 60, total % 60

    if request.method == "POST":
        mode_in = request.form.get("mode", "sleep_now")
        time_hm_in = request.form.get("time_hm", "")
        hm = parse_hm(time_hm_in)
        if hm is None:
            error = "请输入正确时间（例如 23:30）。"
        else:
            h, m = hm
            # include 15 min fall-asleep buffer
            buffer_min = 15
            cycle = 90
            options = [3, 4, 5, 6]  # cycles
            times = []
            if mode_in == "sleep_now":
                # input is bedtime time
                start_h, start_m = add_minutes(h, m, buffer_min)
                for c in options:
                    th, tm = add_minutes(start_h, start_m, c * cycle)
                    times.append(fmt(th, tm))
            else:
                # input is wake time -> compute bed times
                for c in options:
                    th, tm = add_minutes(h, m, -(c * cycle) - buffer_min)
                    times.append(fmt(th, tm))

    meta = {
        "title": "睡眠周期计算 - 健康工具站",
        "description": "睡眠周期计算器：按 90 分钟周期给出推荐入睡/起床时间点，适合做作息规划（仅供参考）。",
        "canonical": canonical_url("/sleep"),
    }
    return render_template("sleep.html", meta=meta, error=error, mode_in=mode_in, time_hm_in=time_hm_in, times=times)


# -----------------------
# Tool: Body fat (US Navy)
# -----------------------
@app.route("/bodyfat", methods=["GET", "POST"])
def bodyfat():
    error = None
    bf = None
    sex_in = "male"
    height_cm_in = ""
    neck_cm_in = ""
    waist_cm_in = ""
    hip_cm_in = ""

    if request.method == "POST":
        sex_in = request.form.get("sex", "male")
        height_cm_in = request.form.get("height_cm", "")
        neck_cm_in = request.form.get("neck_cm", "")
        waist_cm_in = request.form.get("waist_cm", "")
        hip_cm_in = request.form.get("hip_cm", "")

        h = to_float(height_cm_in)
        n = to_float(neck_cm_in)
        w = to_float(waist_cm_in)
        hip = to_float(hip_cm_in) if hip_cm_in.strip() else None

        try:
            if sex_in not in ("male", "female"):
                raise ValueError("性别选择不正确。")
            if not h or h <= 0:
                raise ValueError("请输入正确身高。")
            if not n or n <= 0:
                raise ValueError("请输入正确颈围。")
            if not w or w <= 0:
                raise ValueError("请输入正确腰围。")
            if sex_in == "female" and (hip is None or hip <= 0):
                raise ValueError("女性请输入正确臀围。")
            if w - n <= 0:
                raise ValueError("腰围需大于颈围（用于公式计算）。")

            bf_val = bodyfat_us_navy(sex_in, h, n, w, hip)
            bf = round1(clamp(bf_val, 2.0, 60.0))
        except Exception as e:
            error = str(e)

    meta = {
        "title": "体脂率计算（US Navy）- 健康工具站",
        "description": "体脂率计算器：使用 US Navy 围度公式估算体脂率（%），输入身高、颈围、腰围（女性含臀围），并提供解读与下一步建议。",
        "canonical": canonical_url("/bodyfat"),
    }
    return render_template(
        "bodyfat.html",
        meta=meta,
        error=error,
        bf=bf,
        sex_in=sex_in,
        height_cm_in=height_cm_in,
        neck_cm_in=neck_cm_in,
        waist_cm_in=waist_cm_in,
        hip_cm_in=hip_cm_in,
    )


# -----------------------
# Tool: Ideal weight
# -----------------------
@app.route("/ideal-weight", methods=["GET", "POST"])
def ideal_weight():
    error = None
    sex_in = "male"
    height_cm_in = ""
    results = None

    if request.method == "POST":
        sex_in = request.form.get("sex", "male")
        height_cm_in = request.form.get("height_cm", "")
        h = to_float(height_cm_in)
        if sex_in not in ("male", "female"):
            error = "性别选择不正确。"
        elif not h or h <= 0 or h > 250:
            error = "请输入正确身高（cm）。"
        else:
            res = ideal_weight_methods(h, sex_in)
            results = {k: round1(v) for k, v in res.items()}

    meta = {
        "title": "理想体重计算 - 健康工具站",
        "description": "理想体重计算器：根据身高与性别，用 Devine/Robinson/Miller/Hamwi 等公式给出多个估算结果并对比参考。",
        "canonical": canonical_url("/ideal-weight"),
    }
    return render_template(
        "ideal_weight.html",
        meta=meta,
        error=error,
        sex_in=sex_in,
        height_cm_in=height_cm_in,
        results=results,
    )


# -----------------------
# Tool: Waist risk (WHtR)
# -----------------------
@app.route("/waist", methods=["GET", "POST"])
def waist():
    error = None
    wc_in = ""
    height_cm_in = ""
    whtr = None
    level = None

    if request.method == "POST":
        wc_in = request.form.get("waist_cm", "")
        height_cm_in = request.form.get("height_cm", "")
        wc = to_float(wc_in)
        h = to_float(height_cm_in)
        if not wc or wc <= 0:
            error = "请输入正确腰围（cm）。"
        elif not h or h <= 0:
            error = "请输入正确身高（cm）。"
        else:
            whtr, level = waist_risk(wc, h)
            whtr = round1(whtr)

    meta = {
        "title": "腰围风险（WHtR）- 健康工具站",
        "description": "腰围风险评估：通过腰围/身高比（WHtR）给出简单风险提示，并提供建议与相关工具推荐。",
        "canonical": canonical_url("/waist"),
    }
    return render_template(
        "waist.html",
        meta=meta,
        error=error,
        waist_cm_in=wc_in,
        height_cm_in=height_cm_in,
        whtr=whtr,
        level=level,
    )


# -----------------------
# Tool: Protein
# -----------------------
@app.route("/protein", methods=["GET", "POST"])
def protein():
    error = None
    weight_kg_in = ""
    goal_in = "maintain"
    grams = None
    label = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "")
        goal_in = request.form.get("goal", "maintain")
        w = to_float(weight_kg_in)
        if not w or w <= 0 or w > 300:
            error = "请输入正确体重（kg）。"
        elif goal_in not in ("maintain", "fat_loss", "muscle_gain"):
            error = "目标选择不正确。"
        else:
            g, label = protein_grams(w, goal_in)
            grams = round0(g)

    meta = {
        "title": "蛋白质需求计算 - 健康工具站",
        "description": "蛋白质需求计算器：按体重与目标（维持/减脂/增肌）给出每日蛋白质摄入建议（g/天），并提供实践建议。",
        "canonical": canonical_url("/protein"),
    }
    return render_template(
        "protein.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        goal_in=goal_in,
        grams=grams,
        label=label,
    )


# -----------------------
# Tool: Steps -> kcal
# -----------------------
@app.route("/steps", methods=["GET", "POST"])
def steps():
    error = None
    steps_in = ""
    weight_kg_in = ""
    kcal = None

    if request.method == "POST":
        steps_in = request.form.get("steps", "")
        weight_kg_in = request.form.get("weight_kg", "")
        s = to_int(steps_in)
        w = to_float(weight_kg_in)
        if s is None or s <= 0 or s > 200000:
            error = "请输入正确步数。"
        elif not w or w <= 0 or w > 300:
            error = "请输入正确体重（kg）。"
        else:
            kcal = round0(steps_to_kcal(s, w))

    meta = {
        "title": "步数转热量消耗 - 健康工具站",
        "description": "步数转热量计算器：按步数与体重粗略估算步行消耗（kcal），并给出使用建议与相关工具链接。",
        "canonical": canonical_url("/steps"),
    }
    return render_template(
        "steps.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        weight_kg_in=weight_kg_in,
        kcal=kcal,
    )


# -----------------------
# Tool: Deficit target kcal
# -----------------------
@app.route("/deficit", methods=["GET", "POST"])
def deficit():
    error = None
    tdee_in = ""
    mode_in = "loss_easy"
    target_kcal = None
    label = None

    if request.method == "POST":
        tdee_in = request.form.get("tdee", "")
        mode_in = request.form.get("mode", "loss_easy")
        tdee_val = to_float(tdee_in)
        if not tdee_val or tdee_val <= 0 or tdee_val > 10000:
            error = "请输入正确的 TDEE（kcal/天）。"
        elif mode_in not in ("loss_easy", "loss_fast", "maintain", "gain"):
            error = "模式选择不正确。"
        else:
            target_kcal, label = deficit_plan(tdee_val, mode_in)

    meta = {
        "title": "热量缺口与目标热量 - 健康工具站",
        "description": "根据 TDEE 估算减脂/维持/增肌的目标日摄入热量（kcal/天），并提供下一步建议（蛋白质、步数、体重趋势）。",
        "canonical": canonical_url("/deficit"),
    }
    return render_template(
        "deficit.html",
        meta=meta,
        error=error,
        tdee_in=tdee_in,
        mode_in=mode_in,
        target_kcal=target_kcal,
        label=label,
    )


# -----------------------
# Tool: Goal weight time
# -----------------------
@app.route("/goal-time", methods=["GET", "POST"])
def goal_time():
    error = None
    current_in = ""
    target_in = ""
    rate_in = "0.5"
    weeks = None

    if request.method == "POST":
        current_in = request.form.get("current_kg", "")
        target_in = request.form.get("target_kg", "")
        rate_in = request.form.get("rate", "0.5")

        c = to_float(current_in)
        t = to_float(target_in)
        r = to_float(rate_in)

        if not c or c <= 0 or c > 300:
            error = "请输入正确当前体重（kg）。"
        elif not t or t <= 0 or t > 300:
            error = "请输入正确目标体重（kg）。"
        elif not r or r <= 0 or r > 2.0:
            error = "请输入合理的每周变化速度（建议 0.25–1.0 kg/周）。"
        else:
            wks = weeks_to_goal(c, t, r)
            weeks = round1(wks)

    meta = {
        "title": "目标体重所需时间 - 健康工具站",
        "description": "目标体重时间估算：输入当前体重、目标体重与每周变化速度，估算达到目标所需周数，并给出建议与相关工具链接。",
        "canonical": canonical_url("/goal-time"),
    }
    return render_template(
        "goal_time.html",
        meta=meta,
        error=error,
        current_in=current_in,
        target_in=target_in,
        rate_in=rate_in,
        weeks=weeks,
    )

@app.get("/healthz")
def healthz():
    return "OK", 200

if __name__ == "__main__":
    print("Starting Flask...")
    app.run(host="0.0.0.0", port=5000, debug=True)
