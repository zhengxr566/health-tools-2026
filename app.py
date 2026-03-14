from __future__ import annotations
from datetime import datetime, timedelta, date
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
    # 1. 体重与体型
    # ========= 1.1. BMI与体重 ======= 
    ## 1.1.1 BMI 1.1.2. 理想体重 1.1.3 目标体重时间
    # ========= 1.2. 体脂与围度 =======  
    ## 1.2.1 体脂率 1.2.2. 腰围风险 1.2.3. 腰臀比
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
    # 2. 代谢与热量
    # ========= 2.1. 基础代谢 ======= 
    ## 2.1.1 基础代谢率BMR
    # ========= 2.2. 热量规划 ======= 
    ## 2.2.1 每日热量需求 2.2.2 热量缺口 
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

    # 3. 营养摄入
    # ========= 3.1. 日常摄入 ======= 
    ## 3.1.1. 饮水 3.1.2. 蛋白质  3.1.3. 碳水 3.1.4. 脂肪摄入 3.1.5. 膳食纤维
    ## 3.1.6. 盐摄入
    # ========= 3.2. 宏量营养 ======= 
    ## 3.2.1. 宏量营养 3.2.2. 餐次分配
    # 3.3 饮食分配
    ## 3.3.1. 餐次分配
    "nutrition": {
        "name": "营养摄入", 
        "description": "饮水、蛋白质、宏量营养与饮食分配工具",
        "children": {
            "daily_intake": {
                "name": "日常摄入", 
                "description": "饮水、蛋白质、碳水、脂肪、纤维",
            },
            "macro_nutrition": {
                "name": "宏量营养",
                "description": "蛋白质、碳水、脂肪的整体分配",
            },
            "meal_planning": {
                "name": "饮食分配",
                "description": "三餐、餐次与目标导向分配",
            },
        },
    },
    # 4. 运动与习惯
    # ========= 4.1. 运动消耗 ======= 
    ## 4.1.1 步数转热量 4.1.2 步数转距离 4.1.3 步数转步行时间
    ## 4.1.4 每日步数目标 4.1.5 活动量等级 4.1.6 跑步消耗计算器
    # ========= 4.2. 睡眠时间 ======= 
    ## 4.2.1 睡眠周期 4.2.2 睡眠需求 4.2.3 睡眠时长 4.2.4 补觉时间 4.2.5 午睡时间
    # ========= 4.3. 睡眠质量 ======= 
    ## 4.3.1 睡眠债 4.3.2 睡眠效率 4.3.3 咖啡因截止时间 4.3.4 时差恢复
    ## 4.3.5 作息类型

    "activity": {
        "name": "运动与习惯",
        "description": "步数、睡眠、活动习惯",
        "children": {
            "exercise": {
                "name": "运动消耗",
                "description": "步数与能量消耗",
            },
            "sleep_time": {
                "name": "睡眠时间",
                "description": "入睡、起床、时长与午睡",
            },
            "sleep_quality": {
                "name": "睡眠质量",
                "description": "睡眠债、补觉、效率与作息",
            },
        },
    },
    # 5. 孕期工具
    # ========= 5.1. 基础孕期 ======= 
    ## 5.1.1 预产期计算 5.1.2 怀孕周数 5.1.3 预测排卵日 5.1.4 受孕日期
    # ========= 5.2. 孕期健康 ======= 
    ## 5.2.1 孕期体重增长 5.2.2 孕期热量需求 5.2.3 孕期蛋白质
    ## 5.2.4 胎儿发育周数 5.2.5 孕期饮水量

    "pregnancy": {
        "name": "孕期工具",
        "description": "排卵、受孕、孕周、预产期与孕期健康管理",
        "children": {
            "pregnancy_basic": {
                "name": "基础孕期",
                "description": "排卵期、受孕日期、孕周与预产期",
            },
            "pregnancy_health": {
                "name": "孕期健康",
                "description": "孕期体重、营养、热量与健康管理",
            },
        },
    },
}

TOOLS = [
    # =============== 
    # 1. 体重与体型 
    # ================
    # ========= 1.1. BMI与体重 ======= 
    # 1.1.1 BMI
    {
        "endpoint": "bmi",
        "name": "BMI 计算器",
        "path": "/bmi",
        "desc": "含区间、可视化与建议",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": True,
    },
    # 1.1.2. 理想体重
    {
        "endpoint": "ideal_weight",
        "name": "理想体重计算",
        "path": "/ideal-weight",
        "desc": "多种经典公式对比",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": False,
    },
    # 1.1.3 目标体重
    {
        "endpoint": "goal_time",
        "name": "目标体重所需时间",
        "path": "/goal-time",
        "desc": "按周变化速度估算",
        "category": "weight",
        "subgroup": "bmi_weight",
        "featured": False,
    },
    # ========= 1.2. 体脂与围度 ==============
    # 1.2.1 体脂率
    {
        "endpoint": "bodyfat",
        "name": "体脂率计算（US Navy）",
        "path": "/bodyfat",
        "desc": "围度估算体脂率",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": True,
    },
    # 1.2.2. 腰围风险
    {
        "endpoint": "waist",
        "name": "腰围风险（WHtR）",
        "path": "/waist",
        "desc": "腰围/身高比参考",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": False,
    },
    # 1.2.3. 腰臀比
    {
        "endpoint": "whr",
        "name": "腰臀比计算器（WHR）",
        "path": "/whr",
        "desc": "腰围与臀围比例参考",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": True,
    },
    # =============== 
    # 2. 代谢与热量 
    # ================
    # ========= 2.1. 基础代谢 ======= 
    # 2.1.1 基础代谢率
    {
        "endpoint": "bmr",
        "name": "基础代谢率 BMR",
        "path": "/bmr",
        "desc": "Mifflin-St Jeor 公式估算",
        "category": "metabolism",
        "subgroup": "base_energy",
        "featured": True,
    },
    # ========= 2.2. 热量规划 ======= 
    ## 2.2.1 每日热量需求 
    {
        "endpoint": "calorie",
        "name": "每日热量需求 TDEE",
        "path": "/calorie",
        "desc": "活动水平 + BMR 估算",
        "category": "metabolism",
        "subgroup": "calorie_plan",
        "featured": True,
    },
    ## 2.2.2 热量缺口 
    {
        "endpoint": "deficit",
        "name": "热量缺口/目标热量",
        "path": "/deficit",
        "desc": "减脂/增肌日摄入建议",
        "category": "metabolism",
        "subgroup": "calorie_plan",
        "featured": False,
    },
    # ===============
    # 3. 营养摄入 (TOOLS)
    # ================
    # ========= 3.1. 日常摄入 ===========
    # 3.1.1. 饮水
    {
        "endpoint": "water",
        "name": "每日饮水量",
        "path": "/water",
        "desc": "按体重估算建议",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    # 3.1.2. 蛋白质
    {
        "endpoint": "protein",
        "name": "蛋白质需求",
        "path": "/protein",
        "desc": "按目标建议摄入",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    # 3.1.3. 碳水
    {
        "endpoint": "carbs",
        "name": "碳水化合物需求计算器",
        "path": "/carbs",
        "desc": "估算每天建议摄入多少碳水",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": True,
    },
    # 3.1.4. 脂肪摄入
    {
        "endpoint": "fat-intake",
        "name": "脂肪摄入计算器",
        "path": "/fat-intake",
        "desc": "估算每天建议摄入多少脂肪",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    # 3.1.5. 膳食纤维
    {
        "endpoint": "fiber",
        "name": "膳食纤维计算器",
        "path": "/fiber",
        "desc": "查看每天建议纤维摄入量",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },
    # 3.1.6. 盐摄入
    {
        "endpoint": "salt",
        "name": "盐摄入估算器",
        "path": "/salt",
        "desc": "估算每日盐摄入是否偏高",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": False,
    },

    # ========= 3.2. 宏量营养 ===========
    # 3.2.1. 宏量营养
    {
        "endpoint": "macro",
        "name": "宏量营养素计算器",
        "path": "/macro",
        "desc": "分配蛋白质、碳水和脂肪",
        "category": "nutrition",
        "subgroup": "macro_nutrition",
        "featured": True,
    },
    # ========= 3.3. 饮食分配 ===========
    # 3.2.2. 餐次分配
    {
        "endpoint": "meal-split",
        "name": "餐次分配计算器",
        "path": "/meal-split",
        "desc": "把每日热量和蛋白质分配到三餐",
        "category": "nutrition",
        "subgroup": "meal_planning",
        "featured": False,
    },
    # 4. 运动与习惯
    # ========= 4.1. 运动消耗 ======= 
    ## 4.1.1 步数转热量
    {
        "endpoint": "steps",
        "name": "步数转热量",
        "path": "/steps",
        "desc": "粗略估算步行消耗",
        "category": "activity",
        "subgroup": "exercise",
        "featured": False,
    },
    # 4.1.2 步数转距离
    {
        "endpoint": "steps_distance",
        "name": "步数转距离计算器",
        "path": "/steps-distance",
        "desc": "估算步数大概等于多少公里",
        "category": "activity",
        "subgroup": "exercise",
        "featured": True,
    },
    # 4.1.3 步数转步行时间
    {
        "endpoint": "steps_time",
        "name": "步数转步行时间计算器",
        "path": "/steps-time",
        "desc": "估算这些步数大概要走多久",
        "category": "activity",
        "subgroup": "exercise",
        "featured": True,
    },
    # 4.1.4 每日步数目标
    {
        "endpoint": "step_goal",
        "name": "每日步数目标计算器",
        "path": "/step-goal",
        "desc": "按目标估算每天建议走多少步",
        "category": "activity",
        "subgroup": "exercise",
        "featured": False,
    },
    # 4.1.5 活动量等级
    {
        "endpoint": "activity_level",
        "name": "活动量等级计算器",
        "path": "/activity-level",
        "desc": "判断你属于哪种日常活动水平",
        "category": "activity",
        "subgroup": "exercise",
        "featured": True,
    },
    # 4.1.6 跑步消耗计算器
    {
        "endpoint": "running_kcal",
        "name": "跑步消耗计算器",
        "path": "/running-kcal",
        "desc": "按时间和速度估算跑步热量消耗",
        "category": "activity",
        "subgroup": "exercise",
        "featured": True,
    },
    # ========= 4.2. 睡眠时间 ======= 
    # 4.2.1 睡眠周期
    {
        "endpoint": "sleep",
        "name": "睡眠周期",
        "path": "/sleep",
        "desc": "90 分钟周期时间点",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": False,
    },
    # 4.2.2 睡眠需求
    {
        "endpoint": "sleep_need",
        "name": "睡眠需求计算器",
        "path": "/sleep-need",
        "desc": "按年龄查看建议睡眠时长",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": True,
    },
    # 4.2.3 睡眠时长
    {
        "endpoint": "sleep_duration",
        "name": "睡眠时长计算器",
        "path": "/sleep-duration",
        "desc": "计算从几点睡到几点起一共睡了多久",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": False,
    },
    # 4.2.4 补觉时间
    {
        "endpoint": "sleep_recovery",
        "name": "补觉时间计算器",
        "path": "/sleep-recovery",
        "desc": "估算睡眠不足后大概要补多久",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": False,
    },
    # 4.2.5 午睡时间
    {
        "endpoint": "nap_time",
        "name": "午睡时间计算器",
        "path": "/nap-time",
        "desc": "估算午睡多久更不容易醒来头昏",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": False,
    },
    # ========= 4.3. 睡眠质量 ======= 
    # 4.3.1 睡眠债
    {
        "endpoint": "sleep_debt",
        "name": "睡眠债计算器",
        "path": "/sleep-debt",
        "desc": "估算一周累计少睡了多少小时",
        "category": "activity",
        "subgroup": "sleep_quality",
        "featured": True,
    },
    # 4.3.2 睡眠效率
    {
        "endpoint": "sleep_efficiency",
        "name": "睡眠效率计算器",
        "path": "/sleep-efficiency",
        "desc": "估算躺床时间里有多少真正睡着了",
        "category": "activity",
        "subgroup": "sleep_quality",
        "featured": True,
    },
    # 4.3.3 咖啡因截止时间
    {
        "endpoint": "caffeine_cutoff",
        "name": "咖啡因截止时间计算器",
        "path": "/caffeine-cutoff",
        "desc": "估算今晚想睡好最晚几点别再喝咖啡",
        "category": "activity",
        "subgroup": "sleep_quality",
        "featured": True,
    },
    # 4.3.4 时差恢复
    {
        "endpoint": "jet_lag",
        "name": "时差恢复计算器",
        "path": "/jet-lag",
        "desc": "估算跨时区后大概要几天恢复作息",
        "category": "activity",
        "subgroup": "sleep_quality",
        "featured": True,
    },
    # 4.3.5 作息类型
    {
        "endpoint": "chronotype",
        "name": "作息类型测试",
        "path": "/chronotype",
        "desc": "测试你更像早鸟型还是夜猫型",
        "category": "activity",
        "subgroup": "sleep_quality",
        "featured": True,
    },
    # 5. 孕期工具
    # ========= 5.1. 基础孕期 ======= 
    # 5.1.1 预产期计算
    {
        "endpoint": "pregnancy_due_date",
        "name": "预产期计算器",
        "path": "/pregnancy-due-date",
        "desc": "末次月经推算预产期与孕周",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": True,
    },
    # 5.1.2 怀孕周数
    {
        "endpoint": "pregnancy_week",
        "name": "怀孕周数计算器",
        "path": "/pregnancy-week",
        "desc": "计算当前孕周、孕期阶段与预产期",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": False,
    },
    # 5.1.3 预测排卵日
    {
        "endpoint": "ovulation",
        "name": "排卵期计算器",
        "path": "/ovulation",
        "desc": "预测排卵日与易孕期",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": False,
    },
    # 5.1.4 受孕日期
    {
        "endpoint": "conception_date",
        "name": "受孕日期推算器",
        "path": "/conception-date",
        "desc": "推算宝宝可能受孕时间",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": False,
    },
    # ========= 5.2. 孕期健康 ======= 
    # 5.2.1 孕期体重增长
    {
        "endpoint": "pregnancy_weight",
        "name": "孕期体重增长计算器",
        "path": "/pregnancy-weight",
        "desc": "根据BMI计算孕期体重增长范围",
        "category": "pregnancy",
        "subgroup": "pregnancy_health",
        "featured": False,
    },
    # 5.2.2 孕期热量需求
    {
        "endpoint": "pregnancy_calorie",
        "name": "孕期热量需求计算器",
        "path": "/pregnancy-calorie",
        "desc": "估算孕期每日热量需求",
        "category": "pregnancy",
        "subgroup": "pregnancy_health",
        "featured": False,
    },
    # 5.2.3 孕期蛋白质
    {
        "endpoint": "pregnancy_protein",
        "name": "孕期蛋白质需求计算器",
        "path": "/pregnancy-protein",
        "desc": "估算孕期每日蛋白质摄入",
        "category": "pregnancy",
        "subgroup": "pregnancy_health",
        "featured": False,
    },
    # 5.2.4 胎儿发育周数
    {
        "endpoint": "fetal_development",
        "name": "胎儿发育周数图",
        "path": "/fetal-development",
        "desc": "查看不同孕周的胎儿发育阶段与进度",
        "category": "pregnancy",
        "subgroup": "pregnancy_health",
        "featured": True,
    },
    # 5.2.5 孕期饮水量
    {
        "endpoint": "pregnancy_water",
        "name": "孕期饮水量计算器",
        "path": "/pregnancy-water",
        "desc": "估算怀孕后每天建议喝多少水",
        "category": "pregnancy",
        "subgroup": "pregnancy_health",
        "featured": False,
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

# 1.2.2. 腰围风险
def waist_risk(wc_cm: float, height_cm: float) -> tuple[float, str]:
    whtr = wc_cm / height_cm
    if whtr < 0.5:
        level = "较好"
    elif whtr < 0.6:
        level = "需要注意"
    else:
        level = "风险较高"
    return whtr, level
# 1.2.3. 腰臀比
def whr_info(waist_cm: float, hip_cm: float, sex: str) -> dict:
    """
    Waist-to-Hip Ratio (WHR) calculator.

    Simple reference:
    male:
        < 0.90   -> 较低风险
        < 1.00   -> 需要注意
        >= 1.00  -> 风险较高

    female:
        < 0.80   -> 较低风险
        < 0.85   -> 需要注意
        >= 0.85  -> 风险较高
    """

    if waist_cm <= 0 or waist_cm > 300:
        raise ValueError("请输入合理的腰围（cm）。")
    if hip_cm <= 0 or hip_cm > 300:
        raise ValueError("请输入合理的臀围（cm）。")
    if sex not in ("male", "female"):
        raise ValueError("性别选择不正确。")

    ratio = waist_cm / hip_cm
    ratio_rounded = round1(ratio)

    if sex == "male":
        if ratio < 0.90:
            level = "较低风险"
            progress = 38
        elif ratio < 1.00:
            level = "需要注意"
            progress = 68
        else:
            level = "风险较高"
            progress = 88
    else:
        if ratio < 0.80:
            level = "较低风险"
            progress = 35
        elif ratio < 0.85:
            level = "需要注意"
            progress = 65
        else:
            level = "风险较高"
            progress = 88

    if sex == "male":
        ref_text = "男性常见参考：WHR < 0.90 通常更理想，0.90–0.99 需要注意，≥ 1.00 风险更高。"
    else:
        ref_text = "女性常见参考：WHR < 0.80 通常更理想，0.80–0.84 需要注意，≥ 0.85 风险更高。"

    return {
        "ratio": ratio_rounded,
        "level": level,
        "progress": progress,
        "ref_text": ref_text,
        "waist_cm": round1(waist_cm),
        "hip_cm": round1(hip_cm),
    }

# =============
# 3. 营养摄入
# =============

# ========= 3.1. 日常摄入 =======
# 3.1.1. 饮水

# ========= 3.2. 宏量营养 ======= 
# 3.2.1. 宏量营养
def macro_split(tdee: float, goal: str) -> dict:
    """
    Simple macro split by goal.
    Returns grams of protein, carbs, fat.

    Ratios:
    - fat_loss:    P 30% / C 35% / F 35%
    - maintain:    P 25% / C 45% / F 30%
    - muscle_gain: P 25% / C 50% / F 25%
    """

    if tdee <= 0 or tdee > 10000:
        raise ValueError("请输入合理的热量（kcal/天）。")

    if goal == "fat_loss":
        p_ratio, c_ratio, f_ratio = 0.30, 0.35, 0.35
        label = "减脂期"
    elif goal == "muscle_gain":
        p_ratio, c_ratio, f_ratio = 0.25, 0.50, 0.25
        label = "增肌期"
    else:
        p_ratio, c_ratio, f_ratio = 0.25, 0.45, 0.30
        label = "维持期"

    protein_kcal = tdee * p_ratio
    carbs_kcal = tdee * c_ratio
    fat_kcal = tdee * f_ratio

    protein_g = round0(protein_kcal / 4.0)
    carbs_g = round0(carbs_kcal / 4.0)
    fat_g = round0(fat_kcal / 9.0)

    return {
        "label": label,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_ratio": int(round(p_ratio * 100)),
        "carbs_ratio": int(round(c_ratio * 100)),
        "fat_ratio": int(round(f_ratio * 100)),
    }
# 3.2.2. 餐次分配
def meal_split_plan(total_kcal: float, protein_g: float, pattern: str) -> dict:
    """
    Split daily calories and protein across 3 meals.

    patterns:
    - balanced: breakfast 30 / lunch 35 / dinner 35
    - light_dinner: breakfast 30 / lunch 40 / dinner 30
    - big_dinner: breakfast 25 / lunch 30 / dinner 45
    """

    if total_kcal <= 0 or total_kcal > 10000:
        raise ValueError("请输入合理的每日热量（kcal/天）。")
    if protein_g <= 0 or protein_g > 500:
        raise ValueError("请输入合理的蛋白质（g/天）。")

    if pattern == "light_dinner":
        ratios = [0.30, 0.40, 0.30]
        label = "晚餐较轻"
    elif pattern == "big_dinner":
        ratios = [0.25, 0.30, 0.45]
        label = "晚餐较重"
    else:
        ratios = [0.30, 0.35, 0.35]
        label = "均衡三餐"

    # protein split: keep relatively even, but slightly follow meal pattern
    raw_protein = [protein_g * r for r in ratios]

    breakfast_kcal = round0(total_kcal * ratios[0])
    lunch_kcal = round0(total_kcal * ratios[1])
    dinner_kcal = round0(total_kcal * ratios[2])

    breakfast_p = round0(raw_protein[0])
    lunch_p = round0(raw_protein[1])
    dinner_p = round0(raw_protein[2])

    # adjust rounding drift
    kcal_diff = round0(total_kcal) - (breakfast_kcal + lunch_kcal + dinner_kcal)
    dinner_kcal += kcal_diff

    protein_diff = round0(protein_g) - (breakfast_p + lunch_p + dinner_p)
    dinner_p += protein_diff

    return {
        "label": label,
        "breakfast_kcal": breakfast_kcal,
        "lunch_kcal": lunch_kcal,
        "dinner_kcal": dinner_kcal,
        "breakfast_p": breakfast_p,
        "lunch_p": lunch_p,
        "dinner_p": dinner_p,
        "breakfast_ratio": int(round(ratios[0] * 100)),
        "lunch_ratio": int(round(ratios[1] * 100)),
        "dinner_ratio": int(round(ratios[2] * 100)),
    }
# 3.1.2. 蛋白质
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

# 3.1.3. 碳水
def carbs_need(weight_kg: float, goal: str) -> dict:
    """
    Simple carb recommendation by body weight and goal.
    Educational estimate only.

    g/kg reference:
    - fat_loss: 3.0
    - maintain: 4.0
    - muscle_gain: 5.0
    """

    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")

    if goal == "fat_loss":
        gpk = 3.0
        label = "减脂期"
        progress = 45
    elif goal == "muscle_gain":
        gpk = 5.0
        label = "增肌期"
        progress = 80
    else:
        gpk = 4.0
        label = "维持期"
        progress = 60

    grams = round0(weight_kg * gpk)
    kcal = round0(grams * 4)

    return {
        "label": label,
        "gpk": round1(gpk),
        "grams": grams,
        "kcal": kcal,
        "progress": progress,
    }

# 3.1.4. 脂肪摄入
def fat_need(weight_kg: float, goal: str) -> dict:
    """
    Simple fat recommendation by body weight and goal.
    Educational estimate only.

    g/kg reference:
    - fat_loss: 0.8
    - maintain: 1.0
    - muscle_gain: 1.1
    """

    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")

    if goal == "fat_loss":
        gpk = 0.8
        label = "减脂期"
        progress = 45
    elif goal == "muscle_gain":
        gpk = 1.1
        label = "增肌期"
        progress = 75
    else:
        gpk = 1.0
        label = "维持期"
        progress = 60

    grams = round0(weight_kg * gpk)
    kcal = round0(grams * 9)

    return {
        "label": label,
        "gpk": round1(gpk),
        "grams": grams,
        "kcal": kcal,
        "progress": progress,
    }

# 3.1.5. 膳食纤维
def fiber_need(kcal: float, sex: str) -> dict:
    """
    Simple fiber recommendation for site use.

    Base logic:
    - general rule: 14 g fiber per 1000 kcal
    - with a simple floor:
        male   >= 30 g/day
        female >= 25 g/day
    """

    if kcal <= 0 or kcal > 10000:
        raise ValueError("请输入合理的每日热量（kcal/天）。")

    if sex not in ("male", "female"):
        raise ValueError("性别选择不正确。")

    base = kcal / 1000.0 * 14.0
    floor_val = 30.0 if sex == "male" else 25.0
    grams = round0(max(base, floor_val))

    if grams < 25:
        level = "基础参考"
        progress = 45
    elif grams < 30:
        level = "常见参考"
        progress = 60
    elif grams < 35:
        level = "较充足参考"
        progress = 75
    else:
        level = "较高参考"
        progress = 85

    return {
        "grams": grams,
        "level": level,
        "progress": progress,
        "rule_text": "按每 1000 kcal 约 14 g 膳食纤维的站内简化规则估算",
    }
# 3.1.6. 盐摄入
def salt_estimate(
    home_meals: int,
    takeout_meals: int,
    soup_bowls: int,
    processed_servings: int,
    snack_servings: int,
) -> dict:
    """
    Very simplified site estimator for daily salt intake.

    Estimated salt sources (g/day):
    - home meal: 1.5 g
    - takeout / restaurant meal: 3.0 g
    - soup / broth bowl: 1.5 g
    - processed food serving: 1.2 g
    - salty snack serving: 0.8 g
    """

    vals = [home_meals, takeout_meals, soup_bowls, processed_servings, snack_servings]
    if any(v < 0 or v > 20 for v in vals):
        raise ValueError("请输入合理的份数。")

    total_salt = (
        home_meals * 1.5
        + takeout_meals * 3.0
        + soup_bowls * 1.5
        + processed_servings * 1.2
        + snack_servings * 0.8
    )

    total_salt = round1(total_salt)

    if total_salt <= 5:
        level = "大致在常见控制范围内"
        progress = 45
    elif total_salt <= 7:
        level = "略高，值得注意"
        progress = 70
    else:
        level = "偏高"
        progress = 90

    return {
        "total_salt": total_salt,
        "level": level,
        "progress": progress,
        "rule_text": "本工具采用站内简化估算模型，根据常见高盐食物场景粗略估算每日盐摄入。",
    }
# ========== 4.1. 运动消耗 ==========
# 4.1.1 步数转热量
def steps_to_kcal(steps: int, weight_kg: float) -> float:
    kcal_per_step = 0.05 * (weight_kg / 60.0)
    return steps * kcal_per_step
# 4.1.2 步数转距离
def steps_to_distance(steps: int, height_cm: float, sex: str) -> dict:
    """
    Estimate walking distance from step count.

    Simple stride model:
    - male stride length ≈ height * 0.415
    - female stride length ≈ height * 0.413

    result:
    - distance_m
    - distance_km
    """

    if steps <= 0 or steps > 200000:
        raise ValueError("请输入合理的步数。")
    if height_cm <= 0 or height_cm > 250:
        raise ValueError("请输入合理的身高（cm）。")
    if sex not in ("male", "female"):
        raise ValueError("性别选择不正确。")

    stride_factor = 0.415 if sex == "male" else 0.413
    stride_cm = height_cm * stride_factor
    distance_m = steps * stride_cm / 100.0
    distance_km = distance_m / 1000.0

    return {
        "stride_cm": round1(stride_cm),
        "distance_m": round0(distance_m),
        "distance_km": round1(distance_km),
    }
# 4.1.3 步数转步行时间
def steps_to_time(steps: int, pace: str) -> dict:
    """
    Estimate walking time from steps.

    pace:
    - slow:   80 steps/min
    - normal: 100 steps/min
    - fast:   120 steps/min
    """

    if steps <= 0 or steps > 200000:
        raise ValueError("请输入合理的步数。")

    if pace == "slow":
        spm = 80
        label = "较慢步速"
    elif pace == "fast":
        spm = 120
        label = "较快步速"
    else:
        spm = 100
        label = "常见步速"

    total_minutes = steps / spm
    hours = int(total_minutes // 60)
    minutes = int(round(total_minutes % 60))

    if minutes == 60:
        hours += 1
        minutes = 0

    return {
        "label": label,
        "spm": spm,
        "total_minutes": round1(total_minutes),
        "hours": hours,
        "minutes": minutes,
    }
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

# 4.1.4 每日步数目标
def step_goal_plan(current_steps: int, goal: str) -> dict:
    """
    Simple step goal estimator for daily planning.

    goal:
    - maintain: keep active
    - fat_loss: moderate step increase
    - active_upgrade: improve activity habit

    Returns:
    - target_steps
    - extra_steps
    - estimated_kcal (rough, based on average 0.04 kcal/step)
    """

    if current_steps < 0 or current_steps > 100000:
        raise ValueError("请输入合理的当前日均步数。")

    if goal == "fat_loss":
        extra_steps = 3000
        label = "减脂导向"
        progress = 80
    elif goal == "active_upgrade":
        extra_steps = 2000
        label = "提升活动量"
        progress = 65
    else:
        extra_steps = 1000
        label = "维持活跃"
        progress = 50

    # floor by goal
    if goal == "fat_loss":
        base_floor = 8000
    elif goal == "active_upgrade":
        base_floor = 7000
    else:
        base_floor = 6000

    target_steps = max(base_floor, current_steps + extra_steps)

    # rough estimate
    kcal = round0(target_steps * 0.04)

    return {
        "label": label,
        "target_steps": target_steps,
        "extra_steps": target_steps - current_steps,
        "estimated_kcal": kcal,
        "progress": progress,
    }
# 4.1.5 活动量等级
def activity_level_info(steps_per_day: int, exercise_days: int, sit_hours: float) -> dict:
    """
    Estimate daily activity level using a simple site rule.

    Inputs:
    - steps_per_day: average daily steps
    - exercise_days: exercise sessions per week
    - sit_hours: average sitting hours per day

    Output:
    - level
    - tdee_factor_hint
    """

    if steps_per_day < 0 or steps_per_day > 100000:
        raise ValueError("请输入合理的日均步数。")
    if exercise_days < 0 or exercise_days > 14:
        raise ValueError("请输入合理的每周运动天数。")
    if sit_hours < 0 or sit_hours > 24:
        raise ValueError("请输入合理的久坐时长。")

    score = 0

    if steps_per_day < 5000:
        score += 0
    elif steps_per_day < 8000:
        score += 1
    elif steps_per_day < 11000:
        score += 2
    else:
        score += 3

    if exercise_days <= 1:
        score += 0
    elif exercise_days <= 3:
        score += 1
    elif exercise_days <= 5:
        score += 2
    else:
        score += 3

    if sit_hours >= 10:
        score -= 1
    elif sit_hours <= 6:
        score += 1

    if score <= 1:
        level = "久坐型"
        desc = "你的整体日常活动量偏低，通常更接近久坐生活方式。"
        factor = "1.2 左右"
        progress = 25
    elif score <= 3:
        level = "轻度活动"
        desc = "你有一定活动量，但整体仍属于轻度活动范围。"
        factor = "1.375 左右"
        progress = 45
    elif score <= 5:
        level = "中度活动"
        desc = "你的日常步数和运动频率已经达到中等活动水平。"
        factor = "1.55 左右"
        progress = 65
    elif score <= 7:
        level = "较高活动"
        desc = "你的日常活动量较高，通常已经明显高于普通久坐人群。"
        factor = "1.725 左右"
        progress = 82
    else:
        level = "高活动量"
        desc = "你的活动频率和步数都较高，更接近高活动状态。"
        factor = "1.9 左右"
        progress = 92

    return {
        "level": level,
        "desc": desc,
        "factor": factor,
        "progress": progress,
    }
# 4.1.6 跑步消耗计算器
def running_kcal_estimate(weight_kg: float, minutes: float, pace: str) -> dict:
    """
    Estimate running calories using simple MET values.

    pace:
    - easy:  MET 8.3
    - normal: MET 9.8
    - fast:  MET 11.0

    kcal = MET * weight_kg * hours
    """

    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")
    if minutes <= 0 or minutes > 600:
        raise ValueError("请输入合理的跑步时间（分钟）。")

    if pace == "easy":
        met = 8.3
        label = "轻松跑"
        progress = 45
    elif pace == "fast":
        met = 11.0
        label = "较快跑"
        progress = 85
    else:
        met = 9.8
        label = "常见配速"
        progress = 65

    hours = minutes / 60.0
    kcal = round0(met * weight_kg * hours)

    return {
        "label": label,
        "met": met,
        "kcal": kcal,
        "minutes": round1(minutes),
        "progress": progress,
    }
# ========= 1.1. BMI与体重 ======= 
#1.1.3 目标体重时间
def weeks_to_goal(current_kg: float, target_kg: float, rate_kg_per_week: float) -> float:
    diff = abs(target_kg - current_kg)
    if rate_kg_per_week <= 0:
        return float("inf")
    return diff / rate_kg_per_week

# Pregnancy
def pregnancy_week_info(lmp_date: date) -> dict:
    """
    Calculate pregnancy week info based on LMP (last menstrual period).
    Medical convention: pregnancy starts from the first day of LMP.
    Full term is about 280 days / 40 weeks.
    """
    today = date.today()
    days_pregnant = (today - lmp_date).days

    if days_pregnant < 0:
        raise ValueError("末次月经日期不能晚于今天。")

    week = days_pregnant // 7
    day_in_week = days_pregnant % 7

    due_date = lmp_date + timedelta(days=280)
    days_left = (due_date - today).days

    if week < 13:
        trimester = "孕早期"
    elif week < 28:
        trimester = "孕中期"
    else:
        trimester = "孕晚期"

    progress = max(0, min(100, round(days_pregnant / 280 * 100)))

    return {
        "today": today.strftime("%Y-%m-%d"),
        "days_pregnant": days_pregnant,
        "week": week,
        "day_in_week": day_in_week,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "days_left": days_left,
        "trimester": trimester,
        "progress": progress,
    }

#排卵期
def ovulation_info(lmp_date: date, cycle_length: int) -> dict:
    """
    Calculate ovulation day and fertile window.
    Ovulation usually occurs ~14 days before next period.
    """

    ovulation_day = lmp_date + timedelta(days=(cycle_length - 14))

    fertile_start = ovulation_day - timedelta(days=5)
    fertile_end = ovulation_day + timedelta(days=1)

    next_period = lmp_date + timedelta(days=cycle_length)

    return {
        "ovulation_day": ovulation_day.strftime("%Y-%m-%d"),
        "fertile_start": fertile_start.strftime("%Y-%m-%d"),
        "fertile_end": fertile_end.strftime("%Y-%m-%d"),
        "next_period": next_period.strftime("%Y-%m-%d"),
    }

def conception_info(lmp_date: date) -> dict:
    """
    Estimate conception date based on LMP.
    Ovulation usually occurs about 14 days after LMP.
    """

    conception_date = lmp_date + timedelta(days=14)

    due_date = lmp_date + timedelta(days=280)

    return {
        "conception_date": conception_date.strftime("%Y-%m-%d"),
        "due_date": due_date.strftime("%Y-%m-%d"),
    }
def pregnancy_weight_gain(height_cm: float, weight_kg: float) -> dict:

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        low, high = 12.5, 18
        category = "偏瘦"
    elif bmi < 25:
        low, high = 11.5, 16
        category = "正常"
    elif bmi < 30:
        low, high = 7, 11.5
        category = "偏高"
    else:
        low, high = 5, 9
        category = "肥胖"

    return {
        "bmi": round(bmi, 1),
        "category": category,
        "low": low,
        "high": high
    }

def fetal_development_data(week: int) -> dict:
    """
    Return simple fetal development milestones by pregnancy week.
    Week should be 1-40.
    """
    if week < 1 or week > 40:
        raise ValueError("请输入 1 到 40 之间的孕周。")

    if week <= 4:
        stage = "孕早期"
        summary = "胚胎刚开始形成，受精卵着床，身体基础结构开始建立。"
        size = "非常微小，约种子大小"
    elif week <= 8:
        stage = "孕早期"
        summary = "神经系统、心脏和四肢开始发育，部分器官雏形逐步出现。"
        size = "约蓝莓到覆盆子大小"
    elif week <= 12:
        stage = "孕早期"
        summary = "进入较稳定阶段，面部轮廓、手指脚趾进一步清晰。"
        size = "约青柠大小"
    elif week <= 16:
        stage = "孕中期"
        summary = "骨骼进一步发育，胎儿活动开始增强，部分孕妇可能逐渐感受到变化。"
        size = "约牛油果大小"
    elif week <= 20:
        stage = "孕中期"
        summary = "听觉逐渐发育，肢体活动更明显，身体比例逐渐协调。"
        size = "约香蕉大小"
    elif week <= 24:
        stage = "孕中期"
        summary = "皮肤、肺部和神经系统持续发育，进入更关键的成长阶段。"
        size = "约玉米或长茄子大小"
    elif week <= 28:
        stage = "孕晚期"
        summary = "大脑快速发育，睡眠和活动节律逐渐形成。"
        size = "约菜花大小"
    elif week <= 32:
        stage = "孕晚期"
        summary = "脂肪逐渐堆积，身体开始为出生做准备。"
        size = "约椰子大小"
    elif week <= 36:
        stage = "孕晚期"
        summary = "器官更成熟，体重增长更快，胎位变化更值得关注。"
        size = "约蜜瓜大小"
    else:
        stage = "孕晚期"
        summary = "已接近足月，胎儿器官基本成熟，继续为分娩做准备。"
        size = "接近新生儿体型"

    progress = round(week / 40 * 100)

    return {
        "week": week,
        "stage": stage,
        "summary": summary,
        "size": size,
        "progress": progress,
    }

def pregnancy_calorie_need(base_kcal: float, trimester: str) -> dict:
    """
    Estimate daily calorie needs during pregnancy based on base daily calories.
    Reference pattern:
    - first trimester: +0 kcal
    - second trimester: +340 kcal
    - third trimester: +450 kcal
    """
    if trimester == "first":
        extra = 0
        label = "孕早期"
    elif trimester == "second":
        extra = 340
        label = "孕中期"
    elif trimester == "third":
        extra = 450
        label = "孕晚期"
    else:
        raise ValueError("孕期阶段选择不正确。")

    target = round0(base_kcal + extra)

    progress_map = {
        "first": 20,
        "second": 55,
        "third": 85,
    }

    return {
        "label": label,
        "extra": extra,
        "target": target,
        "progress": progress_map[trimester],
    }

def pregnancy_protein_need(weight_kg: float, trimester: str) -> dict:
    """
    Simple site formula for pregnancy protein needs.
    This is a simplified estimator for educational use, not a clinical prescription.

    Base formula:
    - first trimester: 1.0 g/kg
    - second trimester: 1.1 g/kg
    - third trimester: 1.2 g/kg
    """
    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")

    if trimester == "first":
        gpk = 1.0
        label = "孕早期"
        progress = 20
    elif trimester == "second":
        gpk = 1.1
        label = "孕中期"
        progress = 55
    elif trimester == "third":
        gpk = 1.2
        label = "孕晚期"
        progress = 85
    else:
        raise ValueError("孕期阶段选择不正确。")

    grams = round0(weight_kg * gpk)

    return {
        "label": label,
        "gpk": round(gpk, 1),
        "grams": grams,
        "progress": progress,
    }

def pregnancy_water_need(weight_kg: float, trimester: str) -> dict:
    """
    Simple site formula for pregnancy water needs.
    Educational estimate only.

    Base formula:
    - first trimester: 35 ml/kg
    - second trimester: 38 ml/kg
    - third trimester: 40 ml/kg
    """
    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")

    if trimester == "first":
        ml_per_kg = 35
        label = "孕早期"
        progress = 20
    elif trimester == "second":
        ml_per_kg = 38
        label = "孕中期"
        progress = 55
    elif trimester == "third":
        ml_per_kg = 40
        label = "孕晚期"
        progress = 85
    else:
        raise ValueError("孕期阶段选择不正确。")

    water_ml = round0(weight_kg * ml_per_kg)
    water_l = round1(water_ml / 1000.0)

    return {
        "label": label,
        "ml_per_kg": ml_per_kg,
        "water_ml": water_ml,
        "water_l": water_l,
        "progress": progress,
    }

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



def sleep_debt_info(actual_hours: float, target_hours: float, days: int) -> dict:
    """
    Estimate cumulative sleep debt.
    debt = max(0, target - actual) * days
    """
    if actual_hours <= 0 or actual_hours > 24:
        raise ValueError("请输入合理的实际睡眠时长。")
    if target_hours <= 0 or target_hours > 24:
        raise ValueError("请输入合理的目标睡眠时长。")
    if days <= 0 or days > 31:
        raise ValueError("请输入合理的统计天数。")

    daily_gap = max(0.0, target_hours - actual_hours)
    total_debt = daily_gap * days
    completion = 0 if target_hours == 0 else round((actual_hours / target_hours) * 100)
    completion = max(0, min(100, completion))

    if daily_gap == 0:
        level = "基本达标"
    elif daily_gap < 1:
        level = "轻度睡眠不足"
    elif daily_gap < 2:
        level = "中度睡眠不足"
    else:
        level = "明显睡眠不足"

    return {
        "daily_gap": round1(daily_gap),
        "total_debt": round1(total_debt),
        "completion": completion,
        "level": level,
    }

def sleep_recovery_info(debt_hours: float, recovery_ratio: float) -> dict:
    """
    Estimate recovery sleep time.
    recovery_ratio means how much extra sleep per day the user plans to add.

    Example:
    debt = 6 hours
    recovery_ratio = 1.0 hour/day
    -> about 6 days
    """
    if debt_hours < 0 or debt_hours > 200:
        raise ValueError("请输入合理的睡眠债时长。")
    if recovery_ratio <= 0 or recovery_ratio > 8:
        raise ValueError("请输入合理的每日补觉时长。")

    if debt_hours == 0:
        days_needed = 0.0
    else:
        days_needed = debt_hours / recovery_ratio

    if debt_hours == 0:
        level = "无需额外补觉"
    elif days_needed <= 3:
        level = "短期可调整"
    elif days_needed <= 7:
        level = "需要一周内逐步恢复"
    else:
        level = "建议优先调整整体作息"

    progress = 100 if debt_hours == 0 else max(5, min(100, round((recovery_ratio / max(debt_hours, 1)) * 100 * 2)))

    return {
        "days_needed": round1(days_needed),
        "level": level,
        "progress": progress,
    }
# ========= 4.2. 睡眠时间 ======= 
# 4.2.3 睡眠时长
def sleep_duration_info(bed_hm: str, wake_hm: str, target_hours: float = 8.0) -> dict:
    """
    Calculate sleep duration from bedtime to wake time.
    Supports crossing midnight.

    bed_hm / wake_hm format: HH:MM
    """
    def parse_hm(s: str) -> tuple[int, int]:
        s = s.strip()
        if ":" not in s:
            raise ValueError("请输入正确时间格式，例如 23:30。")
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("请输入正确时间。")
        return h, m

    bed_h, bed_m = parse_hm(bed_hm)
    wake_h, wake_m = parse_hm(wake_hm)

    bed_total = bed_h * 60 + bed_m
    wake_total = wake_h * 60 + wake_m

    if wake_total <= bed_total:
        wake_total += 24 * 60  # cross midnight

    duration_min = wake_total - bed_total
    hours = duration_min // 60
    minutes = duration_min % 60
    duration_hours = duration_min / 60.0

    gap = round1(duration_hours - target_hours)
    completion = max(0, min(100, round(duration_hours / target_hours * 100)))

    if duration_hours < 6:
        level = "睡眠偏少"
    elif duration_hours < 7:
        level = "略少"
    elif duration_hours <= 9:
        level = "较常见范围"
    else:
        level = "偏长"

    return {
        "hours": int(hours),
        "minutes": int(minutes),
        "duration_hours": round1(duration_hours),
        "gap": gap,
        "completion": completion,
        "level": level,
        "bed_hm": bed_hm,
        "wake_hm": wake_hm,
        "target_hours": target_hours,
    }

def nap_time_info(mode: str, time_hm: str) -> dict:
    """
    Nap calculator:
    - short nap: about 20 min
    - full cycle nap: about 90 min
    Supports:
    - nap_now: input current time, output suggested wake times
    - wake_at: input desired wake time, output suggested nap start times
    """

    def parse_hm(s: str) -> tuple[int, int]:
        s = s.strip()
        if ":" not in s:
            raise ValueError("请输入正确时间格式，例如 13:20。")
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("请输入正确时间。")
        return h, m

    def add_minutes(h: int, m: int, minutes: int) -> tuple[int, int]:
        total = h * 60 + m + minutes
        total %= 24 * 60
        return total // 60, total % 60

    def fmt(h: int, m: int) -> str:
        return f"{h:02d}:{m:02d}"

    h, m = parse_hm(time_hm)

    short_nap = 20
    full_cycle = 90

    if mode == "nap_now":
        short_h, short_m = add_minutes(h, m, short_nap)
        full_h, full_m = add_minutes(h, m, full_cycle)
        return {
            "mode_label": "现在开始午睡",
            "short_label": "短午睡（约 20 分钟）",
            "short_time": fmt(short_h, short_m),
            "full_label": "完整周期午睡（约 90 分钟）",
            "full_time": fmt(full_h, full_m),
        }

    if mode == "wake_at":
        short_h, short_m = add_minutes(h, m, -short_nap)
        full_h, full_m = add_minutes(h, m, -full_cycle)
        return {
            "mode_label": "按目标起床时间倒推",
            "short_label": "短午睡建议开始时间",
            "short_time": fmt(short_h, short_m),
            "full_label": "完整周期午睡建议开始时间",
            "full_time": fmt(full_h, full_m),
        }

    raise ValueError("模式选择不正确。")

def sleep_need_by_age(age: int) -> dict:
    """
    Simplified age-based sleep recommendation ranges.
    Educational use only.
    """

    if age < 0 or age > 120:
        raise ValueError("请输入合理年龄。")

    if age <= 2:
        low, high = 11, 14
        label = "婴幼儿"
        note = "这一阶段通常需要更长睡眠，白天小睡也常见。"
        progress = 95
    elif age <= 5:
        low, high = 10, 13
        label = "学龄前儿童"
        note = "学龄前儿童通常需要较长总睡眠时长。"
        progress = 90
    elif age <= 12:
        low, high = 9, 12
        label = "儿童"
        note = "儿童阶段通常仍需要充足睡眠支持日常学习与恢复。"
        progress = 80
    elif age <= 17:
        low, high = 8, 10
        label = "青少年"
        note = "青少年通常仍需要比成年人更长的睡眠时间。"
        progress = 70
    elif age <= 64:
        low, high = 7, 9
        label = "成年人"
        note = "大多数成年人常见建议睡眠范围约为 7–9 小时。"
        progress = 60
    else:
        low, high = 7, 8
        label = "老年人"
        note = "老年人通常仍需要规律而稳定的睡眠。"
        progress = 55

    midpoint = round1((low + high) / 2)

    return {
        "label": label,
        "low": low,
        "high": high,
        "midpoint": midpoint,
        "note": note,
        "progress": progress,
    }

def sleep_efficiency_info(
    bed_hm: str,
    wake_hm: str,
    sleep_latency_min: int,
    awake_during_night_min: int
) -> dict:
    """
    Sleep efficiency = actual sleep time / time in bed * 100

    Inputs:
    - bed_hm: time went to bed
    - wake_hm: final wake-up time
    - sleep_latency_min: how many minutes it took to fall asleep
    - awake_during_night_min: total minutes awake during the night
    """

    def parse_hm(s: str) -> tuple[int, int]:
        s = s.strip()
        if ":" not in s:
            raise ValueError("请输入正确时间格式，例如 23:00。")
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("请输入正确时间。")
        return h, m

    bed_h, bed_m = parse_hm(bed_hm)
    wake_h, wake_m = parse_hm(wake_hm)

    if sleep_latency_min < 0 or sleep_latency_min > 600:
        raise ValueError("请输入合理的入睡耗时（分钟）。")
    if awake_during_night_min < 0 or awake_during_night_min > 600:
        raise ValueError("请输入合理的夜间清醒时长（分钟）。")

    bed_total = bed_h * 60 + bed_m
    wake_total = wake_h * 60 + wake_m

    if wake_total <= bed_total:
        wake_total += 24 * 60

    time_in_bed_min = wake_total - bed_total
    actual_sleep_min = time_in_bed_min - sleep_latency_min - awake_during_night_min

    if actual_sleep_min < 0:
        raise ValueError("输入数据不合理：实际睡眠时间不能小于 0。")

    efficiency = round(actual_sleep_min / time_in_bed_min * 100, 1) if time_in_bed_min > 0 else 0.0

    if efficiency >= 90:
        level = "较高"
    elif efficiency >= 85:
        level = "一般较常见"
    else:
        level = "偏低"

    sleep_hours = actual_sleep_min // 60
    sleep_minutes = actual_sleep_min % 60

    return {
        "time_in_bed_min": time_in_bed_min,
        "actual_sleep_min": actual_sleep_min,
        "sleep_hours": int(sleep_hours),
        "sleep_minutes": int(sleep_minutes),
        "efficiency": efficiency,
        "level": level,
    }

def caffeine_cutoff_info(sleep_hm: str, cutoff_hours: float = 6.0) -> dict:
    """
    Estimate caffeine cutoff time before bed.
    Simple educational logic:
    cutoff time = bedtime - cutoff_hours
    """

    def parse_hm(s: str) -> tuple[int, int]:
        s = s.strip()
        if ":" not in s:
            raise ValueError("请输入正确时间格式，例如 23:00。")
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("请输入正确时间。")
        return h, m

    def add_minutes(h: int, m: int, minutes: int) -> tuple[int, int]:
        total = h * 60 + m + minutes
        total %= 24 * 60
        return total // 60, total % 60

    def fmt(h: int, m: int) -> str:
        return f"{h:02d}:{m:02d}"

    if cutoff_hours <= 0 or cutoff_hours > 12:
        raise ValueError("请输入合理的截止时长。")

    h, m = parse_hm(sleep_hm)
    cutoff_min = int(round(cutoff_hours * 60))
    ch, cm = add_minutes(h, m, -cutoff_min)

    return {
        "sleep_time": sleep_hm,
        "cutoff_time": fmt(ch, cm),
        "cutoff_hours": round(cutoff_hours, 1),
    }

def jet_lag_info(timezones_crossed: int, direction: str) -> dict:
    """
    Estimate jet lag recovery time with a simple practical rule.

    direction:
    - east: harder, about 1 day per timezone
    - west: easier, about 1 day per 2 timezones
    """

    if timezones_crossed < 0 or timezones_crossed > 24:
        raise ValueError("请输入合理的跨时区数量。")

    if direction == "east":
        days_needed = float(timezones_crossed)
        label = "向东飞"
        note = "向东飞通常更难适应，因为需要更早入睡和更早起床。"
    elif direction == "west":
        days_needed = round(timezones_crossed / 2.0, 1)
        label = "向西飞"
        note = "向西飞通常相对更容易，因为很多人更容易晚睡一点。"
    else:
        raise ValueError("飞行方向选择不正确。")

    if timezones_crossed == 0:
        level = "几乎没有明显时差"
    elif days_needed <= 2:
        level = "短期可适应"
    elif days_needed <= 5:
        level = "中等恢复期"
    else:
        level = "恢复时间可能较长"

    progress = 0 if timezones_crossed == 0 else min(100, max(10, round(days_needed / 10 * 100)))

    return {
        "label": label,
        "days_needed": days_needed,
        "note": note,
        "level": level,
        "progress": progress,
    }

def chronotype_result(score: int) -> dict:
    """
    Simple chronotype scoring.
    Lower score => earlier rhythm
    Higher score => later rhythm
    """

    if score <= 7:
        return {
            "type": "早鸟型",
            "title": "你更偏早鸟型作息",
            "desc": "你通常更适合较早进入状态，也更容易在早些时候入睡和起床。",
            "tip": "尽量把重要任务安排在上午，保持固定起床时间通常更适合你。",
            "window": "推荐作息倾向：较早睡、较早起",
        }
    elif score <= 11:
        return {
            "type": "中间型",
            "title": "你更偏中间型作息",
            "desc": "你的作息弹性相对更大，既不会特别早，也不会特别晚，更容易适应常见日程。",
            "tip": "重点不是极端早睡或晚睡，而是尽量保持节律稳定。",
            "window": "推荐作息倾向：中等时间入睡和起床",
        }
    else:
        return {
            "type": "夜猫型",
            "title": "你更偏夜猫型作息",
            "desc": "你可能在傍晚到夜间更容易进入状态，也更不容易太早入睡。",
            "tip": "如果必须早起，建议提前几天慢慢前移作息，而不是突然强行早睡。",
            "window": "推荐作息倾向：较晚睡、较晚起",
        }


# -----------------------
# 3. Pages
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
# Tool: BMI
# -----------------------
# 1. 体重与体型
# ========= 1.1. BMI与体重 ======= 
## 1.1.1 BMI (Route)
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
# Tool: Deficit
# -----------------------
# 2. 代谢与热量
# ========= 2.2. 热量规划 ======= 
## 2.2.1 热量缺口
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
# Tool: pregnancy
# -----------------------
# 5. 孕期工具
# ========= 5.1. 基础孕期 ======= 
## 5.1.1 预产期计算
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
# 5.1.2 怀孕周数
@app.route("/pregnancy-week", methods=["GET", "POST"])
def pregnancy_week():
    error = None
    lmp_in = ""
    result = None

    if request.method == "POST":
        lmp_in = request.form.get("lmp", "").strip()

        try:
            if not lmp_in:
                raise ValueError("请输入末次月经日期。")

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()
            result = pregnancy_week_info(lmp_date)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效日期。"

    meta = {
        "title": "怀孕周数计算器（实时孕周与预产期）- 健康工具站",
        "description": "输入末次月经日期，计算当前怀孕周数、孕期阶段、预产期和孕期进度，并提供公式说明与相关孕期工具。",
        "canonical": canonical_url("/pregnancy-week"),
    }

    return render_template(
        "pregnancy_week.html",
        meta=meta,
        error=error,
        lmp_in=lmp_in,
        result=result,
        page_kind="tool",
    )
# 5.1.3 预测排卵日
@app.route("/ovulation", methods=["GET", "POST"])
def ovulation():

    error = None
    result = None
    lmp_in = ""
    cycle_in = "28"

    if request.method == "POST":

        lmp_in = request.form.get("lmp", "").strip()
        cycle_in = request.form.get("cycle", "28")

        try:

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()
            cycle_length = int(cycle_in)

            if cycle_length < 21 or cycle_length > 45:
                raise ValueError("月经周期通常在21–45天之间")

            result = ovulation_info(lmp_date, cycle_length)

        except Exception as e:
            error = str(e)

    meta = {
        "title": "排卵期计算器（易孕期与排卵日预测）",
        "description": "输入末次月经和周期长度，计算排卵日、易孕期和下次月经日期。",
        "canonical": canonical_url("/ovulation"),
    }

    return render_template(
        "ovulation.html",
        meta=meta,
        result=result,
        error=error,
        lmp_in=lmp_in,
        cycle_in=cycle_in,
        page_kind="tool",
    )
# 5.1.4 受孕日期
@app.route("/conception-date", methods=["GET", "POST"])
def conception_date():

    error = None
    result = None
    lmp_in = ""

    if request.method == "POST":

        lmp_in = request.form.get("lmp", "").strip()

        try:

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()

            result = conception_info(lmp_date)

        except Exception:
            error = "请输入有效日期"

    meta = {
        "title": "受孕日期推算器（宝宝大概什么时候怀上的）",
        "description": "根据末次月经推算可能的受孕日期，同时显示预产期参考。",
        "canonical": canonical_url("/conception-date"),
    }

    return render_template(
        "conception_date.html",
        meta=meta,
        result=result,
        error=error,
        lmp_in=lmp_in,
        page_kind="tool",
    )
# ========= 5.2. 孕期健康 ======= 
# 5.2.1 孕期体重增长
@app.route("/pregnancy-weight", methods=["GET", "POST"])
def pregnancy_weight():

    error = None
    result = None
    height_in = ""
    weight_in = ""

    if request.method == "POST":

        height_in = request.form.get("height_cm", "")
        weight_in = request.form.get("weight_kg", "")

        try:

            height = float(height_in)
            weight = float(weight_in)

            result = pregnancy_weight_gain(height, weight)

        except Exception:
            error = "请输入有效身高和体重"

    meta = {
        "title": "孕期体重增长计算器（Pregnancy Weight Gain Calculator）",
        "description": "根据孕前BMI计算孕期建议体重增长范围，并提供医学参考标准。",
        "canonical": canonical_url("/pregnancy-weight"),
    }

    return render_template(
        "pregnancy_weight.html",
        meta=meta,
        result=result,
        error=error,
        height_in=height_in,
        weight_in=weight_in,
        page_kind="tool",
    )
# 5.2.2 孕期热量需求 
@app.route("/pregnancy-calorie", methods=["GET", "POST"])
def pregnancy_calorie():
    error = None
    base_kcal_in = ""
    trimester_in = "first"
    result = None

    if request.method == "POST":
        base_kcal_in = request.form.get("base_kcal", "").strip()
        trimester_in = request.form.get("trimester", "first")

        try:
            base_kcal = float(base_kcal_in)

            if base_kcal <= 0 or base_kcal > 10000:
                raise ValueError("请输入合理的基础热量（kcal/天）。")

            result = pregnancy_calorie_need(base_kcal, trimester_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "孕期热量需求计算器（不同孕期每天该吃多少热量）- CalmyHealth",
        "description": "输入基础每日热量并选择孕期阶段，估算孕早期、孕中期、孕晚期每天建议摄入热量，并附公式说明、图表展示与相关孕期工具。",
        "canonical": canonical_url("/pregnancy-calorie"),
    }

    return render_template(
        "pregnancy_calorie.html",
        meta=meta,
        error=error,
        base_kcal_in=base_kcal_in,
        trimester_in=trimester_in,
        result=result,
        page_kind="tool",
    )
# 5.2.3 孕期蛋白质
@app.route("/pregnancy-protein", methods=["GET", "POST"])
def pregnancy_protein():
    error = None
    weight_kg_in = ""
    trimester_in = "first"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        trimester_in = request.form.get("trimester", "first")

        try:
            weight_kg = float(weight_kg_in)
            result = pregnancy_protein_need(weight_kg, trimester_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "孕期蛋白质需求计算器（怀孕后每天蛋白质该吃多少）- CalmyHealth",
        "description": "输入体重并选择孕期阶段，估算孕期每天蛋白质摄入建议，并附公式说明、结果图示和相关孕期工具内链。",
        "canonical": canonical_url("/pregnancy-protein"),
    }

    return render_template(
        "pregnancy_protein.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        trimester_in=trimester_in,
        result=result,
        page_kind="tool",
    )
# 5.2.4 胎儿发育周数
@app.route("/fetal-development", methods=["GET", "POST"])
def fetal_development():
    error = None
    week_in = ""
    result = None

    if request.method == "POST":
        week_in = request.form.get("week", "").strip()

        try:
            week = int(week_in)
            result = fetal_development_data(week)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效的孕周。"

    meta = {
        "title": "胎儿发育周数图（孕周发育进度查询）- CalmyHealth",
        "description": "输入孕周，查看胎儿发育阶段、40周进度和本周常见发育特点，并推荐相关孕期工具。",
        "canonical": canonical_url("/fetal-development"),
    }

    return render_template(
        "fetal_development.html",
        meta=meta,
        error=error,
        week_in=week_in,
        result=result,
        page_kind="tool",
    )
# 5.2.5 孕期饮水量
@app.route("/pregnancy-water", methods=["GET", "POST"])
def pregnancy_water():
    error = None
    weight_kg_in = ""
    trimester_in = "first"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        trimester_in = request.form.get("trimester", "first")

        try:
            weight_kg = float(weight_kg_in)
            result = pregnancy_water_need(weight_kg, trimester_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "孕期饮水量计算器（怀孕后每天建议喝多少水）- CalmyHealth",
        "description": "输入体重并选择孕期阶段，估算孕期每天建议饮水量，并附结果说明、公式解释和相关孕期工具内链。",
        "canonical": canonical_url("/pregnancy-water"),
    }

    return render_template(
        "pregnancy_water.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        trimester_in=trimester_in,
        result=result,
        page_kind="tool",
    )


# -----------------------
# Tool: BMR
# -----------------------
# 2. 代谢与热量
# ========= 2.1. 基础代谢 ======= 
## 2.1.1 基础代谢率BMR
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
# Tool: Goal Time
# -----------------------
# 1. 体重与体型
# ========= 1.1. BMI与体重 ======= 
# 1.1.3 目标体重 (Route)
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

# -----------------------
# Tool: TDEE
# -----------------------
# ========= 2.2. 热量规划 ======= 
## 2.2.1 每日热量需求 
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
# 3. 营养摄入
# ========= 3.1. 日常摄入 ======= 
## 3.1.1. 饮水
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
# ========= 4.2. 睡眠时间 ======= 
## 4.2.1 睡眠周期
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
# ========= 4.3. 睡眠质量 ======= 
## 4.3.1 睡眠债
@app.route("/sleep-debt", methods=["GET", "POST"])
def sleep_debt():
    error = None
    actual_in = "6.5"
    target_in = "8"
    days_in = "7"
    result = None

    if request.method == "POST":
        actual_in = request.form.get("actual_hours", "6.5").strip()
        target_in = request.form.get("target_hours", "8").strip()
        days_in = request.form.get("days", "7").strip()

        try:
            actual_hours = float(actual_in)
            target_hours = float(target_in)
            days = int(days_in)

            result = sleep_debt_info(actual_hours, target_hours, days)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "睡眠债计算器（这一周你到底欠了多少睡眠）- CalmyHealth",
        "description": "输入平均实际睡眠时长、目标睡眠时长和统计天数，估算累计睡眠债，并附结果说明、公式解释和相关睡眠工具推荐。",
        "canonical": canonical_url("/sleep-debt"),
    }

    return render_template(
        "sleep_debt.html",
        meta=meta,
        error=error,
        actual_in=actual_in,
        target_in=target_in,
        days_in=days_in,
        result=result,
        page_kind="tool",
    )
# ========= 4.2. 睡眠时间 ======= 
## 4.2.4 补觉时间 (Route)
@app.route("/sleep-recovery", methods=["GET", "POST"])
def sleep_recovery():
    error = None
    debt_in = "6"
    recovery_in = "1"
    result = None

    if request.method == "POST":
        debt_in = request.form.get("debt_hours", "6").strip()
        recovery_in = request.form.get("recovery_hours", "1").strip()

        try:
            debt_hours = float(debt_in)
            recovery_hours = float(recovery_in)
            result = sleep_recovery_info(debt_hours, recovery_hours)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "补觉时间计算器（睡不够后大概要补多久）- CalmyHealth",
        "description": "输入累计睡眠债和你计划每天额外补觉的时长，估算大概需要多少天恢复，并附结果说明、公式解释和相关睡眠工具推荐。",
        "canonical": canonical_url("/sleep-recovery"),
    }

    return render_template(
        "sleep_recovery.html",
        meta=meta,
        error=error,
        debt_in=debt_in,
        recovery_in=recovery_in,
        result=result,
        page_kind="tool",
    )
# 4.2.3 睡眠时长
@app.route("/sleep-duration", methods=["GET", "POST"])
def sleep_duration():
    error = None
    bed_in = "23:30"
    wake_in = "07:00"
    target_in = "8"
    result = None

    if request.method == "POST":
        bed_in = request.form.get("bed_hm", "23:30").strip()
        wake_in = request.form.get("wake_hm", "07:00").strip()
        target_in = request.form.get("target_hours", "8").strip()

        try:
            target_hours = float(target_in)
            if target_hours <= 0 or target_hours > 24:
                raise ValueError("请输入合理的目标睡眠时长。")

            result = sleep_duration_info(bed_in, wake_in, target_hours)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "睡眠时长计算器（从几点睡到几点起一共睡了多久）- CalmyHealth",
        "description": "输入入睡时间、起床时间和目标睡眠时长，计算总睡眠时间、和目标的差距，并附时间轴展示、公式说明与相关睡眠工具推荐。",
        "canonical": canonical_url("/sleep-duration"),
    }

    return render_template(
        "sleep_duration.html",
        meta=meta,
        error=error,
        bed_in=bed_in,
        wake_in=wake_in,
        target_in=target_in,
        result=result,
        page_kind="tool",
    )
# 4.2.5 午睡时间
@app.route("/nap-time", methods=["GET", "POST"])
def nap_time():
    error = None
    mode_in = "nap_now"
    time_in = "13:30"
    result = None

    if request.method == "POST":
        mode_in = request.form.get("mode", "nap_now").strip()
        time_in = request.form.get("time_hm", "13:30").strip()

        try:
            result = nap_time_info(mode_in, time_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "午睡时间计算器（午睡多久不容易醒来头昏）- CalmyHealth",
        "description": "输入现在时间或目标起床时间，计算短午睡和完整周期午睡的推荐时间点，帮助减少午睡后头昏、睡懵和睡过头。",
        "canonical": canonical_url("/nap-time"),
    }

    return render_template(
        "nap_time.html",
        meta=meta,
        error=error,
        mode_in=mode_in,
        time_in=time_in,
        result=result,
        page_kind="tool",
    )
# ========= 4.3. 睡眠质量 ======= 
# 4.3.4 时差恢复
@app.route("/jet-lag", methods=["GET", "POST"])
def jet_lag():
    error = None
    zones_in = "6"
    direction_in = "east"
    result = None

    if request.method == "POST":
        zones_in = request.form.get("timezones_crossed", "6").strip()
        direction_in = request.form.get("direction", "east").strip()

        try:
            timezones_crossed = int(zones_in)
            result = jet_lag_info(timezones_crossed, direction_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "时差恢复计算器（跨时区后大概要几天恢复作息）- CalmyHealth",
        "description": "输入跨越的时区数量和飞行方向，估算时差恢复所需天数，并了解向东飞、向西飞对睡眠节律的不同影响。",
        "canonical": canonical_url("/jet-lag"),
    }

    return render_template(
        "jet_lag.html",
        meta=meta,
        error=error,
        zones_in=zones_in,
        direction_in=direction_in,
        result=result,
        page_kind="tool",
    )
# 4.3.5 作息类型
@app.route("/chronotype", methods=["GET", "POST"])
def chronotype():
    error = None
    result = None
    answers = {
        "sleepy_time": "2",
        "wake_without_alarm": "2",
        "best_focus": "2",
        "weekend_shift": "2",
        "morning_feeling": "2",
    }

    if request.method == "POST":
        try:
            answers["sleepy_time"] = request.form.get("sleepy_time", "2").strip()
            answers["wake_without_alarm"] = request.form.get("wake_without_alarm", "2").strip()
            answers["best_focus"] = request.form.get("best_focus", "2").strip()
            answers["weekend_shift"] = request.form.get("weekend_shift", "2").strip()
            answers["morning_feeling"] = request.form.get("morning_feeling", "2").strip()

            score = sum(int(v) for v in answers.values())
            result = chronotype_result(score)
            result["score"] = score

        except Exception:
            error = "请完成所有选项后再提交。"

    meta = {
        "title": "作息类型测试（你是早鸟型还是夜猫型）- CalmyHealth",
        "description": "通过几个简单问题测试你更像早鸟型、夜猫型还是中间型作息，并查看更适合自己的睡眠节律建议。",
        "canonical": canonical_url("/chronotype"),
    }

    return render_template(
        "chronotype.html",
        meta=meta,
        error=error,
        result=result,
        answers=answers,
        page_kind="tool",
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

@app.route("/sleep-need", methods=["GET", "POST"])
def sleep_need():
    error = None
    age_in = "30"
    result = None

    if request.method == "POST":
        age_in = request.form.get("age", "30").strip()

        try:
            age = int(age_in)
            result = sleep_need_by_age(age)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效年龄。"

    meta = {
        "title": "睡眠需求计算器（按年龄需要睡多久）- CalmyHealth",
        "description": "输入年龄，查看常见建议睡眠时长范围，并了解不同年龄阶段为什么需要不同睡眠时间。",
        "canonical": canonical_url("/sleep-need"),
    }

    return render_template(
        "sleep_need.html",
        meta=meta,
        error=error,
        age_in=age_in,
        result=result,
        page_kind="tool",
    )

@app.route("/caffeine-cutoff", methods=["GET", "POST"])
def caffeine_cutoff():
    error = None
    sleep_in = "23:00"
    cutoff_in = "6"
    result = None

    if request.method == "POST":
        sleep_in = request.form.get("sleep_hm", "23:00").strip()
        cutoff_in = request.form.get("cutoff_hours", "6").strip()

        try:
            cutoff_hours = float(cutoff_in)
            result = caffeine_cutoff_info(sleep_in, cutoff_hours)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "咖啡因截止时间计算器（今晚想睡好，最晚几点别再喝咖啡）- CalmyHealth",
        "description": "输入今晚预计睡觉时间，估算最晚几点后尽量不要再摄入咖啡因，帮助减少咖啡、茶、能量饮料对睡眠的影响。",
        "canonical": canonical_url("/caffeine-cutoff"),
    }

    return render_template(
        "caffeine_cutoff.html",
        meta=meta,
        error=error,
        sleep_in=sleep_in,
        cutoff_in=cutoff_in,
        result=result,
        page_kind="tool",
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

@app.route("/sleep-efficiency", methods=["GET", "POST"])
def sleep_efficiency():
    error = None
    bed_in = "23:00"
    wake_in = "07:00"
    latency_in = "20"
    awake_in = "30"
    result = None

    if request.method == "POST":
        bed_in = request.form.get("bed_hm", "23:00").strip()
        wake_in = request.form.get("wake_hm", "07:00").strip()
        latency_in = request.form.get("sleep_latency_min", "20").strip()
        awake_in = request.form.get("awake_during_night_min", "30").strip()

        try:
            sleep_latency_min = int(latency_in)
            awake_during_night_min = int(awake_in)

            result = sleep_efficiency_info(
                bed_in,
                wake_in,
                sleep_latency_min,
                awake_during_night_min,
            )

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "睡眠效率计算器（你躺床的时间有多少真正睡着了）- CalmyHealth",
        "description": "输入上床时间、起床时间、入睡耗时和夜间清醒时长，计算睡眠效率，帮助判断你躺床时间中有多少真正用于睡眠。",
        "canonical": canonical_url("/sleep-efficiency"),
    }

    return render_template(
        "sleep_efficiency.html",
        meta=meta,
        error=error,
        bed_in=bed_in,
        wake_in=wake_in,
        latency_in=latency_in,
        awake_in=awake_in,
        result=result,
        page_kind="tool",
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
# Tool: Daily intake
# -----------------------
# ========= 3.1. 日常摄入 ======= 
# 3.1.2. 蛋白质
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

# ======= 3.2. 宏量营养 ============
# 3.2.1. 宏量营养
@app.route("/macro", methods=["GET", "POST"])
def macro():
    error = None
    tdee_in = ""
    goal_in = "maintain"
    result = None

    if request.method == "POST":
        tdee_in = request.form.get("tdee", "").strip()
        goal_in = request.form.get("goal", "maintain").strip()

        try:
            tdee_val = float(tdee_in)
            if goal_in not in ("fat_loss", "maintain", "muscle_gain"):
                raise ValueError("目标选择不正确。")

            result = macro_split(tdee_val, goal_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "宏量营养素计算器（蛋白质、碳水、脂肪每天该吃多少）- CalmyHealth",
        "description": "输入每日总热量并选择目标，计算蛋白质、碳水和脂肪的建议分配，适合减脂、维持和增肌人群参考。",
        "canonical": canonical_url("/macro"),
    }

    return render_template(
        "macro.html",
        meta=meta,
        error=error,
        tdee_in=tdee_in,
        goal_in=goal_in,
        result=result,
        page_kind="tool",
    )

# 3.2.2. 餐次分配
@app.route("/meal-split", methods=["GET", "POST"])
def meal_split():
    error = None
    kcal_in = ""
    protein_in = ""
    pattern_in = "balanced"
    result = None

    if request.method == "POST":
        kcal_in = request.form.get("kcal", "").strip()
        protein_in = request.form.get("protein_g", "").strip()
        pattern_in = request.form.get("pattern", "balanced").strip()

        try:
            kcal_val = float(kcal_in)
            protein_val = float(protein_in)

            if pattern_in not in ("balanced", "light_dinner", "big_dinner"):
                raise ValueError("分配模式不正确。")

            result = meal_split_plan(kcal_val, protein_val, pattern_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "餐次分配计算器（一天三餐怎么分配热量和蛋白质）- CalmyHealth",
        "description": "输入每日总热量和蛋白质目标，把一天三餐的热量与蛋白质分配得更清楚，适合减脂、维持和增肌饮食安排参考。",
        "canonical": canonical_url("/meal-split"),
    }

    return render_template(
        "meal_split.html",
        meta=meta,
        error=error,
        kcal_in=kcal_in,
        protein_in=protein_in,
        pattern_in=pattern_in,
        result=result,
        page_kind="tool",
    )
# 3.1.3. 碳水 (Route)
@app.route("/carbs", methods=["GET", "POST"])
def carbs():
    error = None
    weight_kg_in = ""
    goal_in = "maintain"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        goal_in = request.form.get("goal", "maintain").strip()

        try:
            weight_kg = float(weight_kg_in)
            if goal_in not in ("fat_loss", "maintain", "muscle_gain"):
                raise ValueError("目标选择不正确。")

            result = carbs_need(weight_kg, goal_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "碳水化合物需求计算器（每天大概要吃多少碳水）- CalmyHealth",
        "description": "输入体重并选择目标，估算每天建议摄入多少碳水化合物，适合减脂、维持和增肌饮食参考。",
        "canonical": canonical_url("/carbs"),
    }

    return render_template(
        "carbs.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        goal_in=goal_in,
        result=result,
        page_kind="tool",
    )

# 3.1.4. 脂肪摄入 (Route)
@app.route("/fat-intake", methods=["GET", "POST"])
def fat_intake():
    error = None
    weight_kg_in = ""
    goal_in = "maintain"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        goal_in = request.form.get("goal", "maintain").strip()

        try:
            weight_kg = float(weight_kg_in)
            if goal_in not in ("fat_loss", "maintain", "muscle_gain"):
                raise ValueError("目标选择不正确。")

            result = fat_need(weight_kg, goal_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "脂肪摄入计算器（每天建议吃多少脂肪）- CalmyHealth",
        "description": "输入体重并选择目标，估算每天建议摄入多少脂肪，适合作为减脂、维持和增肌饮食的参考起点。",
        "canonical": canonical_url("/fat-intake"),
    }

    return render_template(
        "fat_intake.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        goal_in=goal_in,
        result=result,
        page_kind="tool",
    )
# 3.1.5. 膳食纤维 (Route)
@app.route("/fiber", methods=["GET", "POST"])
def fiber():
    error = None
    kcal_in = ""
    sex_in = "male"
    result = None

    if request.method == "POST":
        kcal_in = request.form.get("kcal", "").strip()
        sex_in = request.form.get("sex", "male").strip()

        try:
            kcal_val = float(kcal_in)
            result = fiber_need(kcal_val, sex_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "膳食纤维计算器（每天需要多少纤维）- CalmyHealth",
        "description": "输入每日热量和性别，估算每天建议摄入多少膳食纤维，并了解膳食纤维在日常饮食中的作用。",
        "canonical": canonical_url("/fiber"),
    }

    return render_template(
        "fiber.html",
        meta=meta,
        error=error,
        kcal_in=kcal_in,
        sex_in=sex_in,
        result=result,
        page_kind="tool",
    )

# 3.1.6. 盐摄入 (Route)
@app.route("/salt", methods=["GET", "POST"])
def salt():
    error = None
    home_in = "2"
    takeout_in = "1"
    soup_in = "0"
    processed_in = "1"
    snack_in = "0"
    result = None

    if request.method == "POST":
        home_in = request.form.get("home_meals", "2").strip()
        takeout_in = request.form.get("takeout_meals", "1").strip()
        soup_in = request.form.get("soup_bowls", "0").strip()
        processed_in = request.form.get("processed_servings", "1").strip()
        snack_in = request.form.get("snack_servings", "0").strip()

        try:
            result = salt_estimate(
                int(home_in),
                int(takeout_in),
                int(soup_in),
                int(processed_in),
                int(snack_in),
            )
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "盐摄入估算器（你每天吃盐会不会太多）- CalmyHealth",
        "description": "根据家常菜、外卖、汤、加工食品和咸味零食的份数，粗略估算每天盐摄入是否偏高，并给出日常调整建议。",
        "canonical": canonical_url("/salt"),
    }

    return render_template(
        "salt.html",
        meta=meta,
        error=error,
        home_in=home_in,
        takeout_in=takeout_in,
        soup_in=soup_in,
        processed_in=processed_in,
        snack_in=snack_in,
        result=result,
        page_kind="tool",
    )
# -----------------------
# Tool: Steps
# -----------------------
# 4. 运动与习惯
# ========= 4.1. 运动消耗 ======= 
# 4.1.1 步数转热量
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
# 4.1.2 步数转距离 (Route)
@app.route("/steps-distance", methods=["GET", "POST"])
def steps_distance():
    error = None
    steps_in = "10000"
    height_cm_in = ""
    sex_in = "male"
    result = None

    if request.method == "POST":
        steps_in = request.form.get("steps", "10000").strip()
        height_cm_in = request.form.get("height_cm", "").strip()
        sex_in = request.form.get("sex", "male").strip()

        try:
            steps_val = int(steps_in)
            height_val = float(height_cm_in)
            result = steps_to_distance(steps_val, height_val, sex_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "步数转距离计算器（10000步大概是多少公里）- CalmyHealth",
        "description": "输入步数、身高和性别，估算步数大概等于多少米、多少公里，并了解步数与距离的换算逻辑。",
        "canonical": canonical_url("/steps-distance"),
    }

    return render_template(
        "steps_distance.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        height_cm_in=height_cm_in,
        sex_in=sex_in,
        result=result,
        page_kind="tool",
    )
# 4.1.3 步数转步行时间 (Route)
@app.route("/steps-time", methods=["GET", "POST"])
def steps_time():
    error = None
    steps_in = "10000"
    pace_in = "normal"
    result = None

    if request.method == "POST":
        steps_in = request.form.get("steps", "10000").strip()
        pace_in = request.form.get("pace", "normal").strip()

        try:
            steps_val = int(steps_in)
            result = steps_to_time(steps_val, pace_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "步数转步行时间计算器（这些步数大概要走多久）- CalmyHealth",
        "description": "输入步数和步行速度，估算这些步数大概要走多久，帮助你更直观地理解每日步数和活动时间。",
        "canonical": canonical_url("/steps-time"),
    }

    return render_template(
        "steps_time.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        pace_in=pace_in,
        result=result,
        page_kind="tool",
    )
# 4.1.4 每日步数目标
@app.route("/step-goal", methods=["GET", "POST"])
def step_goal():
    error = None
    current_steps_in = "6000"
    goal_in = "maintain"
    result = None

    if request.method == "POST":
        current_steps_in = request.form.get("current_steps", "6000").strip()
        goal_in = request.form.get("goal", "maintain").strip()

        try:
            current_steps_val = int(current_steps_in)
            if goal_in not in ("maintain", "fat_loss", "active_upgrade"):
                raise ValueError("目标选择不正确。")

            result = step_goal_plan(current_steps_val, goal_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "每日步数目标计算器（想减脂或维持体重，每天走多少步更合适）- CalmyHealth",
        "description": "输入你当前日均步数和目标，估算每天更适合的步数目标，并帮助你把活动量目标变得更清晰、更容易执行。",
        "canonical": canonical_url("/step-goal"),
    }

    return render_template(
        "step_goal.html",
        meta=meta,
        error=error,
        current_steps_in=current_steps_in,
        goal_in=goal_in,
        result=result,
        page_kind="tool",
    )
# 4.1.5 活动量等级
@app.route("/activity-level", methods=["GET", "POST"])
def activity_level():
    error = None
    steps_in = "7000"
    exercise_days_in = "2"
    sit_hours_in = "8"
    result = None

    if request.method == "POST":
        steps_in = request.form.get("steps_per_day", "7000").strip()
        exercise_days_in = request.form.get("exercise_days", "2").strip()
        sit_hours_in = request.form.get("sit_hours", "8").strip()

        try:
            result = activity_level_info(
                int(steps_in),
                int(exercise_days_in),
                float(sit_hours_in),
            )
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "活动量等级计算器（你属于久坐、轻度还是中度活动）- CalmyHealth",
        "description": "输入日均步数、每周运动天数和久坐时长，估算你的活动量等级，并帮助理解自己更接近久坐、轻度还是中度活动。",
        "canonical": canonical_url("/activity-level"),
    }

    return render_template(
        "activity_level.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        exercise_days_in=exercise_days_in,
        sit_hours_in=sit_hours_in,
        result=result,
        page_kind="tool",
    )
# 4.1.6 跑步消耗计算器
@app.route("/running-kcal", methods=["GET", "POST"])
def running_kcal():
    error = None
    weight_kg_in = ""
    minutes_in = "30"
    pace_in = "normal"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        minutes_in = request.form.get("minutes", "30").strip()
        pace_in = request.form.get("pace", "normal").strip()

        try:
            weight_val = float(weight_kg_in)
            minutes_val = float(minutes_in)
            result = running_kcal_estimate(weight_val, minutes_val, pace_in)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "跑步消耗计算器（跑步30分钟大概消耗多少热量）- CalmyHealth",
        "description": "输入体重、跑步时间和速度，估算跑步大概消耗多少热量，并帮助理解跑步和日常活动量之间的关系。",
        "canonical": canonical_url("/running-kcal"),
    }

    return render_template(
        "running_kcal.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        minutes_in=minutes_in,
        pace_in=pace_in,
        result=result,
        page_kind="tool",
    )

@app.get("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    print("Starting Flask...")
    app.run(host="0.0.0.0", port=5000, debug=True)