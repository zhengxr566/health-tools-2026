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
    has_request_context,
)
import calendar
import json
from pathlib import Path

from flask import abort

from articles import ARTICLES, ARTICLES_BY_SLUG, AUTHOR as ARTICLE_AUTHOR, HANT_OVERRIDES
from seo_meta import SEO_OVERRIDES
from i18n_hant import ENV_KEY as LANG_ENV_KEY, HANT_PREFIX, HantPrefixMiddleware, convert_html
from i18n_ja import (
    JA_CATEGORIES, JA_META, JA_PAGES, JA_PREFIX, JA_TOOLS, JaPrefixMiddleware, ja_links, ja_msg,
)
from articles_ja import JA_ARTICLES, JA_ARTICLES_BY_SLUG, JA_AUTHOR

app = Flask(__name__)
# 繁体版：/zh-hant/... 共用同一套路由，输出时转繁体（见 i18n_hant.py）
# 日语版：/ja/... 共用路由和计算逻辑，模板单独翻译（见 i18n_ja.py）
app.wsgi_app = JaPrefixMiddleware(HantPrefixMiddleware(app.wsgi_app))
app.jinja_env.filters["ja_msg"] = ja_msg

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
    # 旧的 Render 域名和 Cloud Run 自带的 *.run.app 网址都 301 到正式域名，避免重复内容。
    # 带 X-Calmy-Preview: 1 请求头时不跳转，便于切换 DNS 前在 run.app 上测试（搜索引擎不会带这个头）。
    if host.endswith(".run.app") and request.headers.get("X-Calmy-Preview") == "1":
        return None
    if host in OLD_HOSTS or host.endswith(".run.app") or host == "www.calmyhealth.com":
        qs = f"?{request.query_string.decode()}" if request.query_string else ""
        return redirect(f"{BASE_URL_ENV}{request.script_root}{request.path}{qs}", code=301)


@app.route("/google984348f5d29aa2c5.html")
def google_verify():
    return send_from_directory(".", "google984348f5d29aa2c5.html")


def is_hant() -> bool:
    return has_request_context() and request.environ.get(LANG_ENV_KEY) == "hant"


def is_ja() -> bool:
    return has_request_context() and request.environ.get(LANG_ENV_KEY) == "ja"


def lang_prefix() -> str:
    return HANT_PREFIX if is_hant() else JA_PREFIX if is_ja() else ""


def ja_available(path: str) -> bool:
    """这个路径有没有日语版（日语版只包含已翻译的页面）。"""
    if path in JA_PAGES:
        return True
    if path.startswith("/guide/"):
        return path[len("/guide/"):] in JA_ARTICLES_BY_SLUG
    return False


def canonical_url(path: str) -> str:
    # 各语言版本的 canonical 指向各自的网址（/zh-hant/...、/ja/...）
    prefix = lang_prefix()
    if prefix and path == "/":
        return BASE_URL_ENV.rstrip("/") + prefix + "/"
    return BASE_URL_ENV.rstrip("/") + prefix + path


def lang_urls(path: str) -> dict:
    base = BASE_URL_ENV.rstrip("/")
    return {
        "hans": base + path,
        "hant": base + HANT_PREFIX + (path if path != "/" else "/"),
        "ja": (base + JA_PREFIX + (path if path != "/" else "/")) if ja_available(path) else None,
    }


_flask_render_template = render_template


def render_template(name: str, **context):
    """日语版优先使用 templates/ja/ 下的同名模板。"""
    if is_ja():
        ja_name = f"ja/{name}"
        if (Path(app.root_path) / "templates" / ja_name).exists():
            name = ja_name
    return _flask_render_template(name, **context)


@app.before_request
def ja_only_translated_pages():
    # 没有翻译的页面不提供日语版
    if is_ja() and not ja_available(request.path):
        abort(404)


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
            "diet_quality": {
                "name": "饮食质量",
                "description": "控糖、GI/GL 与饮食结构参考",
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
    # 1.2.4 FFMI 计算
    {
        "endpoint": "ffmi",
        "name": "FFMI 计算器",
        "path": "/ffmi",
        "desc": "去脂体重指数估算",
        "category": "weight",
        "subgroup": "body_shape",
        "featured": True,
    },
    # 1.2.5 体脂目标时间
    {
        "endpoint": "body_fat_goal",
        "name": "体脂目标时间计算器",
        "path": "/body-fat-goal",
        "desc": "估算达到目标体脂率所需时间",
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
    # 2.2.3 维持体重
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
    # 3.1.7 糖摄入
    {
        "endpoint": "sugar_intake",
        "name": "糖摄入计算器",
        "path": "/sugar-intake",
        "desc": "估算每天糖摄入是否偏高",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": True,
    },
    # 3.1.8 咖啡因摄入
    {
        "endpoint": "caffeine_intake",
        "name": "咖啡因摄入计算器",
        "path": "/caffeine-intake",
        "desc": "估算每天咖啡因摄入量",
        "category": "nutrition",
        "subgroup": "daily_intake",
        "featured": True,
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
    # 3.3.1. 餐次分配
    {
        "endpoint": "meal-split",
        "name": "餐次分配计算器",
        "path": "/meal-split",
        "desc": "把每日热量和蛋白质分配到三餐",
        "category": "nutrition",
        "subgroup": "meal_planning",
        "featured": False,
    },
    # ========= 3.4 饮食质量 ======= 
    # 3.4.1. GL估算 
    {
        "endpoint": "glycemic_load",
        "name": "GI/GL 估算器",
        "path": "/glycemic-load",
        "desc": "估算食物血糖负荷参考",
        "category": "nutrition",
        "subgroup": "diet_quality",
        "featured": True,
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
    # 4.1.7 跑步配速
    {
        "endpoint": "running_pace",
        "name": "跑步配速计算器",
        "path": "/running-pace",
        "desc": "计算每公里配速与预计完赛时间",
        "category": "activity",
        "subgroup": "exercise",
        "featured": True,
    },
    # 4.1.8 心率区间
    {
        "endpoint": "heart_rate_zone",
        "name": "心率区间计算器",
        "path": "/heart-rate-zone",
        "desc": "估算运动心率训练区间",
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
    # 4.2.6 起床时间
    {
        "endpoint": "sleep_wake_time",
        "name": "起床时间计算器",
        "path": "/sleep-wake-time",
        "desc": "按90分钟睡眠周期计算更容易自然醒的起床时间",
        "category": "activity",
        "subgroup": "sleep_time",
        "featured": False,
    },
    # 4.2.7 - 入睡时间
    {
        "endpoint": "sleep_bedtime",
        "name": "入睡时间计算器",
        "path": "/sleep-bedtime",
        "desc": "根据起床时间反推最佳入睡时间，减少睡眠中断感",
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
    # 5.1.5 月经周期
    {
        "endpoint": "period_calculator",
        "name": "月经周期计算器",
        "path": "/period-calculator",
        "desc": "预测下次月经与下个周期时间",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": True,
    },
    # 5.1.6 安全期计算
    {
        "endpoint": "safe_days_calculator",
        "name": "安全期计算器",
        "path": "/safe-days-calculator",
        "desc": "按周期估算相对低受孕概率日期",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": False,
    },
    # 5.1.7 易孕期计算
    {
        "endpoint": "fertility_calculator",
        "name": "易孕期计算器",
        "path": "/fertility-calculator",
        "desc": "预测易孕期与较高受孕概率日期",
        "category": "pregnancy",
        "subgroup": "pregnancy_basic",
        "featured": True,
    },
    # 5.1.8 着床时间
    {
        "endpoint": "implantation_calculator",
        "name": "着床时间计算器",
        "path": "/implantation-calculator",
        "desc": "估算受孕后可能的着床时间范围",
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

# -----------------------
# Noindex: 高风险（孕产 / 生殖健康）页面
# 页面仍可访问，但不进搜索结果、不进 sitemap、不放广告。
# 想恢复收录：把分类从 NOINDEX_CATEGORIES 去掉，或把单个 path 加到 INDEX_OVERRIDE_PATHS。
# -----------------------
NOINDEX_CATEGORIES = {"pregnancy"}
INDEX_OVERRIDE_PATHS: set[str] = set()

NOINDEX_PATHS = {
    t["path"]
    for t in TOOLS
    if t.get("category") in NOINDEX_CATEGORIES and t["path"] not in INDEX_OVERRIDE_PATHS
} | {f"/category/{slug}" for slug in NOINDEX_CATEGORIES}


def is_noindex(path: str) -> bool:
    return path.rstrip("/") in NOINDEX_PATHS if path != "/" else False


@app.after_request
def add_noindex_header(resp):
    if is_noindex(request.path):
        resp.headers["X-Robots-Tag"] = "noindex, follow"
    return resp


@app.after_request
def convert_to_hant(resp):
    # 繁体版：把渲染好的 HTML 转成台湾正体，并把站内链接改成 /zh-hant/ 开头
    if is_hant() and resp.mimetype == "text/html" and not resp.direct_passthrough:
        resp.set_data(convert_html(resp.get_data(as_text=True)))
        resp.headers["Content-Language"] = "zh-Hant"
    elif is_ja() and resp.mimetype == "text/html" and not resp.direct_passthrough:
        resp.set_data(ja_links(resp.get_data(as_text=True)))
        resp.headers["Content-Language"] = "ja"
    return resp

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


# -----------------------
# 示意图与分享卡片（由 scripts/make_figures.py 生成，简体 / 繁体各一份）
# -----------------------
STATIC_DIR = Path(app.root_path) / "static"

FIGURES = {
    "body-measurement": {
        "w": 720, "h": 560,
        "alt": "围度测量位置示意图：颈围在喉结下方，腰围在肋骨下缘与髂嵴连线的中点，臀围在臀部最突出处",
        "caption": "颈围、腰围、臀围的测量位置。美国海军体脂公式中，男性腰围改在肚脐水平测量。",
        "ja": {
            "alt": "周囲径の測り方の図：首囲はのどぼとけの下、ウエストは肋骨の下端と腸骨の上端の中間、ヒップはお尻のいちばん出ているところ",
            "caption": "首囲・ウエスト・ヒップの測る位置。メタボ健診の腹囲と米海軍式の男性の腹囲は、おへその高さで測ります。",
        },
    },
    "bmi-chart": {
        "w": 782, "h": 528,
        "alt": "BMI 身高体重对照表：身高 150–190 cm、体重 40–115 kg 对应的 BMI 数值，按中国标准分级着色",
        "caption": "BMI 身高体重对照表（中国成人体重判定标准 WS/T 428-2013）。找到自己的身高行和体重列，交叉格就是 BMI。",
        "hant": {
            "h": 548,
            "alt": "BMI 身高体重对照表：身高 150–190 cm、体重 40–115 kg 对应的 BMI 数值，按台湾国民健康署标准分级着色",
            "caption": "BMI 身高体重对照表（台湾国民健康署成人体位标准）。找到自己的身高行和体重列，交叉格就是 BMI。",
        },
        "ja": {
            "h": 548,
            "alt": "BMI早見表：身長150〜190cm・体重40〜115kgのBMIを、日本肥満学会の基準で色分けした表",
            "caption": "BMI早見表（日本肥満学会の判定基準）。自分の身長の行と体重の列が交わるマスがBMIです。",
        },
    },
    "bodyfat-ranges": {
        "w": 760, "h": 330,
        "alt": "男女体脂率参考范围条形图：必需脂肪、运动员、健身良好、一般水平、偏高（ACE 分级）",
        "caption": "男女体脂率参考范围（美国运动委员会 ACE 分级）。女性的必需脂肪比男性多，参考值整体高 7–10 个百分点。",
        "ja": {
            "alt": "男女別の体脂肪率の目安を示した帯グラフ：必須脂肪、アスリート、引き締まっている、標準、高め（ACEの区分）",
            "caption": "男女別の体脂肪率の目安（米国運動協議会 ACE の区分）。女性は必須脂肪が多いため、全体に男性より7〜10ポイント高めです。",
        },
    },
}

# 哪些页面放了哪些示意图（用于图片 sitemap 和文章 JSON-LD；模板里用 ui.figure(key) 显示）
PAGE_FIGURES = {
    "/bmi": ["bmi-chart"],
    "/waist": ["body-measurement"],
    "/whr": ["body-measurement"],
    "/bodyfat": ["bodyfat-ranges", "body-measurement"],
    "/guide/bmi-normal-range": ["bmi-chart"],
    "/guide/waist-to-height-ratio": ["body-measurement"],
    "/guide/body-fat-percentage-chart": ["bodyfat-ranges", "body-measurement"],
}

# 已生成的分享卡片文件名（例如 bmi.png、bmi.hant.png、bmi.ja.png），按语言分别判断有没有专属卡片
OG_FILES = {p.name for p in (STATIC_DIR / "og").glob("*.png")}


def current_lang() -> str:
    return "hant" if is_hant() else "ja" if is_ja() else "hans"


def lang_suffix(lang: str) -> str:
    return "" if lang == "hans" else f".{lang}"


def fig_src(key: str, absolute: bool = False, lang: str | None = None) -> str:
    lang = lang or current_lang()
    path = f"/static/img/{key}{lang_suffix(lang)}.svg"
    return f"{BASE_URL_ENV}{path}" if absolute else path


def local_figures() -> dict:
    """繁体 / 日语版套用 FIGURES 里的 "hant" / "ja" 覆盖（说明文字、图高等）。"""
    lang = current_lang()
    if lang == "hans":
        return FIGURES
    return {k: {**v, **v.get(lang, {})} for k, v in FIGURES.items()}


def og_image_url(path: str, lang: str | None = None) -> str | None:
    lang = lang or current_lang()
    key = path.rstrip("/").split("/")[-1] or "default"
    name = f"{key}{lang_suffix(lang)}.png"
    if name not in OG_FILES:
        name = f"default{lang_suffix(lang)}.png"
        if name not in OG_FILES:
            return None
    return f"{BASE_URL_ENV}/static/og/{name}"


@app.context_processor
def inject_global_nav():
    return {
        "nav_categories": grouped_tools(),
        "top_tools": top_tools(10),
        "site_name": SITE_NAME,
        "site_name_zh": SITE_NAME_ZH,
        "page_noindex": is_noindex(request.path) and not is_ja(),
        # 语言版本：简体 / 繁体对应网址（用于 hreflang 和语言切换）
        "is_hant": is_hant(),
        "lang_urls": lang_urls(request.path),
        # 搜索标题 / 描述覆盖（见 seo_meta.py）
        "seo_override": (
            (SEO_OVERRIDES.get(request.path) or {}).get("hant") if is_hant() else None
        ) or SEO_OVERRIDES.get(request.path),
        # 工具页底部“相关阅读”：哪些文章把当前页列为相关工具
        "page_articles": (
            [a for a in JA_ARTICLES if request.path in a.get("related_tools", [])] if is_ja() else
            [local_article(a) for a in ARTICLES if request.path in a.get("related_tools", [])]
        ),
        "figures": local_figures(),
        "fig_src": fig_src,
        "og_image": og_image_url(request.path),
        # 日语版
        "is_ja": is_ja(),
        "ja_meta": JA_META.get(request.path) if is_ja() else None,
        "ja_tools": JA_TOOLS,
        "ja_categories": JA_CATEGORIES,
        "ja_articles": JA_ARTICLES,
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


# BMI 分级标准：简体版用中国成人标准，繁体版（台湾/香港读者）用台湾卫福部国健署标准。
# 文字用简体书写，繁体版输出时会自动转换（例如“健康体位”→“健康體位”）。
# kind 用于选择行动建议：low / normal / over / obese
BMI_STANDARDS = {
    "cn": {
        "name": "中国成人体重判定标准（WS/T 428-2013）",
        "source_text": "国家卫生行业标准《成人体重判定》WS/T 428-2013",
        "source_url": "",
        "bands": [
            {"label": "偏瘦", "lo": None, "hi": 18.5, "kind": "low",
             "note": "体重偏低，可结合饮食摄入、力量训练和恢复情况综合观察。"},
            {"label": "正常", "lo": 18.5, "hi": 24.0, "kind": "normal",
             "note": "处于正常范围，建议继续结合腰围、体脂率和生活方式一起评估。"},
            {"label": "超重", "lo": 24.0, "hi": 28.0, "kind": "over",
             "note": "建议关注总热量摄入、活动量、睡眠，以及腰围变化。"},
            {"label": "肥胖", "lo": 28.0, "hi": None, "kind": "obese",
             "note": "建议结合饮食、运动和专业评估进行体重管理，不宜只看单一数字。"},
        ],
    },
    "tw": {
        "name": "台湾成人体位标准（卫生福利部国民健康署）",
        "source_text": "卫生福利部国民健康署：成人肥胖定义",
        "source_url": "https://www.hpa.gov.tw/",
        "bands": [
            {"label": "体重过轻", "lo": None, "hi": 18.5, "kind": "low",
             "note": "体重偏低，可结合饮食摄入、力量训练和恢复情况综合观察。"},
            {"label": "健康体位", "lo": 18.5, "hi": 24.0, "kind": "normal",
             "note": "处于健康范围，建议继续结合腰围、体脂率和生活方式一起评估。"},
            {"label": "过重", "lo": 24.0, "hi": 27.0, "kind": "over",
             "note": "建议关注总热量摄入、活动量、睡眠，以及腰围变化。"},
            {"label": "轻度肥胖", "lo": 27.0, "hi": 30.0, "kind": "obese",
             "note": "建议开始有计划地控制体重，并留意血压、血糖、血脂等指标。"},
            {"label": "中度肥胖", "lo": 30.0, "hi": 35.0, "kind": "obese",
             "note": "建议在医师或营养师协助下制定体重管理计划。"},
            {"label": "重度肥胖", "lo": 35.0, "hi": None, "kind": "obese",
             "note": "建议尽早就医评估，由专业人员协助制定体重管理方案。"},
        ],
    },
    # 日语版：日本肥满学会（JASSO）的判定基准，文字直接用日语
    "jp": {
        "name": "日本肥満学会の判定基準（肥満症診療ガイドライン2022）",
        "source_text": "日本肥満学会『肥満症診療ガイドライン2022』",
        "source_url": "https://www.jasso.or.jp/",
        "bands": [
            {"label": "低体重（やせ）", "lo": None, "hi": 18.5, "kind": "low",
             "note": "やせ気味です。食事量やたんぱく質が足りているか見直しましょう。"},
            {"label": "普通体重", "lo": 18.5, "hi": 25.0, "kind": "normal",
             "note": "普通体重の範囲です。腹囲や体脂肪率もあわせて確認しましょう。"},
            {"label": "肥満（1度）", "lo": 25.0, "hi": 30.0, "kind": "obese",
             "note": "食事と活動量を見直し、腹囲や健診の数値も確認しましょう。"},
            {"label": "肥満（2度）", "lo": 30.0, "hi": 35.0, "kind": "obese",
             "note": "計画的な減量がすすめられます。健診結果もあわせて確認しましょう。"},
            {"label": "肥満（3度）", "lo": 35.0, "hi": 40.0, "kind": "obese",
             "note": "高度肥満にあたります。医療機関での相談をおすすめします。"},
            {"label": "肥満（4度）", "lo": 40.0, "hi": None, "kind": "obese",
             "note": "高度肥満にあたります。医療機関での相談をおすすめします。"},
        ],
    },
}


def bmi_standard() -> dict:
    return BMI_STANDARDS["tw" if is_hant() else "jp" if is_ja() else "cn"]


def bmi_band(bmi: float, std: dict | None = None) -> dict:
    std = std or bmi_standard()
    for b in std["bands"]:
        if (b["lo"] is None or bmi >= b["lo"]) and (b["hi"] is None or bmi < b["hi"]):
            return b
    return std["bands"][-1]


def bmi_category_cn(bmi: float) -> str:
    if bmi < 18.5:
        return "偏瘦"
    if bmi < 24.0:
        return "正常"
    if bmi < 28.0:
        return "偏胖"
    return "肥胖"


def bmr_nibiohn(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    """国立健康・栄养研究所の式（Ganpule AA, et al. Eur J Clin Nutr, 2007），日本人向け。kcal/天。"""
    const = 0.4235 if sex == "male" else 0.9708
    return (0.0481 * weight_kg + 0.0234 * height_cm - 0.0138 * age - const) * 1000 / 4.186


def bmi_progress(bmi: float) -> int:
    p = (bmi - 15.0) / (35.0 - 15.0) * 100.0
    return int(round(clamp(p, 0, 100)))


# -----------------------
# 结果色带（工具页“你在这里”可视化，和 static/img 里的示意图共用一套颜色）
# -----------------------
BAND_COLORS = {
    "low": ("#93c5fd", "#1f2937"),
    "normal": ("#86efac", "#1f2937"),
    "over": ("#fde68a", "#1f2937"),
    "obese": [("#fca5a5", "#1f2937"), ("#f87171", "#1f2937"), ("#dc2626", "#ffffff"), ("#991b1b", "#ffffff")],
}


def band_color(std: dict, idx: int) -> tuple[str, str]:
    """返回 (填充色, 文字色)。多个肥胖分级时颜色逐级加深。"""
    kind = std["bands"][idx]["kind"]
    if kind != "obese":
        return BAND_COLORS[kind]
    obese_idx = [i for i, b in enumerate(std["bands"]) if b["kind"] == "obese"]
    shades = BAND_COLORS["obese"]
    n = obese_idx.index(idx)
    if len(obese_idx) == 1:
        return shades[1]
    return shades[min(n, len(shades) - 1)]


def make_gauge(bands: list[dict], value: float, vmin: float, vmax: float,
               decimals: int = 1, unit: str = "") -> dict:
    """把分级区间转换成色带数据。bands 每项含 label / lo / hi / color（lo、hi 可为 None）。"""
    span = vmax - vmin

    def pct(v: float) -> float:
        return round(clamp((v - vmin) / span * 100.0, 0.0, 100.0), 2)

    segs, ticks = [], []
    for b in bands:
        lo = vmin if b["lo"] is None else b["lo"]
        hi = vmax if b["hi"] is None else b["hi"]
        if hi <= vmin or lo >= vmax:
            continue
        x0, x1 = pct(lo), pct(hi)
        cur = (b["lo"] is None or value >= b["lo"]) and (b["hi"] is None or value < b["hi"])
        segs.append({"x": x0, "w": round(x1 - x0, 2), "mid": round((x0 + x1) / 2, 2),
                     "label": b["label"], "color": b["color"], "current": cur})
        if b["lo"] is not None and vmin < b["lo"] < vmax:
            ticks.append({"x": x0, "text": f"{b['lo']:g}{unit}"})
    return {"segments": segs, "ticks": ticks, "marker": pct(value),
            "value_text": f"{value:.{decimals}f}{unit}"}


def bmi_gauge(bmi: float, std: dict) -> dict:
    bands = [{**b, "color": band_color(std, i)[0]} for i, b in enumerate(std["bands"])]
    return make_gauge(bands, bmi, 14.0, 40.0)


# 体脂率分级：美国运动委员会（ACE），与 scripts/make_figures.py 的示意图一致
BODYFAT_BANDS = {
    "male": [("必需脂肪", None, 6), ("运动员", 6, 14), ("健身良好", 14, 18), ("一般水平", 18, 25), ("偏高", 25, None)],
    "female": [("必需脂肪", None, 14), ("运动员", 14, 21), ("健身良好", 21, 25), ("一般水平", 25, 32), ("偏高", 32, None)],
}
BODYFAT_COLORS = ["#cbd5e1", "#93c5fd", "#86efac", "#fde68a", "#fca5a5"]

# 腰围身高比：0.4–0.5 为常用健康区间（Ashwell 等），≥0.6 风险明显升高
WHTR_BANDS = [
    {"label": "偏低", "lo": None, "hi": 0.4, "color": "#93c5fd"},
    {"label": "较好", "lo": 0.4, "hi": 0.5, "color": "#86efac"},
    {"label": "需要注意", "lo": 0.5, "hi": 0.6, "color": "#fde68a"},
    {"label": "风险较高", "lo": 0.6, "hi": None, "color": "#f87171"},
]

# 腰臀比：WHO 2008（男 ≥0.90、女 ≥0.85 风险明显升高），与 whr_info 的分级一致
WHR_BANDS = {
    "male": [
        {"label": "较低风险", "lo": None, "hi": 0.85, "color": "#86efac"},
        {"label": "需要注意", "lo": 0.85, "hi": 0.90, "color": "#fde68a"},
        {"label": "风险较高", "lo": 0.90, "hi": None, "color": "#f87171"},
    ],
    "female": [
        {"label": "较低风险", "lo": None, "hi": 0.80, "color": "#86efac"},
        {"label": "需要注意", "lo": 0.80, "hi": 0.85, "color": "#fde68a"},
        {"label": "风险较高", "lo": 0.85, "hi": None, "color": "#f87171"},
    ],
}


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
    if whtr < 0.4:
        level = "偏低（体重可能偏轻）"
    elif whtr < 0.5:
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

    Reference (WHO Expert Consultation on Waist Circumference and
    Waist-Hip Ratio, 2008: substantially increased risk at
    men >= 0.90, women >= 0.85):
    male:
        < 0.85   -> 较低风险
        < 0.90   -> 需要注意
        >= 0.90  -> 风险较高

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
    ratio_rounded = f"{ratio:.2f}"  # 固定两位小数显示，如 0.80

    if sex == "male":
        if ratio < 0.85:
            level = "较低风险"
            progress = 38
        elif ratio < 0.90:
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
        ref_text = "男性参考（WHO）：WHR < 0.85 通常更理想，0.85–0.89 需要注意，≥ 0.90 代谢风险明显升高。"
    else:
        ref_text = "女性参考（WHO）：WHR < 0.80 通常更理想，0.80–0.84 需要注意，≥ 0.85 代谢风险明显升高。"

    return {
        "ratio": ratio_rounded,
        "level": level,
        "progress": progress,
        "ref_text": ref_text,
        "waist_cm": round1(waist_cm),
        "hip_cm": round1(hip_cm),
    }
# 1.2.4 FFMI 计算
def ffmi_info(height_cm: float, weight_kg: float, bodyfat_pct: float, sex: str) -> dict:
    """
    FFMI (Fat-Free Mass Index)

    lean_mass = weight * (1 - bodyfat%)
    ffmi = lean_mass / height_m^2

    Normalized FFMI (common site formula):
    ffmi_norm = ffmi + 6.1 * (1.8 - height_m)

    This is an educational estimator only.
    """

    if height_cm <= 0 or height_cm > 250:
        raise ValueError("请输入合理的身高（cm）。")
    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")
    if bodyfat_pct <= 0 or bodyfat_pct >= 70:
        raise ValueError("请输入合理的体脂率（%）。")
    if sex not in ("male", "female"):
        raise ValueError("性别选择不正确。")

    height_m = height_cm / 100.0
    bodyfat_ratio = bodyfat_pct / 100.0

    lean_mass = weight_kg * (1.0 - bodyfat_ratio)
    fat_mass = weight_kg - lean_mass

    ffmi = lean_mass / (height_m * height_m)
    ffmi_normalized = ffmi + 6.1 * (1.8 - height_m)

    # Simple interpretation bands
    if sex == "male":
        if ffmi_normalized < 18:
            level = "偏低"
            note = "通常更接近偏瘦或肌肉量相对较少的状态。"
            progress = 35
        elif ffmi_normalized < 21:
            level = "常见范围"
            note = "通常属于较常见的自然体型范围。"
            progress = 58
        elif ffmi_normalized < 23:
            level = "较高"
            note = "通常说明去脂体重较高，肌肉量基础较好。"
            progress = 76
        else:
            level = "很高"
            note = "通常已经属于较高的去脂体重水平，更建议结合训练背景、体脂率和长期变化一起看。"
            progress = 88
    else:
        if ffmi_normalized < 14:
            level = "偏低"
            note = "通常更接近偏瘦或肌肉量相对较少的状态。"
            progress = 35
        elif ffmi_normalized < 17:
            level = "常见范围"
            note = "通常属于较常见的自然体型范围。"
            progress = 58
        elif ffmi_normalized < 19:
            level = "较高"
            note = "通常说明去脂体重较高，肌肉量基础较好。"
            progress = 76
        else:
            level = "很高"
            note = "通常已经属于较高的去脂体重水平，更建议结合训练背景、体脂率和长期变化一起看。"
            progress = 88

    return {
        "height_m": round(height_m, 2),
        "lean_mass": round1(lean_mass),
        "fat_mass": round1(fat_mass),
        "ffmi": round1(ffmi),
        "ffmi_normalized": round1(ffmi_normalized),
        "level": level,
        "note": note,
        "progress": progress,
    }

# 1.2.5 体脂目标时间
def body_fat_goal_info(
    weight_kg: float,
    bodyfat_pct: float,
    target_bodyfat_pct: float,
    daily_deficit_kcal: float
) -> dict:
    """
    Estimate time needed to reach target body fat %.

    Simplified logic:
    - current lean mass = weight * (1 - bodyfat%)
    - assume lean mass roughly maintained
    - target weight = lean mass / (1 - target_bodyfat%)
    - fat to lose = current weight - target weight
    - kcal needed ≈ fat_to_lose * 7700
    - days = total_kcal / daily_deficit

    Educational estimate only.
    """

    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理的体重（kg）。")
    if bodyfat_pct <= 0 or bodyfat_pct >= 70:
        raise ValueError("请输入合理的当前体脂率（%）。")
    if target_bodyfat_pct <= 0 or target_bodyfat_pct >= 60:
        raise ValueError("请输入合理的目标体脂率（%）。")
    if target_bodyfat_pct >= bodyfat_pct:
        raise ValueError("目标体脂率需要低于当前体脂率。")
    if daily_deficit_kcal <= 0 or daily_deficit_kcal > 2000:
        raise ValueError("请输入合理的每日热量缺口（kcal/天）。")

    current_bf_ratio = bodyfat_pct / 100.0
    target_bf_ratio = target_bodyfat_pct / 100.0

    lean_mass = weight_kg * (1.0 - current_bf_ratio)
    current_fat_mass = weight_kg - lean_mass

    target_weight = lean_mass / (1.0 - target_bf_ratio)
    target_fat_mass = target_weight - lean_mass

    fat_to_lose = weight_kg - target_weight
    fat_mass_to_lose = current_fat_mass - target_fat_mass

    total_kcal_needed = fat_mass_to_lose * 7700.0
    days_needed = total_kcal_needed / daily_deficit_kcal
    weeks_needed = days_needed / 7.0
    months_needed = days_needed / 30.4

    # pacing / interpretation
    weekly_loss_kg = daily_deficit_kcal * 7.0 / 7700.0

    if daily_deficit_kcal < 300:
        pace_label = "较温和"
        pace_note = "缺口相对温和，通常更容易长期坚持，但达到目标会更慢。"
        progress = 38
    elif daily_deficit_kcal <= 600:
        pace_label = "常见减脂节奏"
        pace_note = "属于很多人较常采用的减脂节奏，通常在速度与可持续性之间更平衡。"
        progress = 62
    else:
        pace_label = "较激进"
        pace_note = "热量缺口较大，速度更快，但更建议关注饥饿感、恢复状态和蛋白质摄入。"
        progress = 82

    return {
        "lean_mass": round1(lean_mass),
        "current_fat_mass": round1(current_fat_mass),
        "target_weight": round1(target_weight),
        "target_fat_mass": round1(target_fat_mass),
        "fat_to_lose": round1(fat_to_lose),
        "fat_mass_to_lose": round1(fat_mass_to_lose),
        "days_needed": round1(days_needed),
        "weeks_needed": round1(weeks_needed),
        "months_needed": round1(months_needed),
        "weekly_loss_kg": round1(weekly_loss_kg),
        "pace_label": pace_label,
        "pace_note": pace_note,
        "progress": progress,
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

    if goal == "dri":
        # 日本人の食事摂取基準的目标量中间值附近：P15% / F25% / C60%（日语版使用）
        p_ratio, c_ratio, f_ratio = 0.15, 0.60, 0.25
        label = "膳食参考均衡型"
    elif goal == "fat_loss":
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
# 3.3.1. 餐次分配
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
# 3.4.1. GL估算 
def glycemic_load_info(gi: float, carbs_g: float, fiber_g: float = 0.0) -> dict:
    """
    Glycemic Load calculator.

    Formula:
    available_carbs = max(0, total_carbs - fiber)
    GL = GI * available_carbs / 100

    Educational estimate only.
    """

    if gi <= 0 or gi > 150:
        raise ValueError("请输入合理的 GI 数值。")
    if carbs_g < 0 or carbs_g > 500:
        raise ValueError("请输入合理的碳水化合物（g）。")
    if fiber_g < 0 or fiber_g > 100:
        raise ValueError("请输入合理的膳食纤维（g）。")
    if fiber_g > carbs_g:
        raise ValueError("膳食纤维不能大于总碳水。")

    available_carbs = max(0.0, carbs_g - fiber_g)
    gl = gi * available_carbs / 100.0

    if gi <= 55:
        gi_level = "低 GI"
    elif gi < 70:
        gi_level = "中 GI"
    else:
        gi_level = "高 GI"

    if gl <= 10:
        gl_level = "低 GL"
        note = "这份食物的血糖负荷相对较低，通常更接近小份量或可利用碳水较少的情况。"
        progress = 32
    elif gl < 20:
        gl_level = "中 GL"
        note = "这份食物的血糖负荷处于中等范围，是否适合还要结合总饮食结构和食用场景一起看。"
        progress = 58
    else:
        gl_level = "高 GL"
        note = "这份食物的血糖负荷相对较高，通常意味着 GI 较高、可利用碳水较多，或两者同时存在。"
        progress = 86

    return {
        "gi": round1(gi),
        "gi_level": gi_level,
        "carbs_g": round1(carbs_g),
        "fiber_g": round1(fiber_g),
        "available_carbs_g": round1(available_carbs),
        "gl": round1(gl),
        "gl_level": gl_level,
        "note": note,
        "progress": progress,
        "rule_text": "本工具采用简化公式：GL = GI × 可利用碳水 ÷ 100，其中可利用碳水≈总碳水 - 膳食纤维。",
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
# 3.1.7 糖摄入
def sugar_intake_estimate(
    sugary_drinks: int,
    desserts: int,
    sweet_snacks: int,
    sweet_sauces: int,
    sweet_coffee_tea: int,
) -> dict:
    """
    Very simplified daily sugar estimator.

    Estimated sugar per serving (g):
    - sugary drink: 25 g
    - dessert: 18 g
    - sweet snack: 12 g
    - sweet sauce / syrup use: 8 g
    - sweetened coffee / tea: 10 g

    Educational estimate only.
    """

    vals = [sugary_drinks, desserts, sweet_snacks, sweet_sauces, sweet_coffee_tea]
    if any(v < 0 or v > 20 for v in vals):
        raise ValueError("请输入合理的份数。")

    total_sugar_g = (
        sugary_drinks * 25
        + desserts * 18
        + sweet_snacks * 12
        + sweet_sauces * 8
        + sweet_coffee_tea * 10
    )

    total_sugar_g = round1(total_sugar_g)
    total_sugar_kcal = round0(total_sugar_g * 4)

    if total_sugar_g <= 25:
        level = "较低"
        note = "整体糖摄入大致偏低或较克制。"
        progress = 35
    elif total_sugar_g <= 50:
        level = "需要注意"
        note = "已经进入很多人日常容易不知不觉偏高的区间。"
        progress = 65
    else:
        level = "偏高"
        note = "糖摄入相对偏高，更建议留意饮料、甜点和零食来源。"
        progress = 88

    return {
        "total_sugar_g": total_sugar_g,
        "total_sugar_kcal": total_sugar_kcal,
        "level": level,
        "note": note,
        "progress": progress,
        "rule_text": "本工具采用站内简化估算模型，根据常见含糖饮料、甜点、零食和调味场景粗略估算每日糖摄入。",
    }
# 3.1.8 咖啡因摄入
def caffeine_intake_estimate(
    brewed_coffee: int,
    espresso_shots: int,
    tea_cups: int,
    energy_drinks: int,
    cola_cans: int,
) -> dict:
    """
    Simplified caffeine intake estimator.

    Estimated caffeine per serving (mg):
    - brewed coffee: 95 mg / cup
    - espresso shot: 63 mg / shot
    - tea: 40 mg / cup
    - energy drink: 80 mg / can
    - cola: 35 mg / can

    Educational estimate only.
    """

    vals = [brewed_coffee, espresso_shots, tea_cups, energy_drinks, cola_cans]
    if any(v < 0 or v > 20 for v in vals):
        raise ValueError("请输入合理的份数。")

    total_mg = (
        brewed_coffee * 95
        + espresso_shots * 63
        + tea_cups * 40
        + energy_drinks * 80
        + cola_cans * 35
    )

    if total_mg <= 100:
        level = "较低"
        note = "整体咖啡因摄入相对较低，对多数人来说通常较温和。"
        progress = 25
    elif total_mg <= 200:
        level = "常见范围"
        note = "属于很多人日常比较常见的咖啡因摄入水平。"
        progress = 48
    elif total_mg <= 400:
        level = "偏高但常见"
        note = "已经进入较高摄入区间，更值得关注摄入时间、睡眠和个体敏感度。"
        progress = 72
    else:
        level = "较高"
        note = "整体咖啡因摄入较高，更建议留意心悸、焦虑、入睡困难和晚间睡眠质量。"
        progress = 90

    return {
        "total_mg": int(round(total_mg)),
        "level": level,
        "note": note,
        "progress": progress,
        "rule_text": "本工具采用站内简化估算模型，根据常见咖啡、浓缩咖啡、茶、能量饮料和可乐的平均咖啡因含量粗略估算每日摄入。",
    }
# ========== 4.1. 运动消耗 ==========
# 4.1.1 步数转热量
STEP_WALK_MET = 3.5   # 正常步速（约 4.8 km/h）步行，Compendium of Physical Activities
STEP_CADENCE = 100    # 正常步频，步/分钟


def steps_to_kcal(steps: int, weight_kg: float) -> float:
    """
    MET 法估算步行总消耗：kcal = MET × 体重(kg) × 时间(h)
    时间按正常步频 100 步/分钟换算；60 kg 走 10000 步 ≈ 350 kcal。
    """
    hours = steps / STEP_CADENCE / 60.0
    return STEP_WALK_MET * weight_kg * hours
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
    - fast:   130 steps/min
    """

    if steps <= 0 or steps > 200000:
        raise ValueError("请输入合理的步数。")

    if pace == "slow":
        spm = 80
        label = "较慢步速"
    elif pace == "fast":
        spm = 130
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
# 4.1.7 跑步配速
def running_pace_info(distance_km: float, hours: int, minutes: int, seconds: int) -> dict:
    """
    Running pace calculator.

    Inputs:
    - distance_km
    - total time: hours, minutes, seconds

    Outputs:
    - pace per km
    - speed km/h
    - estimated finish times for 3k / 5k / 10k / half / marathon
    """

    if distance_km <= 0 or distance_km > 1000:
        raise ValueError("请输入合理的跑步距离（km）。")
    if hours < 0 or hours > 23:
        raise ValueError("请输入合理的小时数。")
    if minutes < 0 or minutes > 59:
        raise ValueError("请输入合理的分钟数。")
    if seconds < 0 or seconds > 59:
        raise ValueError("请输入合理的秒数。")

    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError("总时间需要大于 0。")

    pace_sec_per_km = total_seconds / distance_km
    speed_kmh = distance_km / (total_seconds / 3600.0)

    def fmt_hms(sec: float) -> str:
        sec = int(round(sec))
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        if h > 0:
            return f"{h:d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def fmt_pace(sec_per_km: float) -> str:
        sec_per_km = int(round(sec_per_km))
        m = sec_per_km // 60
        s = sec_per_km % 60
        return f"{m:d}'{s:02d}\" /km"

    # common target distances
    projections = {
        "3k": fmt_hms(pace_sec_per_km * 3),
        "5k": fmt_hms(pace_sec_per_km * 5),
        "10k": fmt_hms(pace_sec_per_km * 10),
        "half_marathon": fmt_hms(pace_sec_per_km * 21.0975),
        "marathon": fmt_hms(pace_sec_per_km * 42.195),
    }

    if speed_kmh < 7:
        level = "偏慢配速"
        note = "更接近轻松慢跑或恢复跑的常见范围。"
        progress = 35
    elif speed_kmh < 10:
        level = "常见配速"
        note = "属于很多日常跑步者比较常见的配速区间。"
        progress = 58
    elif speed_kmh < 13:
        level = "较快配速"
        note = "通常已经属于较积极训练或节奏跑常见范围。"
        progress = 78
    else:
        level = "高配速"
        note = "通常说明速度较快，更建议结合训练经验和目标距离一起判断。"
        progress = 90

    return {
        "total_time_text": fmt_hms(total_seconds),
        "pace_text": fmt_pace(pace_sec_per_km),
        "pace_sec_per_km": round(pace_sec_per_km, 1),
        "speed_kmh": round1(speed_kmh),
        "level": level,
        "note": note,
        "progress": progress,
        "projections": projections,
    }
# 4.1.8 心率区间
def heart_rate_zone_info(age: int, resting_hr: int | None = None) -> dict:
    """
    Heart rate zone calculator.

    Base method:
    - max_hr = 220 - age

    Optional Karvonen method if resting_hr is provided:
    - heart rate reserve (HRR) = max_hr - resting_hr
    - target = resting_hr + HRR * intensity

    Zones:
    Z1: 50-60%
    Z2: 60-70%
    Z3: 70-80%
    Z4: 80-90%
    Z5: 90-100%
    """

    if age <= 0 or age > 120:
        raise ValueError("请输入合理年龄。")

    if resting_hr is not None and (resting_hr <= 0 or resting_hr > 120):
        raise ValueError("请输入合理的静息心率（bpm）。")

    max_hr = 220 - age

    zones = [
        ("Zone 1", "恢复 / 热身", 0.50, 0.60),
        ("Zone 2", "轻松有氧", 0.60, 0.70),
        ("Zone 3", "中等强度", 0.70, 0.80),
        ("Zone 4", "阈值 / 较高强度", 0.80, 0.90),
        ("Zone 5", "高强度冲刺", 0.90, 1.00),
    ]

    result_zones = []

    if resting_hr is None:
        # Simple method
        for code, label, lo, hi in zones:
            low_bpm = round0(max_hr * lo)
            high_bpm = round0(max_hr * hi)
            result_zones.append({
                "code": code,
                "label": label,
                "low_bpm": low_bpm,
                "high_bpm": high_bpm,
            })
        method_label = "最大心率百分比法"
        note = "当前结果按“220 - 年龄”估算最大心率，再按百分比划分区间，适合作为一般参考。"
    else:
        # Karvonen
        hrr = max_hr - resting_hr
        for code, label, lo, hi in zones:
            low_bpm = round0(resting_hr + hrr * lo)
            high_bpm = round0(resting_hr + hrr * hi)
            result_zones.append({
                "code": code,
                "label": label,
                "low_bpm": low_bpm,
                "high_bpm": high_bpm,
            })
        method_label = "Karvonen 储备心率法"
        note = "当前结果已考虑静息心率，通常比单纯最大心率百分比法更贴近个体差异。"

    if age < 30:
        progress = 75
    elif age < 50:
        progress = 60
    else:
        progress = 48

    return {
        "max_hr": max_hr,
        "resting_hr": resting_hr,
        "method_label": method_label,
        "note": note,
        "zones": result_zones,
        "progress": progress,
    }

# 4.2.6 起床时间

# 4.2.7 入睡时间

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
# 5.1.4 受孕日期
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

# 5.1.1
from datetime import datetime, timedelta, date
import calendar

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def format_week_label(days_from_lmp):
    weeks = days_from_lmp // 7
    extra_days = days_from_lmp % 7
    return f"{weeks}周+{extra_days}天"

def estimate_due_date(lmp_date):
    return lmp_date + timedelta(days=280)

def build_pregnancy_calendar(lmp_date, due_date):
    today = date.today()

    months = []
    current_year = lmp_date.year
    current_month = lmp_date.month

    while (current_year, current_month) <= (due_date.year, due_date.month):
        _, month_days = calendar.monthrange(current_year, current_month)
        days_map = {}

        for day in range(1, month_days + 1):
            current_date = date(current_year, current_month, day)

            if lmp_date <= current_date <= due_date:
                days_from_lmp = (current_date - lmp_date).days
                days_map[day] = {
                    "week_num": days_from_lmp // 7,
                    "is_today": current_date == today,
                    "is_due_date": current_date == due_date,
                }

        months.append({
            "label": f"{current_year}-{current_month:02d}",
            "month_num": current_month,
            "days_map": days_map,
        })

        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1

    return {"months": months}

def estimate_conception_date(lmp_date):
    return lmp_date + timedelta(days=14)

# 5.1.5 月经周期
def period_cycle_info(lmp_date: date, cycle_length: int, period_length: int) -> dict:
    """
    Period calculator.

    Inputs:
    - lmp_date: last menstrual period start date
    - cycle_length: average cycle length in days
    - period_length: average period length in days

    Outputs:
    - current cycle day
    - next period start/end
    - estimated ovulation
    - fertile window
    """

    today = date.today()

    if lmp_date > today:
        raise ValueError("末次月经开始日期不能晚于今天。")
    if cycle_length < 21 or cycle_length > 45:
        raise ValueError("请输入合理的月经周期长度（通常 21–45 天）。")
    if period_length < 1 or period_length > 15:
        raise ValueError("请输入合理的经期时长（通常 1–15 天）。")

    days_since_lmp = (today - lmp_date).days
    current_cycle_day = (days_since_lmp % cycle_length) + 1

    next_period_start = lmp_date
    while next_period_start <= today:
        next_period_start += timedelta(days=cycle_length)

    next_period_end = next_period_start + timedelta(days=period_length - 1)

    estimated_ovulation = next_period_start - timedelta(days=14)
    fertile_start = estimated_ovulation - timedelta(days=5)
    fertile_end = estimated_ovulation + timedelta(days=1)

    current_period_end = lmp_date + timedelta(days=period_length - 1)

    if today <= current_period_end:
        phase = "经期中"
        progress = 18
    elif current_cycle_day < cycle_length * 0.4:
        phase = "卵泡期"
        progress = 40
    elif abs((estimated_ovulation - today).days) <= 1:
        phase = "排卵期附近"
        progress = 68
    elif today < next_period_start:
        phase = "黄体期"
        progress = 82
    else:
        phase = "新周期临近"
        progress = 92

    return {
        "today": today.strftime("%Y-%m-%d"),
        "current_cycle_day": current_cycle_day,
        "phase": phase,
        "progress": progress,
        "current_period_end": current_period_end.strftime("%Y-%m-%d"),
        "next_period_start": next_period_start.strftime("%Y-%m-%d"),
        "next_period_end": next_period_end.strftime("%Y-%m-%d"),
        "estimated_ovulation": estimated_ovulation.strftime("%Y-%m-%d"),
        "fertile_start": fertile_start.strftime("%Y-%m-%d"),
        "fertile_end": fertile_end.strftime("%Y-%m-%d"),
        "cycle_length": cycle_length,
        "period_length": period_length,
    }
# 5.1.6 安全期计算
def safe_days_info(lmp_date: date, cycle_length: int, period_length: int) -> dict:
    """
    Safe days calculator (educational estimate only).

    Assumptions:
    - Ovulation ~ 14 days before next period
    - Fertile window = ovulation - 5 days to ovulation + 1 day
    - "Safer" days are dates outside the fertile window within the current cycle

    This is NOT a contraceptive method and should only be used as a rough cycle reference.
    """

    today = date.today()

    if lmp_date > today:
        raise ValueError("末次月经开始日期不能晚于今天。")
    if cycle_length < 21 or cycle_length > 45:
        raise ValueError("请输入合理的月经周期长度（通常 21–45 天）。")
    if period_length < 1 or period_length > 15:
        raise ValueError("请输入合理的经期时长（通常 1–15 天）。")

    cycle_start = lmp_date
    while cycle_start + timedelta(days=cycle_length) <= today:
        cycle_start += timedelta(days=cycle_length)

    cycle_end = cycle_start + timedelta(days=cycle_length - 1)

    estimated_ovulation = cycle_start + timedelta(days=(cycle_length - 14))
    fertile_start = estimated_ovulation - timedelta(days=5)
    fertile_end = estimated_ovulation + timedelta(days=1)

    period_end = cycle_start + timedelta(days=period_length - 1)

    safe_early_start = cycle_start
    safe_early_end = fertile_start - timedelta(days=1)

    safe_late_start = fertile_end + timedelta(days=1)
    safe_late_end = cycle_end

    current_cycle_day = (today - cycle_start).days + 1

    def fmt(d: date) -> str:
        return d.strftime("%Y-%m-%d")

    # current status
    if fertile_start <= today <= fertile_end:
        current_status = "当前接近易孕期"
        progress = 80
    elif cycle_start <= today <= period_end:
        current_status = "当前在经期内"
        progress = 20
    elif today < fertile_start:
        current_status = "当前在周期前段"
        progress = 40
    else:
        current_status = "当前在周期后段"
        progress = 60

    def valid_range(start_d: date, end_d: date):
        if start_d > end_d:
            return None
        return {
            "start": fmt(start_d),
            "end": fmt(end_d),
        }

    return {
        "today": fmt(today),
        "cycle_start": fmt(cycle_start),
        "cycle_end": fmt(cycle_end),
        "current_cycle_day": current_cycle_day,
        "current_status": current_status,
        "progress": progress,
        "period_end": fmt(period_end),
        "estimated_ovulation": fmt(estimated_ovulation),
        "fertile_start": fmt(fertile_start),
        "fertile_end": fmt(fertile_end),
        "safe_early": valid_range(safe_early_start, safe_early_end),
        "safe_late": valid_range(safe_late_start, safe_late_end),
        "cycle_length": cycle_length,
        "period_length": period_length,
    }
# 5.1.7 易孕期计算
def fertility_window_info(lmp_date: date, cycle_length: int) -> dict:
    """
    Fertility calculator.

    Inputs:
    - lmp_date: last menstrual period start date
    - cycle_length: average cycle length in days

    Logic:
    - ovulation ≈ next period - 14 days
    - fertile window ≈ ovulation - 5 days to ovulation + 1 day
    - highlight peak fertility days around ovulation

    Educational estimate only.
    """

    today = date.today()

    if lmp_date > today:
        raise ValueError("末次月经开始日期不能晚于今天。")
    if cycle_length < 21 or cycle_length > 45:
        raise ValueError("请输入合理的月经周期长度（通常 21–45 天）。")

    cycle_start = lmp_date
    while cycle_start + timedelta(days=cycle_length) <= today:
        cycle_start += timedelta(days=cycle_length)

    cycle_end = cycle_start + timedelta(days=cycle_length - 1)
    next_period_start = cycle_start + timedelta(days=cycle_length)

    ovulation_day = next_period_start - timedelta(days=14)
    fertile_start = ovulation_day - timedelta(days=5)
    fertile_end = ovulation_day + timedelta(days=1)

    # Peak fertility estimation: ovulation day and previous 2 days
    peak_start = ovulation_day - timedelta(days=2)
    peak_end = ovulation_day

    current_cycle_day = (today - cycle_start).days + 1

    if fertile_start <= today <= fertile_end:
        status = "当前接近易孕期"
        progress = 82
    elif today < fertile_start:
        status = "当前尚未进入易孕期"
        progress = 40
    else:
        status = "当前已过本周期主要易孕期"
        progress = 65

    return {
        "today": today.strftime("%Y-%m-%d"),
        "cycle_start": cycle_start.strftime("%Y-%m-%d"),
        "cycle_end": cycle_end.strftime("%Y-%m-%d"),
        "next_period_start": next_period_start.strftime("%Y-%m-%d"),
        "current_cycle_day": current_cycle_day,
        "status": status,
        "progress": progress,
        "ovulation_day": ovulation_day.strftime("%Y-%m-%d"),
        "fertile_start": fertile_start.strftime("%Y-%m-%d"),
        "fertile_end": fertile_end.strftime("%Y-%m-%d"),
        "peak_start": peak_start.strftime("%Y-%m-%d"),
        "peak_end": peak_end.strftime("%Y-%m-%d"),
        "cycle_length": cycle_length,
    }
# 5.1.8 着床时间
def implantation_info(lmp_date: date | None = None, ovulation_date: date | None = None) -> dict:
    """
    Estimate implantation window.

    Logic:
    - If ovulation/conception-related date is known, implantation often occurs about
      6 to 10 days after ovulation/fertilization.
    - If only LMP is provided, estimate ovulation as LMP + (cycle approx 28 => +14 days),
      then estimate implantation window from there.

    This is an educational estimate only.
    """

    today = date.today()

    if ovulation_date is None and lmp_date is None:
        raise ValueError("请至少提供排卵日或末次月经开始日期。")

    if ovulation_date is not None and ovulation_date > today:
        raise ValueError("排卵日不能晚于今天。")

    if lmp_date is not None and lmp_date > today:
        raise ValueError("末次月经开始日期不能晚于今天。")

    source_label = ""
    if ovulation_date is not None:
        base_date = ovulation_date
        source_label = "按排卵日估算"
    else:
        base_date = lmp_date + timedelta(days=14)
        source_label = "按末次月经开始日期估算（默认约第14天排卵）"

    implantation_start = base_date + timedelta(days=6)
    implantation_peak = base_date + timedelta(days=8)
    implantation_end = base_date + timedelta(days=10)

    days_from_base_to_today = (today - base_date).days

    if today < implantation_start:
        status = "当前通常还早于常见着床时间范围"
        progress = 30
    elif implantation_start <= today <= implantation_end:
        status = "当前接近常见着床时间范围"
        progress = 72
    else:
        status = "当前通常已过常见着床时间范围"
        progress = 90

    return {
        "source_label": source_label,
        "base_date": base_date.strftime("%Y-%m-%d"),
        "implantation_start": implantation_start.strftime("%Y-%m-%d"),
        "implantation_peak": implantation_peak.strftime("%Y-%m-%d"),
        "implantation_end": implantation_end.strftime("%Y-%m-%d"),
        "days_from_base_to_today": days_from_base_to_today,
        "status": status,
        "progress": progress,
    }
# ========= 5.2. 孕期健康 ======= 
# 5.2.1 孕期体重增长
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
# 5.2.4 胎儿发育周数
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
# 5.2.2 孕期热量需求
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
# 5.2.3 孕期蛋白质
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
# 5.2.5 孕期饮水量
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


ADSENSE_PUB_ID = "pub-8372619640631658"


@app.get("/ads.txt")
def ads_txt():
    # 授权数字卖方声明：只允许 Google AdSense 以本站发布商 ID 销售广告位
    line = f"google.com, {ADSENSE_PUB_ID}, DIRECT, f08c47fec0942fa0"
    return Response(line + "\n", mimetype="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    core_paths = ["/", "/tools", "/guide", "/about", "/privacy", "/contact"]
    category_paths = [f"/category/{slug}" for slug in CATEGORY_META.keys()]
    tool_paths = [t["path"] for t in TOOLS]
    article_paths = [f"/guide/{a['slug']}" for a in ARTICLES]
    all_paths = [
        p for p in core_paths + category_paths + tool_paths + article_paths
        if not is_noindex(p)
    ]

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # 每个页面列出简体和繁体两个网址，并互相标注 hreflang
    xml[1] = ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
              'xmlns:xhtml="http://www.w3.org/1999/xhtml" '
              'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">')
    for path in all_paths:
        urls = lang_urls(path)
        alternates = [
            f'    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{urls["hans"]}"/>',
            f'    <xhtml:link rel="alternate" hreflang="zh-Hant" href="{urls["hant"]}"/>',
        ]
        if urls["ja"]:
            alternates.append(f'    <xhtml:link rel="alternate" hreflang="ja" href="{urls["ja"]}"/>')
        alternates.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{urls["hans"]}"/>')
        versions = [(urls["hans"], "hans"), (urls["hant"], "hant")]
        if urls["ja"]:
            versions.append((urls["ja"], "ja"))
        for loc, lang in versions:
            xml.append("  <url>")
            xml.append(f"    <loc>{loc}</loc>")
            xml.extend(alternates)
            for key in PAGE_FIGURES.get(path, []):
                xml.append(f"    <image:image><image:loc>{fig_src(key, absolute=True, lang=lang)}</image:loc></image:image>")
            xml.append("  </url>")

    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


# -----------------------
# 健康指南（文章）
# -----------------------
def _jsonld(data) -> str:
    # 防止正文里出现 </script> 截断标签
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def local_article(a: dict) -> dict:
    """繁体版时套用 HANT_OVERRIDES（按台湾标准改写的标题、描述、目录、FAQ 和补充来源）。"""
    if not is_hant():
        return a
    ov = HANT_OVERRIDES.get(a["slug"])
    if not ov:
        return a
    merged = {**a, **{k: v for k, v in ov.items() if k != "extra_sources"}}
    merged["sources"] = list(a.get("sources", [])) + list(ov.get("extra_sources", []))
    return merged


def article_jsonld(a: dict) -> str:
    url = canonical_url(f"/guide/{a['slug']}")
    graph = [
        {
            "@type": "Article",
            "headline": a["h1"],
            "description": a["description"],
            "image": [u for u in [og_image_url(f"/guide/{a['slug']}")] if u] + [
                fig_src(k, absolute=True) for k in PAGE_FIGURES.get(f"/guide/{a['slug']}", [])
            ],
            "datePublished": a["published"],
            "dateModified": a["updated"],
            "inLanguage": "zh-CN",
            "mainEntityOfPage": url,
            "author": {
                "@type": "Person",
                "name": ARTICLE_AUTHOR["name"],
                "url": canonical_url(ARTICLE_AUTHOR["url"]),
            },
            "publisher": {
                "@type": "Organization",
                "name": SITE_NAME,
                "url": canonical_url("/"),
            },
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "首页", "item": canonical_url("/")},
                {"@type": "ListItem", "position": 2, "name": "健康指南", "item": canonical_url("/guide")},
                {"@type": "ListItem", "position": 3, "name": a["h1"], "item": url},
            ],
        },
    ]
    if a.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": ans}}
                for q, ans in a["faq"]
            ],
        })
    return _jsonld({"@context": "https://schema.org", "@graph": graph})


@app.get("/guide")
def guide_index():
    if is_ja():
        meta = meta_for(JA_META["/guide"][0], JA_META["/guide"][1], "/guide")
        return render_template("guide_index.html", meta=meta, articles=JA_ARTICLES)
    meta = meta_for(
        f"健康指南：体重、热量、营养、运动与睡眠常见问题 - {SITE_NAME}",
        "CalmyHealth 健康指南：用研究和公式讲清楚 BMI、体脂、热量缺口、蛋白质、饮水、步数、跑步、心率和睡眠等常见问题，每篇附参考来源和可直接计算的工具。",
        "/guide",
    )
    order = ["体重与体型", "代谢与热量", "营养摄入", "运动与步数", "睡眠"]
    names = order + sorted({a["category"] for a in ARTICLES} - set(order))
    groups = [
        {"name": n, "articles": [local_article(a) for a in ARTICLES if a["category"] == n]}
        for n in names
    ]
    groups = [g for g in groups if g["articles"]]
    return render_template("guide_index.html", meta=meta, groups=groups)


@app.get("/guide/<slug>")
def guide_article(slug: str):
    if is_ja():
        return guide_article_ja(slug)
    a = ARTICLES_BY_SLUG.get(slug)
    if a is None:
        abort(404)
    a = local_article(a)

    tools_by_path = {t["path"]: t for t in TOOLS}
    related_tools = [
        {"path": p, "name": tools_by_path[p]["name"], "desc": tools_by_path[p].get("desc", "")}
        for p in a.get("related_tools", []) if p in tools_by_path
    ]
    related_articles = [
        local_article(ARTICLES_BY_SLUG[s]) for s in a.get("related_articles", []) if s in ARTICLES_BY_SLUG
    ]

    meta = meta_for(f"{a['title']} - {SITE_NAME}", a["description"], f"/guide/{slug}")
    meta["og_type"] = "article"

    return render_template(
        f"guide/{slug}.html",
        meta=meta,
        article=a,
        author=ARTICLE_AUTHOR,
        article_jsonld=article_jsonld(a),
        related_tools=related_tools,
        related_articles=related_articles,
    )



def guide_article_ja(slug: str):
    a = JA_ARTICLES_BY_SLUG.get(slug)
    if a is None:
        abort(404)
    url = canonical_url(f"/guide/{slug}")
    tools_by_path = {t["path"]: t for t in JA_TOOLS}
    related_tools = [
        {"path": p, "name": tools_by_path[p]["name"], "desc": tools_by_path[p]["desc"]}
        for p in a.get("related_tools", []) if p in tools_by_path
    ]
    related_articles = [JA_ARTICLES_BY_SLUG[s] for s in a.get("related_articles", []) if s in JA_ARTICLES_BY_SLUG]
    graph = [
        {
            "@type": "Article",
            "headline": a["h1"],
            "description": a["description"],
            "image": [u for u in [og_image_url(f"/guide/{slug}")] if u] + [
                fig_src(k, absolute=True) for k in PAGE_FIGURES.get(f"/guide/{slug}", [])
            ],
            "datePublished": a["published"],
            "dateModified": a["updated"],
            "inLanguage": "ja",
            "mainEntityOfPage": url,
            "author": {"@type": "Person", "name": JA_AUTHOR["name"], "url": canonical_url(JA_AUTHOR["url"])},
            "publisher": {"@type": "Organization", "name": SITE_NAME, "url": canonical_url("/")},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "ホーム", "item": canonical_url("/")},
                {"@type": "ListItem", "position": 2, "name": "健康ガイド", "item": canonical_url("/guide")},
                {"@type": "ListItem", "position": 3, "name": a["h1"], "item": url},
            ],
        },
    ]
    if a.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
                for q, ans in a["faq"]
            ],
        })
    meta = meta_for(f"{a['title']} - {SITE_NAME}", a["description"], f"/guide/{slug}")
    meta["og_type"] = "article"
    return render_template(
        f"guide/{slug}.html",
        meta=meta,
        article=a,
        author=JA_AUTHOR,
        article_jsonld=_jsonld({"@context": "https://schema.org", "@graph": graph}),
        related_tools=related_tools,
        related_articles=related_articles,
    )


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
from datetime import datetime, timedelta

def parse_hm_to_datetime(hm):
    return datetime.strptime(hm, "%H:%M")

def calc_sleep_duration(bed_hm, wake_hm):
    bed_dt = parse_hm_to_datetime(bed_hm)
    wake_dt = parse_hm_to_datetime(wake_hm)

    if wake_dt <= bed_dt:
        wake_dt += timedelta(days=1)

    diff = wake_dt - bed_dt
    total_minutes = int(diff.total_seconds() // 60)

    hours = total_minutes // 60
    minutes = total_minutes % 60
    duration_hours = round(total_minutes / 60, 2)

    if duration_hours < 6:
        level = "偏短"
    elif duration_hours <= 9:
        level = "常见范围"
    else:
        level = "偏长"

    return {
        "bed_hm": bed_hm,
        "wake_hm": wake_hm,
        "hours": hours,
        "minutes": minutes,
        "duration_hours": duration_hours,
        "level": level,
    }

def format_duration_from_hours(hours):
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 0:
        return f"{h}小时"
    return f"{h}小时{m}分钟"

def build_duration_rows_from_bedtime(bed_hm):
    bed_dt = parse_hm_to_datetime(bed_hm)

    rows = []
    for hours in [6, 6.5, 7, 7.5, 8, 8.5, 9]:
        wake_dt = bed_dt + timedelta(hours=hours)
        rows.append({
            "wake_hm": wake_dt.strftime("%H:%M"),
            "duration_text": format_duration_from_hours(hours),
            "is_recommended": hours in [7.5, 8, 8.5],
        })

    return rows

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
    # 首页
    meta = meta_for(
        "CalmyHealth｜健康计算器与减脂工具导航",
        "CalmyHealth 提供 BMI、TDEE、BMR、体脂率、步数距离、跑步配速、睡眠等在线计算器和健康指南文章，适合日常健康管理和减脂参考。",
        "/",
    )
    return render_template(
        "index.html",
        meta=meta,
        categories=grouped_tools(),
        featured_tools=featured_tools,
        guide_articles=[
            local_article(ARTICLES_BY_SLUG[s]) for s in (
                "bmi-normal-range", "bmr-vs-tdee", "protein-intake-per-day",
                "10000-steps-km", "running-pace-chart", "sleep-cycle-90-minutes",
            ) if s in ARTICLES_BY_SLUG
        ],
        tools=TOOLS,
        page_kind="home",
    )

@app.get("/tools")
def tools():
# /tools
    meta = meta_for(
        "健康工具导航｜BMI、TDEE、步数、睡眠计算器 - CalmyHealth",
        "按分类浏览 CalmyHealth 健康工具，包括体重体型、代谢热量、营养摄入、运动习惯、睡眠和孕期相关计算器。",
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
        [t for t in TOOLS if not is_noindex(t["path"])],
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
        "关于 CalmyHealth：独立运营的免费健身与生活方式计算器网站，说明编辑方针、各工具使用的公式与参考来源及免责声明。",
        "/about",
    )
    return render_template("about.html", meta=meta)


@app.get("/privacy")
def privacy():
    meta = meta_for(
        f"隐私政策 - {SITE_NAME}",
        "CalmyHealth 隐私政策：无需注册，计算输入不保存；说明服务器日志、访问统计、Google 广告 Cookie 及如何关闭个性化广告。",
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

    contact_email = "hello@calmyhealth.com"  # 这里换成你的邮箱

    return render_template(
        "contact.html",
        meta=meta,
        contact_email=contact_email
    )
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
    gauge = None
    band_kind = None
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
            band = bmi_band(bmi_raw)
            category = band["label"]
            band_kind = band["kind"]
            progress = bmi_progress(bmi_raw)
            std = bmi_standard()
            gauge = bmi_gauge(bmi_raw, std)

            normal = next(b for b in std["bands"] if b["kind"] == "normal")
            ideal_min = round1(normal["lo"] * hm * hm)
            ideal_max = round1((normal["hi"] - 0.1) * hm * hm)

            if w < ideal_min:
                to_min = round1(ideal_min - w)
            elif w > ideal_max:
                to_max = round1(w - ideal_max)

            if band_kind == "low":
                suggestions = [
                    "优先保证规律三餐与足够蛋白质摄入。",
                    "每周进行 2–3 次力量训练，提升肌肉量与体能。",
                    "关注睡眠质量与压力水平，避免长期熬夜。",
                ]
            elif band_kind == "normal":
                suggestions = [
                    "保持当前体重趋势，重点关注腰围与体脂率。",
                    "每周累计 150 分钟中等强度运动更容易长期维持。",
                    "饮食上优先选择高纤维、足够蛋白质与稳定作息。",
                ]
            elif band_kind == "over":
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
        "BMI 计算器｜身高体重指数计算 - CalmyHealth",
        "BMI 计算器：输入身高和体重，快速计算 BMI 数值、健康体重范围和体型分类，并查看相关健康建议。",
        "/bmi",
    )

    return render_template(
        "bmi.html",
        meta=meta,
        error=error,
        bmi=bmi_val,
        category=category,
        progress=progress,
        gauge=gauge,
        band_kind=band_kind,
        ideal_min=ideal_min,
        ideal_max=ideal_max,
        to_min=to_min,
        to_max=to_max,
        suggestion_title=suggestion_title,
        suggestions=suggestions,
        risk_note=risk_note,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
        bmi_std=bmi_standard(),
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

    # /deficit
    meta = meta_for(
        "热量缺口计算器｜减脂目标热量计算 - CalmyHealth",
        "热量缺口怎么计算？输入TDEE并选择目标，估算减脂、维持或增肌所需每日热量，适合体重管理参考。",
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
# 2.2.3 维持体重
def maintenance_calories_info(
    sex: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_factor: float
) -> dict:
    """
    Maintenance calories are essentially TDEE.
    This helper also provides simple planning targets:
    - mild cut
    - moderate cut
    - mild gain
    """

    if sex not in ("male", "female"):
        raise ValueError("性别选择不正确。")
    if age <= 0 or age > 120:
        raise ValueError("请输入合理年龄。")
    if height_cm <= 0 or height_cm > 250:
        raise ValueError("请输入合理身高（cm）。")
    if weight_kg <= 0 or weight_kg > 300:
        raise ValueError("请输入合理体重（kg）。")
    if activity_factor < 1.1 or activity_factor > 2.5:
        raise ValueError("活动水平选择不正确。")

    bmr = mifflin_st_jeor(sex, age, height_cm, weight_kg)
    maintenance_kcal = round0(bmr * activity_factor)

    mild_cut = max(1200, maintenance_kcal - 300)
    moderate_cut = max(1200, maintenance_kcal - 500)
    mild_gain = maintenance_kcal + 250

    if activity_factor < 1.3:
        activity_label = "久坐 / 很轻活动"
        progress = 35
    elif activity_factor < 1.5:
        activity_label = "轻度活动"
        progress = 50
    elif activity_factor < 1.7:
        activity_label = "中度活动"
        progress = 68
    elif activity_factor < 1.9:
        activity_label = "较高活动"
        progress = 82
    else:
        activity_label = "高活动量"
        progress = 92

    return {
        "bmr": round0(bmr),
        "maintenance_kcal": maintenance_kcal,
        "mild_cut": mild_cut,
        "moderate_cut": moderate_cut,
        "mild_gain": mild_gain,
        "activity_label": activity_label,
        "progress": progress,
    }
# -----------------------
# Tool: pregnancy
# -----------------------
# 5. 孕期工具
# ========= 5.1. 基础孕期 ======= 
## 5.1.1 预产期计算
@app.route("/pregnancy-due-date", methods=["GET", "POST"])
def pregnancy_due_date():
    error = None
    lmp_in = ""

    due_date = None
    days_to_due = None
    current_week = None
    pregnancy_calendar = None

    # 示例数据
    demo_due_date = None
    demo_days_to_due = None
    demo_current_week = None
    demo_pregnancy_calendar = None

    meta = {
        "title": "预产期计算器（孕周表格版）- CalmyHealth",
        "description": "输入末次月经第一天，计算预计预产期、距离预产期天数、当前孕周，并查看完整显示到预产期的孕周表格。",
        "canonical": canonical_url("/pregnancy-due-date"),
    }

    # -----------------------
    # 先准备未计算时的示例数据
    # 示例逻辑：假设今天大约在孕 12 周
    # -----------------------
    try:
        today = date.today()
        demo_lmp_date = today - timedelta(days=12 * 7 + 3)  # 示例：12周+3天
        demo_due_date_obj = estimate_due_date(demo_lmp_date)

        demo_due_date = demo_due_date_obj.strftime("%Y-%m-%d")
        demo_days_to_due = (demo_due_date_obj - today).days
        demo_current_week = format_week_label((today - demo_lmp_date).days)
        demo_pregnancy_calendar = build_pregnancy_calendar(demo_lmp_date, demo_due_date_obj)
    except Exception:
        demo_due_date = None
        demo_days_to_due = None
        demo_current_week = None
        demo_pregnancy_calendar = None

    # -----------------------
    # 用户提交后计算真实结果
    # -----------------------
    if request.method == "POST":
        lmp_in = (request.form.get("lmp") or "").strip()

        try:
            if not lmp_in:
                raise ValueError("请输入末次月经第一天。")

            lmp_date = parse_date(lmp_in)
            today = date.today()

            if lmp_date > today:
                raise ValueError("末次月经第一天不能晚于今天。")

            due_date_obj = estimate_due_date(lmp_date)

            due_date = due_date_obj.strftime("%Y-%m-%d")
            days_to_due = (due_date_obj - today).days

            pregnancy_days = (today - lmp_date).days
            current_week = format_week_label(pregnancy_days)

            pregnancy_calendar = build_pregnancy_calendar(lmp_date, due_date_obj)

        except ValueError as e:
            error = str(e)
        except Exception:
            error = "日期格式错误，请重新输入。"

    return render_template(
        "pregnancy_due_date.html",
        meta=meta,
        error=error,
        lmp_in=lmp_in,
        due_date=due_date,
        days_to_due=days_to_due,
        current_week=current_week,
        pregnancy_calendar=pregnancy_calendar,
        demo_due_date=demo_due_date,
        demo_days_to_due=demo_days_to_due,
        demo_current_week=demo_current_week,
        demo_pregnancy_calendar=demo_pregnancy_calendar,
        page_kind="tool",
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

    # /pregnancy-week
    meta = {
        "title": "怀孕周数计算器｜孕周与预产期计算 - CalmyHealth",
        "description": "输入末次月经日期，计算当前怀孕周数、孕期阶段、预产期和孕期进度，适合孕期时间参考。",
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
# 5.1.5 月经周期
@app.route("/period-calculator", methods=["GET", "POST"])
def period_calculator():
    error = None
    result = None

    lmp_in = ""
    cycle_in = "28"
    period_in = "5"

    if request.method == "POST":
        lmp_in = request.form.get("lmp", "").strip()
        cycle_in = request.form.get("cycle_length", "28").strip()
        period_in = request.form.get("period_length", "5").strip()

        try:
            if not lmp_in:
                raise ValueError("请输入末次月经开始日期。")

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()
            cycle_length = int(cycle_in)
            period_length = int(period_in)

            result = period_cycle_info(lmp_date, cycle_length, period_length)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "月经周期计算器｜下次月经与排卵期预测 - CalmyHealth",
        "description": "输入末次月经开始日期、周期长度和经期时长，预测下次月经、排卵日和易孕期范围。",
        "canonical": canonical_url("/period-calculator"),
    }
    return render_template(
        "period_calculator.html",
        meta=meta,
        error=error,
        result=result,
        lmp_in=lmp_in,
        cycle_in=cycle_in,
        period_in=period_in,
        page_kind="tool",
    )
# 5.1.6 安全期计算
@app.route("/safe-days-calculator", methods=["GET", "POST"])
def safe_days_calculator():
    error = None
    result = None

    lmp_in = ""
    cycle_in = "28"
    period_in = "5"

    if request.method == "POST":
        lmp_in = request.form.get("lmp", "").strip()
        cycle_in = request.form.get("cycle_length", "28").strip()
        period_in = request.form.get("period_length", "5").strip()

        try:
            if not lmp_in:
                raise ValueError("请输入末次月经开始日期。")

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()
            cycle_length = int(cycle_in)
            period_length = int(period_in)

            result = safe_days_info(lmp_date, cycle_length, period_length)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "安全期计算器（月经周期参考）- CalmyHealth",
        "description": "输入末次月经开始日期、平均周期长度和经期时长，估算周期中的相对低受孕概率日期、排卵日和易孕期范围，仅供周期参考。",
        "canonical": canonical_url("/safe-days-calculator"),
    }

    return render_template(
        "safe_days_calculator.html",
        meta=meta,
        error=error,
        result=result,
        lmp_in=lmp_in,
        cycle_in=cycle_in,
        period_in=period_in,
        page_kind="tool",
    )
# 5.1.7 易孕期计算
@app.route("/fertility-calculator", methods=["GET", "POST"])
def fertility_calculator():
    error = None
    result = None

    lmp_in = ""
    cycle_in = "28"

    if request.method == "POST":
        lmp_in = request.form.get("lmp", "").strip()
        cycle_in = request.form.get("cycle_length", "28").strip()

        try:
            if not lmp_in:
                raise ValueError("请输入末次月经开始日期。")

            lmp_date = datetime.strptime(lmp_in, "%Y-%m-%d").date()
            cycle_length = int(cycle_in)

            result = fertility_window_info(lmp_date, cycle_length)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "易孕期计算器（Fertility Calculator）- CalmyHealth",
        "description": "输入末次月经开始日期和平均周期长度，预测排卵日、易孕期范围和相对更高受孕概率的日期窗口。",
        "canonical": canonical_url("/fertility-calculator"),
    }

    return render_template(
        "fertility_calculator.html",
        meta=meta,
        error=error,
        result=result,
        lmp_in=lmp_in,
        cycle_in=cycle_in,
        page_kind="tool",
    )
# 5.1.8 着床时间
@app.route("/implantation-calculator", methods=["GET", "POST"])
def implantation_calculator():
    error = None
    result = None

    mode_in = "lmp"
    lmp_in = ""
    ovulation_in = ""

    if request.method == "POST":
        mode_in = request.form.get("mode", "lmp").strip()
        lmp_in = request.form.get("lmp", "").strip()
        ovulation_in = request.form.get("ovulation_date", "").strip()

        try:
            if mode_in == "ovulation":
                if not ovulation_in:
                    raise ValueError("请输入排卵日。")
                result = implantation_info(ovulation_date=parse_date(ovulation_in))
            else:
                mode_in = "lmp"
                if not lmp_in:
                    raise ValueError("请输入末次月经开始日期。")
                result = implantation_info(lmp_date=parse_date(lmp_in))
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "着床时间计算器 - CalmyHealth",
        "description": "输入排卵日或末次月经开始日期，估算常见的着床时间范围（排卵后约 6–10 天），仅供参考。",
        "canonical": canonical_url("/implantation-calculator"),
    }

    return render_template(
        "implantation_calculator.html",
        meta=meta,
        error=error,
        result=result,
        mode_in=mode_in,
        lmp_in=lmp_in,
        ovulation_in=ovulation_in,
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
    bmr_jp = None
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
            bmr_jp = round0(bmr_nibiohn(sex_in, age, h, w))

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
        bmr_jp=bmr_jp,
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
        "每日热量需求计算器｜TDEE 计算器 - CalmyHealth",
        "TDEE 计算器：输入性别、年龄、身高、体重和活动水平，估算每日热量需求，适合减脂、维持体重和增肌参考。",
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
# 2.2.3 维持体重
@app.route("/maintenance-calories", methods=["GET", "POST"])
def maintenance_calories():
    error = None
    result = None

    sex_in = "male"
    age_in = ""
    height_cm_in = ""
    weight_kg_in = ""
    activity_in = "1.375"

    if request.method == "POST":
        sex_in = request.form.get("sex", "male").strip()
        age_in = request.form.get("age", "").strip()
        height_cm_in = request.form.get("height_cm", "").strip()
        weight_kg_in = request.form.get("weight_kg", "").strip()
        activity_in = request.form.get("activity", "1.375").strip()

        try:
            age = int(age_in)
            height_cm = float(height_cm_in)
            weight_kg = float(weight_kg_in)
            activity_factor = float(activity_in)

            result = maintenance_calories_info(
                sex_in,
                age,
                height_cm,
                weight_kg,
                activity_factor,
            )

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "维持体重热量计算器（Maintenance Calories）- CalmyHealth",
        "description": "输入性别、年龄、身高、体重和活动水平，估算维持当前体重所需热量，并查看轻度减脂、常见减脂和温和增肌的热量参考。",
        "canonical": canonical_url("/maintenance-calories"),
    }

    return render_template(
        "maintenance_calories.html",
        meta=meta,
        error=error,
        result=result,
        sex_in=sex_in,
        age_in=age_in,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
        activity_in=activity_in,
        page_kind="tool",
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
        "title": "睡眠债计算器｜这一周你欠了多少睡眠 - CalmyHealth",
        "description": "如果每天少睡1小时，一周就会累计约7小时睡眠债。输入你的睡眠时长，快速估算睡眠债，并了解需要多久恢复。",
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
    result = None
    duration_rows = None

    bed_hour_in = "23"
    bed_minute_in = "30"
    wake_hour_in = "07"
    wake_minute_in = "00"

    if request.method == "POST":
        bed_hour_in = request.form.get("bed_hour", "23").strip()
        bed_minute_in = request.form.get("bed_minute", "30").strip()
        wake_hour_in = request.form.get("wake_hour", "07").strip()
        wake_minute_in = request.form.get("wake_minute", "00").strip()

        bed_hm = f"{bed_hour_in}:{bed_minute_in}"
        wake_hm = f"{wake_hour_in}:{wake_minute_in}"

        try:
            result = calc_sleep_duration(bed_hm, wake_hm)
            duration_rows = build_duration_rows_from_bedtime(bed_hm)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效时间。"
    else:
        bed_hm = f"{bed_hour_in}:{bed_minute_in}"
        duration_rows = build_duration_rows_from_bedtime(bed_hm)

    meta = {
        "title": "从几点睡到几点起一共睡了多久？睡眠时长计算器 - CalmyHealth",
        "description": "23:30到07:00大约是7小时30分钟。选择入睡时间和起床时间，快速计算睡眠时长，并查看不同起床时间对应的睡眠时长表。",
        "canonical": canonical_url("/sleep-duration"),
    }

    return render_template(
        "sleep_duration.html",
        meta=meta,
        error=error,
        result=result,
        duration_rows=duration_rows,
        bed_hm_for_table=f"{bed_hour_in}:{bed_minute_in}",
        bed_hour_in=bed_hour_in,
        bed_minute_in=bed_minute_in,
        wake_hour_in=wake_hour_in,
        wake_minute_in=wake_minute_in,
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
# 4.2.6 起床时间
@app.route("/sleep-wake-time", methods=["GET", "POST"])
def sleep_wake_time():
    error = None
    hour_in = "23"
    minute_in = "00"
    sleep_rows = []
    recommended_time = None
    recommended_cycles = None

    if request.method == "POST":
        hour_in = request.form.get("hour", "23")
        minute_in = request.form.get("minute", "00")

        try:
            hour = int(hour_in)
            minute = int(minute_in)

            base = datetime(2000, 1, 1, hour, minute) + timedelta(minutes=15)

            for cycles in [3, 4, 5, 6]:
                t = base + timedelta(minutes=90 * cycles)
                is_recommended = cycles == 5

                row = {
                    "cycles": cycles,
                    "duration_text": f"{cycles * 1.5:g} 小时",
                    "time": t.strftime("%H:%M"),
                    "is_recommended": is_recommended,
                }
                sleep_rows.append(row)

                if is_recommended:
                    recommended_time = row["time"]
                    recommended_cycles = cycles

        except Exception:
            error = "请输入有效时间。"

    meta = {
        "title": "起床时间计算器（按睡眠周期推荐几点醒）- CalmyHealth",
        "description": "选择准备入睡的时间，按90分钟睡眠周期和入睡缓冲，计算更适合醒来的起床时间。",
        "canonical": canonical_url("/sleep-wake-time"),
    }

    return render_template(
        "sleep_wake_time.html",
        meta=meta,
        error=error,
        hour_in=hour_in,
        minute_in=minute_in,
        sleep_rows=sleep_rows,
        recommended_time=recommended_time,
        recommended_cycles=recommended_cycles,
        page_kind="tool",
    )

# 4.2.7 入睡时间
@app.route("/sleep-bedtime", methods=["GET", "POST"])
def sleep_bedtime():
    error = None
    hour_in = "07"
    minute_in = "00"
    sleep_rows = []
    recommended_time = None
    recommended_cycles = None

    if request.method == "POST":
        hour_in = request.form.get("hour", "07")
        minute_in = request.form.get("minute", "00")

        try:
            hour = int(hour_in)
            minute = int(minute_in)

            base = datetime(2000, 1, 1, hour, minute)

            for cycles in [3, 4, 5, 6]:
                t = base - timedelta(minutes=(90 * cycles + 15))
                is_recommended = cycles == 5

                row = {
                    "cycles": cycles,
                    "duration_text": f"{cycles * 1.5:g} 小时",
                    "time": t.strftime("%H:%M"),
                    "is_recommended": is_recommended,
                }
                sleep_rows.append(row)

                if is_recommended:
                    recommended_time = row["time"]
                    recommended_cycles = cycles

        except Exception:
            error = "请输入有效时间。"

    meta = {
        "title": "入睡时间计算器（按起床时间反推几点睡）- CalmyHealth",
        "description": "选择目标起床时间，按90分钟睡眠周期和入睡缓冲，反推更适合准备睡觉的时间。",
        "canonical": canonical_url("/sleep-bedtime"),
    }

    return render_template(
        "sleep_bedtime.html",
        meta=meta,
        error=error,
        hour_in=hour_in,
        minute_in=minute_in,
        sleep_rows=sleep_rows,
        recommended_time=recommended_time,
        recommended_cycles=recommended_cycles,
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
    gauge = None
    bf_category = None
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
            bf_bands = [{"label": n, "lo": lo, "hi": hi, "color": BODYFAT_COLORS[i]}
                        for i, (n, lo, hi) in enumerate(BODYFAT_BANDS[sex_in])]
            gauge = make_gauge(bf_bands, bf, 0.0, 45.0, unit="%")
            bf_category = next(g["label"] for g in gauge["segments"] if g["current"]) if any(
                g["current"] for g in gauge["segments"]) else bf_bands[-1]["label"]
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
        gauge=gauge,
        bf_category=bf_category,
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
# 1.2.2 腰围风险
@app.route("/waist", methods=["GET", "POST"])
def waist():
    error = None
    wc_in = ""
    height_cm_in = ""
    whtr = None
    level = None
    gauge = None
    waist_limit = None

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
            whtr_raw, level = waist_risk(wc, h)
            whtr = f"{whtr_raw:.2f}"
            gauge = make_gauge(WHTR_BANDS, whtr_raw, 0.3, 0.8, decimals=2)
            # 腰围低于身高一半（WHtR < 0.5）对应的腰围上限
            waist_limit = round1(h * 0.5)

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
        gauge=gauge,
        waist_limit=waist_limit,
    )

# 1.2.3. 腰臀比
@app.route("/whr", methods=["GET", "POST"])
def whr():
    error = None
    sex_in = "male"
    waist_cm_in = ""
    hip_cm_in = ""
    result = None

    if request.method == "POST":
        sex_in = request.form.get("sex", "male").strip()
        waist_cm_in = request.form.get("waist_cm", "").strip()
        hip_cm_in = request.form.get("hip_cm", "").strip()

        try:
            waist_cm = float(waist_cm_in)
            hip_cm = float(hip_cm_in)
            result = whr_info(waist_cm, hip_cm, sex_in)
            result["gauge"] = make_gauge(WHR_BANDS[sex_in], waist_cm / hip_cm, 0.65, 1.1, decimals=2)
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "腰臀比计算器（WHR）- CalmyHealth",
        "description": "输入腰围、臀围和性别，计算腰臀比（WHR），查看常见参考范围，并帮助理解腰部脂肪分布风险。",
        "canonical": canonical_url("/whr"),
    }

    return render_template(
        "whr.html",
        meta=meta,
        error=error,
        sex_in=sex_in,
        waist_cm_in=waist_cm_in,
        hip_cm_in=hip_cm_in,
        result=result,
        page_kind="tool",
    )
# 1.2.4 FFMI 计算
@app.route("/ffmi", methods=["GET", "POST"])
def ffmi():
    error = None
    sex_in = "male"
    height_cm_in = ""
    weight_kg_in = ""
    bodyfat_pct_in = ""
    result = None

    if request.method == "POST":
        sex_in = request.form.get("sex", "male").strip()
        height_cm_in = request.form.get("height_cm", "").strip()
        weight_kg_in = request.form.get("weight_kg", "").strip()
        bodyfat_pct_in = request.form.get("bodyfat_pct", "").strip()

        try:
            height_cm = float(height_cm_in)
            weight_kg = float(weight_kg_in)
            bodyfat_pct = float(bodyfat_pct_in)

            result = ffmi_info(height_cm, weight_kg, bodyfat_pct, sex_in)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "FFMI 计算器（去脂体重指数）- CalmyHealth",
        "description": "输入身高、体重、体脂率和性别，计算 FFMI（去脂体重指数）、标准化 FFMI 和去脂体重，帮助更全面理解体型与肌肉量水平。",
        "canonical": canonical_url("/ffmi"),
    }

    return render_template(
        "ffmi.html",
        meta=meta,
        error=error,
        sex_in=sex_in,
        height_cm_in=height_cm_in,
        weight_kg_in=weight_kg_in,
        bodyfat_pct_in=bodyfat_pct_in,
        result=result,
        page_kind="tool",
    )
# 1.2.5 体脂目标时间
@app.route("/body-fat-goal", methods=["GET", "POST"])
def body_fat_goal():
    error = None
    weight_kg_in = ""
    bodyfat_pct_in = ""
    target_bodyfat_pct_in = ""
    daily_deficit_kcal_in = "400"
    result = None

    if request.method == "POST":
        weight_kg_in = request.form.get("weight_kg", "").strip()
        bodyfat_pct_in = request.form.get("bodyfat_pct", "").strip()
        target_bodyfat_pct_in = request.form.get("target_bodyfat_pct", "").strip()
        daily_deficit_kcal_in = request.form.get("daily_deficit_kcal", "400").strip()

        try:
            weight_kg = float(weight_kg_in)
            bodyfat_pct = float(bodyfat_pct_in)
            target_bodyfat_pct = float(target_bodyfat_pct_in)
            daily_deficit_kcal = float(daily_deficit_kcal_in)

            result = body_fat_goal_info(
                weight_kg,
                bodyfat_pct,
                target_bodyfat_pct,
                daily_deficit_kcal,
            )

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "体脂目标时间计算器（多久能降到目标体脂）- CalmyHealth",
        "description": "输入当前体重、当前体脂率、目标体脂率和每日热量缺口，估算达到目标体脂率大概需要多久，并查看减脂节奏参考。",
        "canonical": canonical_url("/body-fat-goal"),
    }

    return render_template(
        "body_fat_goal.html",
        meta=meta,
        error=error,
        weight_kg_in=weight_kg_in,
        bodyfat_pct_in=bodyfat_pct_in,
        target_bodyfat_pct_in=target_bodyfat_pct_in,
        daily_deficit_kcal_in=daily_deficit_kcal_in,
        result=result,
        page_kind="tool",
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
            if goal_in not in ("fat_loss", "maintain", "muscle_gain", "dri"):
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
# ========= 3.3 饮食分配 ======= 
# 3.3.1. 餐次分配
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
        "description": "根据总热量需求，合理分配三餐摄入，帮助控制体重和饮食结构。",
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
# ========= 3.4 饮食质量 ======= 
## 3.4.1. GL估算 
@app.route("/glycemic-load", methods=["GET", "POST"])
def glycemic_load():
    error = None
    result = None

    gi_in = ""
    carbs_in = ""
    fiber_in = "0"

    if request.method == "POST":
        gi_in = request.form.get("gi", "").strip()
        carbs_in = request.form.get("carbs_g", "").strip()
        fiber_in = request.form.get("fiber_g", "0").strip()

        try:
            gi_val = float(gi_in)
            carbs_val = float(carbs_in)
            fiber_val = float(fiber_in)

            result = glycemic_load_info(gi_val, carbs_val, fiber_val)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "GI/GL 估算器（血糖负荷计算器）- CalmyHealth",
        "description": "输入 GI、总碳水和膳食纤维，估算食物的血糖负荷 GL，并了解低 GI、低 GL 与饮食结构之间的区别。",
        "canonical": canonical_url("/glycemic-load"),
    }

    return render_template(
        "glycemic_load.html",
        meta=meta,
        error=error,
        result=result,
        gi_in=gi_in,
        carbs_in=carbs_in,
        fiber_in=fiber_in,
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
# 3.1.7 糖摄入
@app.route("/sugar-intake", methods=["GET", "POST"])
def sugar_intake():
    error = None
    result = None

    sugary_drinks_in = "1"
    desserts_in = "0"
    sweet_snacks_in = "1"
    sweet_sauces_in = "0"
    sweet_coffee_tea_in = "1"

    if request.method == "POST":
        sugary_drinks_in = request.form.get("sugary_drinks", "1").strip()
        desserts_in = request.form.get("desserts", "0").strip()
        sweet_snacks_in = request.form.get("sweet_snacks", "1").strip()
        sweet_sauces_in = request.form.get("sweet_sauces", "0").strip()
        sweet_coffee_tea_in = request.form.get("sweet_coffee_tea", "1").strip()

        try:
            result = sugar_intake_estimate(
                int(sugary_drinks_in),
                int(desserts_in),
                int(sweet_snacks_in),
                int(sweet_sauces_in),
                int(sweet_coffee_tea_in),
            )
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "糖摄入估算器（你每天吃糖会不会太多）- CalmyHealth",
        "description": "根据含糖饮料、甜点、甜味零食、调味酱和加糖咖啡茶的份数，粗略估算每天添加糖摄入量与对应热量，并给出控糖建议。",
        "canonical": canonical_url("/sugar-intake"),
    }

    return render_template(
        "sugar_intake.html",
        meta=meta,
        error=error,
        result=result,
        sugary_drinks_in=sugary_drinks_in,
        desserts_in=desserts_in,
        sweet_snacks_in=sweet_snacks_in,
        sweet_sauces_in=sweet_sauces_in,
        sweet_coffee_tea_in=sweet_coffee_tea_in,
        page_kind="tool",
    )
# 3.1.8 咖啡因摄入
@app.route("/caffeine-intake", methods=["GET", "POST"])
def caffeine_intake():
    error = None
    result = None

    brewed_coffee_in = "1"
    espresso_shots_in = "0"
    tea_cups_in = "1"
    energy_drinks_in = "0"
    cola_cans_in = "0"

    if request.method == "POST":
        brewed_coffee_in = request.form.get("brewed_coffee", "1").strip()
        espresso_shots_in = request.form.get("espresso_shots", "0").strip()
        tea_cups_in = request.form.get("tea_cups", "1").strip()
        energy_drinks_in = request.form.get("energy_drinks", "0").strip()
        cola_cans_in = request.form.get("cola_cans", "0").strip()

        try:
            result = caffeine_intake_estimate(
                int(brewed_coffee_in),
                int(espresso_shots_in),
                int(tea_cups_in),
                int(energy_drinks_in),
                int(cola_cans_in),
            )
        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    meta = {
        "title": "咖啡因摄入计算器（一天喝多少咖啡因）- CalmyHealth",
        "description": "根据咖啡、浓缩咖啡、茶、能量饮料和可乐的份数，粗略估算每天咖啡因摄入量，并判断整体是否偏高。",
        "canonical": canonical_url("/caffeine-intake"),
    }

    return render_template(
        "caffeine_intake.html",
        meta=meta,
        error=error,
        result=result,
        brewed_coffee_in=brewed_coffee_in,
        espresso_shots_in=espresso_shots_in,
        tea_cups_in=tea_cups_in,
        energy_drinks_in=energy_drinks_in,
        cola_cans_in=cola_cans_in,
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

    table_weights = [50, 60, 70, 80]
    kcal_table = [
        (n, [round0(steps_to_kcal(n, kg)) for kg in table_weights])
        for n in (3000, 5000, 8000, 10000, 12000)
    ]

    meta = meta_for(
        "步数转热量计算器｜10000步消耗多少卡路里 - CalmyHealth",
        "10000步大约消耗 290–470 卡路里（体重 50–80 kg、正常步速），例如 60 kg 约 350 kcal。输入步数和体重，用 MET 法估算步行热量消耗，适合日常活动与减脂参考。",
        "/steps",
    )
    return render_template(
        "steps.html",
        meta=meta,
        error=error,
        steps_in=steps_in,
        weight_kg_in=weight_kg_in,
        kcal=kcal,
        table_weights=table_weights,
        kcal_table=kcal_table,
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
        "title": "步数转距离计算器｜10000步等于多少公里 - CalmyHealth",
        "description": "10000步一般约为6–8公里。输入步数、身高和性别，即可根据步幅估算步行距离。简化模型：男性步幅≈身高×0.415，女性步幅≈身高×0.413。",
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
        "title": "步数转时间计算器｜10000步要走多久 - CalmyHealth",
        "description": "10000步要走多久？一般约100分钟。输入步数并选择步行速度，快速估算步行时间，适合日常活动与减脂规划。",
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

    # /step-goal
    meta = {
        "title": "每日步数目标计算器（你应该走多少步）- CalmyHealth",
        "description": "每天走多少步合适？输入当前日均步数和目标，估算建议每日步数，适合提升活动量、减脂和习惯管理参考。",
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

    # /activity-level
    meta = {
        "title": "活动水平计算器（久坐还是活跃）- CalmyHealth",
        "description": "根据日常行为判断你的活动水平分类，用于计算热量消耗和健康评估。",
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
# 4.1.6 跑步热量消耗计算器
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

    # /running-kcal
    meta = {
        "title": "跑步热量消耗计算器｜跑步消耗多少卡路里 - CalmyHealth",
        "description": "跑步消耗多少卡路里？输入体重、跑步时间和速度，估算跑步热量消耗，适合运动和减脂参考。",
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
# 4.1.7 跑步配速
@app.route("/running-pace", methods=["GET", "POST"])
def running_pace():
    error = None
    result = None

    distance_km_in = "5"
    hours_in = "0"
    minutes_in = "30"
    seconds_in = "00"

    if request.method == "POST":
        distance_km_in = request.form.get("distance_km", "5").strip()
        hours_in = request.form.get("hours", "0").strip()
        minutes_in = request.form.get("minutes", "30").strip()
        seconds_in = request.form.get("seconds", "00").strip()

        try:
            distance_km = float(distance_km_in)
            hours = int(hours_in)
            minutes = int(minutes_in)
            seconds = int(seconds_in)

            result = running_pace_info(distance_km, hours, minutes, seconds)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    # /running-pace
    meta = {
        "title": "跑步配速计算器｜每公里配速与完赛时间 - CalmyHealth",
        "description": "输入跑步距离和完成时间，计算每公里配速、平均速度，并估算5K、10K、半马和全马完赛时间。",
        "canonical": canonical_url("/running-pace"),
    }

    return render_template(
        "running_pace.html",
        meta=meta,
        error=error,
        result=result,
        distance_km_in=distance_km_in,
        hours_in=hours_in,
        minutes_in=minutes_in,
        seconds_in=seconds_in,
        page_kind="tool",
    )
# 4.1.8 心率区间
@app.route("/heart-rate-zone", methods=["GET", "POST"])
def heart_rate_zone():
    error = None
    result = None

    age_in = ""
    resting_hr_in = ""

    if request.method == "POST":
        age_in = request.form.get("age", "").strip()
        resting_hr_in = request.form.get("resting_hr", "").strip()

        try:
            age = int(age_in)
            resting_hr = int(resting_hr_in) if resting_hr_in else None

            result = heart_rate_zone_info(age, resting_hr)

        except Exception as e:
            error = str(e) if str(e) else "请输入有效数据。"

    # /heart-rate-zone
    meta = {
        "title": "心率区间计算器｜运动燃脂与有氧心率 - CalmyHealth",
        "description": "输入年龄和静息心率，估算运动心率区间，帮助理解恢复、燃脂、有氧、阈值和高强度训练范围。",
        "canonical": canonical_url("/heart-rate-zone"),
    }
    return render_template(
        "heart_rate_zone.html",
        meta=meta,
        error=error,
        result=result,
        age_in=age_in,
        resting_hr_in=resting_hr_in,
        page_kind="tool",
    )

@app.get("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    print("Starting Flask...")
    app.run(host="0.0.0.0", port=5000, debug=True)