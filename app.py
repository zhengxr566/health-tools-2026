from __future__ import annotations

from datetime import datetime, timedelta
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)

# -----------------------
# Brand / SEO / Domain
# -----------------------
SITE_NAME = "CalmyHealth"
SITE_NAME_ZH = "CalmyHealth 健康工具"
BASE_URL_ENV = "https://calmyhealth.com"

OLD_HOSTS = {
    "health-tools-2026.onrender.com",
    "www.health-tools-2026.onrender.com",
}


@app.before_request
def redirect_old_domain():
    host = request.host.split(":")[0].lower()
    if host in OLD_HOSTS:
        qs = f"?{request.query_string.decode()}" if request.query_string else ""
        return redirect(f"{BASE_URL_ENV}{request.path}{qs}", code=301)


@app.route("/google984348f5d29aa2c5.html")
def google_verify():
    return send_from_directory(".", "google984348f5d29aa2c5.html")


def canonical_url(path: str) -> str:
    return BASE_URL_ENV.rstrip("/") + path


# -----------------------
# Information Architecture
# -----------------------
CATEGORY_META = {
    "weight": {
        "name": "体重与体型",
        "description": "BMI、体脂、理想体重、围度相关工具",
        "children": {
            "bmi_weight": {
                "name": "BMI与体重",
                "description": "BMI、理想体重、目标体重",
            },
            "body_shape": {
                "name": "体脂与围度",
                "description": "体脂率、腰围、腰臀比等",
            },
        },
    },
    "metabolism": {
        "name": "代谢与热量",
        "description": "BMR、TDEE、热量目标",
        "children": {
            "base_energy": {
                "name": "基础代谢",
                "description": "BMR、静息消耗",
            },
            "calorie_plan": {
                "name": "热量规划",
                "description": "TDEE、热量缺口、目标时间",
            },
        },
    },
    "nutrition": {
        "name": "营养摄入",
        "description": "蛋白质、饮水、宏量营养",
        "children": {
            "daily_intake": {
                "name": "日常摄入",
                "description": "蛋白质、饮水量",
            },
        },
    },
    "activity": {
        "name": "运动与习惯",
        "description": "步数、睡眠、活动习惯",
        "children": {
            "exercise": {
                "name": "运动消耗",
                "description": "步数与能量消耗",
            },
            "sleep_habit": {
                "name": "作息与睡眠",
                "description": "睡眠周期与习惯",
            },
        },
    },
    "pregnancy": {
        "name": "孕期工具",
        "description": "预产期与孕周相关",
        "children": {
            "pregnancy_basic": {
                "name": "基础孕期",
                "description": "预产期、孕周",
            },
        },
    },
}

TOOLS = [
    {
        "endpoint": "bmi",
        "name": "BMI 计算器（高级版）",
        "path": "/bmi",
        "desc": "含区间、可视化与建议",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": True,
    },
    {
        "endpoint": "ideal_weight",
        "name": "理想体重计算",
        "path": "/ideal-weight",
        "desc": "多种经典公式对比",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": False,
    },
    {
        "endpoint": "goal_time",
        "name": "目标体重所需时间",
        "path": "/goal-time",
        "desc": "按周变化速度估算",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": False,
    },
    {
        "endpoint": "bodyfat",
        "name": "体脂率计算（US Navy）",
        "path": "/bodyfat",
        "desc": "围度估算体脂率",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": True,
    },
    {
        "endpoint": "waist",
        "name": "腰围风险（WHtR）",
        "path": "/waist",
        "desc": "腰围/身高比参考",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": False,
    },
    {
        "endpoint": "bmr",
        "name": "基础代谢率 BMR",
        "path": "/bmr",
        "desc": "Mifflin-St Jeor 公式估算",
        "category": "metabolism",
        "subgroup": "base_energy",
        "featured": True,
    },
    {
        "endpoint": "calorie",
        "name": "每日热量需求 TDEE",
        "path": "/calorie",
        "desc": "活动水平 + BMR 估算",
        "category": "metabolism",
        "subgroup": "calorie_plan",
        "featured": True,
    },
    {
        "endpoint": "deficit",
        "name": "热量缺口/目标热量",
        "path": "/deficit",
        "desc": "减脂/增肌日摄入建议",
        "category": "metabolism",
        "subgroup": "calorie_plan",
        "featured": False,
    },
    {
        "endpoint": "protein",
        "name": "蛋白质需求",
        "path": "/protein",
        "desc": "按目标建议摄入",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    {
        "endpoint": "water",
        "name": "每日饮水量",
        "path": "/water",
        "desc": "按体重估算建议",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    {
        "endpoint": "steps",
        "name": "步数转热量",
        "path": "/steps",
        "desc": "粗略估算步行消耗",
        "category": "activity",
        "subgroup": "exercise",
        "featured": False,
    },
    {
        "endpoint": "sleep",
        "name": "睡眠周期",
        "path": "/sleep",
        "desc": "90 分钟周期时间点",
        "category": "activity",
        "subgroup": "sleep_habit",
        "featured": False,
    },
    {
        "endpoint": "pregnancy_due_date",
        "name": "预产期计算器",
        "path": "/pregnancy-due-date",
        "desc": "末次月经推算预产期与孕周",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": True,
    },
]

from flask import request

def grouped_tools(current_path=None):
    """
    Return 3-level navigation data for sidebar / tools pages.

    Structure:
    [
        {
            "slug": "weight",
            "name": "体重与体型",
            "description": "...",
            "count": 5,
            "is_open": True,
            "children": [
                {
                    "slug": "bmi_weight",
                    "name": "BMI与体重",
                    "description": "...",
                    "count": 3,
                    "is_open": True,
                    "tools": [
                        {
                            "endpoint": "bmi",
                            "name": "BMI 计算器",
                            "path": "/bmi",
                            "desc": "...",
                            "category": "weight",
                            "subgroup": "bmi_weight",
                            "featured": True,
                            "is_active": True,
                        }
                    ],
                }
            ],
        }
    ]
    """

    if current_path is None:
        try:
            current_path = request.path
        except RuntimeError:
            current_path = ""

    groups = []

    for cat_slug, cat_meta in CATEGORY_META.items():
        children = []

        for child_slug, child_meta in cat_meta.get("children", {}).items():
            # 取出当前分类 + 子分类下的工具
            child_tools = [
                t.copy()
                for t in TOOLS
                if t.get("category") == cat_slug and t.get("subgroup") == child_slug
            ]

            # 给每个工具标记当前是否激活
            for tool in child_tools:
                tool["is_active"] = (tool.get("path") == current_path)

            # 热门工具排前面，再按名称排序
            child_tools = sorted(
                child_tools,
                key=lambda x: (
                    not x.get("featured", False),  # featured=True 排前
                    x.get("name", "")
                )
            )

            # 如果这个子分类没有工具，可以选择跳过
            if not child_tools:
                continue

            child_is_open = any(tool["is_active"] for tool in child_tools)

            children.append({
                "slug": child_slug,
                "name": child_meta.get("name", child_slug),
                "description": child_meta.get("description", ""),
                "count": len(child_tools),
                "is_open": child_is_open,
                "tools": child_tools,
            })

        # 分类总数
        total_count = sum(child["count"] for child in children)

        # 分类是否展开：
        # 1. 当前路径是这个分类页 /category/<slug>
        # 2. 或者它下面有子分类已展开
        cat_is_open = (
            current_path == f"/category/{cat_slug}"
            or any(child["is_open"] for child in children)
        )

        groups.append({
            "slug": cat_slug,
            "name": cat_meta.get("name", cat_slug),
            "description": cat_meta.get("description", ""),
            "count": total_count,
            "is_open": cat_is_open,
            "children": children,
        })

    return groups


@app.context_processor
def inject_global_nav():
    return {
        "nav_categories": grouped_tools(),
        "top_tools": top_tools(10),
        "site_name": SITE_NAME,
        "site_name_zh": SITE_NAME_ZH,
    }

def meta_for(title: str, description: str, path: str) -> dict:
    return {
        "title": title,
        "description": description,
        "canonical": canonical_url(path),
    }


# -----------------------
# Helpers
# -----------------------
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
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "male" else -161)


def bmi_category_cn(bmi: float) -> str:
    if bmi < 18.5:
        return "偏瘦"
    if bmi < 24.0:
        return "正常"
    if bmi < 28.0:
        return "偏胖"
    return "肥胖"


def bmi_progress(bmi: float) -> int:
    p = (bmi - 15.0) / (35.0 - 15.0) * 100.0
    return int(round(clamp(p, 0, 100)))


def bodyfat_us_navy(
    sex: str,
    height_cm: float,
    neck_cm: float,
    waist_cm: float,
    hip_cm: float | None,
) -> float:
    import math

    h = height_cm
    n = neck_cm
    w = waist_cm
    if sex == "male":
        return 495 / (
            1.0324 - 0.19077 * math.log10(w - n) + 0.15456 * math.log10(h)
        ) - 450
    else:
        if hip_cm is None:
            raise ValueError("female requires hip")
        hip = hip_cm
        return 495 / (
            1.29579
            - 0.35004 * math.log10(w + hip - n)
            + 0.22100 * math.log10(h)
        ) - 450


def ideal_weight_methods(height_cm: float, sex: str) -> dict:
    h_in = height_cm / 2.54
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
    whtr = wc_cm / height_cm
    if whtr < 0.5:
        level = "较好"
    elif whtr < 0.6:
        level = "需要注意"
    else:
        level = "风险较高"
    return whtr, level


def protein_grams(weight_kg: float, goal: str) -> tuple[float, str]:
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
    kcal_per_step = 0.05 * (weight_kg / 60.0)
    return steps * kcal_per_step


def deficit_plan(tdee: float, mode: str) -> tuple[int, str]:
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
    core_paths = ["/", "/tools", "/about", "/privacy", "/contact"]
    category_paths = [f"/category/{slug}" for slug in CATEGORY_META.keys()]
    tool_paths = [t["path"] for t in TOOLS]
    all_paths = core_paths + category_paths + tool_paths

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for path in all_paths:
        xml.append("  <url>")
        xml.append(f"    <loc>{canonical_url(path)}</loc>")
        xml.append("  </url>")

    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


# -----------------------
# Pages
# -----------------------
@app.get("/")
def index():
    featured_tools = top_tools(10)
    meta = meta_for(
        f"{SITE_NAME} - 健康计算工具导航",
        "BMI、TDEE、BMR、体脂率、理想体重、蛋白质、睡眠、预产期等在线健康工具。",
        "/",
    )
    return render_template(
        "index.html",
        meta=meta,
        categories=grouped_tools(),
        featured_tools=featured_tools,
        tools=TOOLS,
        page_kind="home",
    )

@app.get("/tools")
def tools():
    meta = meta_for(
        f"工具导航 - {SITE_NAME}",
        "按分类浏览 CalmyHealth 的健康工具：体重与体型、代谢与热量、营养摄入、运动与习惯、孕期工具。",
        "/tools",
    )
    return render_template(
        "tools.html",
        meta=meta,
        categories=grouped_tools(),
        tools=TOOLS,
        top_tools=top_tools(10),
        page_kind="tools",
    )

def top_tools(limit=10):
    ranked = sorted(
        TOOLS,
        key=lambda x: (
            not x.get("featured", False),
            x.get("name", "")
        )
    )
    return ranked[:limit]

@app.get("/category/<slug>")
def category_page(slug: str):
    nav_groups = grouped_tools()
    current_cat = next((c for c in nav_groups if c["slug"] == slug), None)

    if current_cat is None:
        return redirect(url_for("tools"))

    meta = meta_for(
        f"{current_cat['name']}工具 - {SITE_NAME}",
        f"浏览 {current_cat['name']} 相关健康工具：{current_cat['description']}",
        f"/category/{slug}",
    )

    return render_template(
        "category.html",
        meta=meta,
        current_cat=current_cat,
        categories=nav_groups,
        page_kind="category",
    )


@app.get("/about")
def about():
    meta = meta_for(
        f"关于 - {SITE_NAME}",
        "关于 CalmyHealth：围绕健康数据理解与工具化场景，持续扩展可读、可用、可导航的健康工具页面。",
        "/about",
    )
    return render_template("about.html", meta=meta)


@app.get("/privacy")
def privacy():
    meta = meta_for(
        f"隐私政策 - {SITE_NAME}",
        "隐私政策：CalmyHealth 不要求账号，不出售个人信息；输入数据仅用于当次计算展示（服务器日志除外）。",
        "/privacy",
    )
    return render_template("privacy.html", meta=meta)


@app.get("/contact")
def contact():
    meta = meta_for(
        f"联系 - {SITE_NAME}",
        "联系页面：反馈建议、Bug 报告与合作咨询。",
        "/contact",
    )
    return render_template("contact.html", meta=meta)


# -----------------------
# Tool: pregnancy
# -----------------------
@app.route("/pregnancy-due-date", methods=["GET", "POST"])
def pregnancy_due_date():
    due_date = None
    error = None

    if request.method == "POST":
        try:
            lmp = request.form.get("lmp")
            lmp_date = datetime.strptime(lmp, "%Y-%m-%d")
            due_date = (lmp_date + timedelta(days=280)).strftime("%Y-%m-%d")
        except Exception:
            error = "请输入有效的日期"

    meta = meta_for(
        "预产期计算器（怀孕到生产时间推算）- CalmyHealth",
        "输入末次月经日期，推算预产期与孕周（仅供参考）。包含预产期怎么算、怀孕多久生、常见问题与相关工具链接。",
        "/pregnancy-due-date",
    )
    return render_template(
        "pregnancy_due_date.html",
        meta=meta,
        due_date=due_date,
        error=error,
    )


# -----------------------
# Tool: BMI
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

            ideal_min = round1(18.5 * hm * hm)
            ideal_max = round1(23.9 * hm * hm)

            if bmi_raw < 18.5:
                to_min = round1(ideal_min - w)
            elif bmi_raw > 23.9:
                to_max = round1(w - ideal_max)

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

    meta = meta_for(
        "BMI 计算器（高级版）- CalmyHealth",
        "在线 BMI 计算器：支持身高体重输入，输出 BMI 数值、成人参考范围、健康体重区间与行动建议，并推荐 BMR/TDEE 等相关工具。",
        "/bmi",
    )

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

    meta = meta_for(
        "基础代谢率 BMR - CalmyHealth",
        "在线 BMR 计算器：使用 Mifflin-St Jeor 公式估算基础代谢率（kcal/天），并提供用途说明与下一步工具推荐（TDEE、BMI 等）。",
        "/bmr",
    )
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
# Tool: TDEE
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

    meta = meta_for(
        "每日热量需求 TDEE - CalmyHealth",
        "在线 TDEE 计算器：基于 BMR 与活动水平估算每日总能量消耗，并提供减脂/维持/增肌使用建议与相关工具链接。",
        "/calorie",
    )
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
            water_ml = round0(w * 33.0)
            water_l = round1(water_ml / 1000.0)

    meta = meta_for(
        "每日饮水量计算 - CalmyHealth",
        "按体重估算每日饮水量建议（ml/L），并提供影响因素与实践建议。免费在线工具。",
        "/water",
    )
    return render_template(
        "water.html",
        meta=meta,
        error=error,
        water_ml=water_ml,
        water_l=water_l,
        weight_kg_in=weight_kg_in,
    )


# -----------------------
# Tool: Sleep
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
        total %= 24 * 60
        return total // 60, total % 60

    if request.method == "POST":
        mode_in = request.form.get("mode", "sleep_now")
        time_hm_in = request.form.get("time_hm", "")
        hm = parse_hm(time_hm_in)

        if hm is None:
            error = "请输入正确时间（例如 23:30）。"
        else:
            h, m = hm
            buffer_min = 15
            cycle = 90
            options = [3, 4, 5, 6]

            if mode_in == "sleep_now":
                start_h, start_m = add_minutes(h, m, buffer_min)
                for c in options:
                    th, tm = add_minutes(start_h, start_m, c * cycle)
                    times.append(fmt(th, tm))
            else:
                for c in options:
                    th, tm = add_minutes(h, m, -(c * cycle) - buffer_min)
                    times.append(fmt(th, tm))

    meta = meta_for(
        "睡眠周期计算 - CalmyHealth",
        "睡眠周期计算器：按 90 分钟周期给出推荐入睡/起床时间点，适合做作息规划（仅供参考）。",
        "/sleep",
    )
    return render_template(
        "sleep.html",
        meta=meta,
        error=error,
        mode_in=mode_in,
        time_hm_in=time_hm_in,
        times=times,
    )


# -----------------------
# Tool: Body Fat
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

    meta = meta_for(
        "体脂率计算（US Navy）- CalmyHealth",
        "体脂率计算器：使用 US Navy 围度公式估算体脂率（%），输入身高、颈围、腰围（女性含臀围），并提供解读与下一步建议。",
        "/bodyfat",
    )
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
# Tool: Ideal Weight
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

    meta = meta_for(
        "理想体重计算 - CalmyHealth",
        "理想体重计算器：根据身高与性别，用 Devine/Robinson/Miller/Hamwi 等公式给出多个估算结果并对比参考。",
        "/ideal-weight",
    )
    return render_template(
        "ideal_weight.html",
        meta=meta,
        error=error,
        sex_in=sex_in,
        height_cm_in=height_cm_in,
        results=results,
    )


# -----------------------
# Tool: Waist Risk
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

    meta = meta_for(
        "腰围风险（WHtR）- CalmyHealth",
        "腰围风险评估：通过腰围/身高比（WHtR）给出简单风险提示，并提供建议与相关工具推荐。",
        "/waist",
    )
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

    meta = meta_for(
        "蛋白质需求计算 - CalmyHealth",
        "蛋白质需求计算器：按体重与目标（维持/减脂/增肌）给出每日蛋白质摄入建议（g/天），并提供实践建议。",
        "/protein",
    )
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
# Tool: Steps
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

    meta = meta_for(
        "步数转热量消耗 - CalmyHealth",
        "步数转热量计算器：按步数与体重粗略估算步行消耗（kcal），并给出使用建议与相关工具链接。",
        "/steps",
    )
    return render_template(
        "steps.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        weight_kg_in=weight_kg_in,
        kcal=kcal,
    )


# -----------------------
# Tool: Deficit
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

    meta = meta_for(
        "热量缺口与目标热量 - CalmyHealth",
        "根据 TDEE 估算减脂/维持/增肌的目标日摄入热量（kcal/天），并提供下一步建议（蛋白质、步数、体重趋势）。",
        "/deficit",
    )
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
# Tool: Goal Time
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
            weeks = round1(weeks_to_goal(c, t, r))

    meta = meta_for(
        "目标体重所需时间 - CalmyHealth",
        "目标体重时间估算：输入当前体重、目标体重与每周变化速度，估算达到目标所需周数，并给出建议与相关工具链接。",
        "/goal-time",
    )
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